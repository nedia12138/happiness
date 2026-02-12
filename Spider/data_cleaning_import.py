#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import pymysql
import logging
import os
import sys
from datetime import datetime

# 环境初始化
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
from config.config import DB_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('data_import.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class HappinessDataImporter:
    def __init__(self):
        self.db_config = DB_CONFIG
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.batch_size = 1000

    def get_conn(self):
        return pymysql.connect(**self.db_config)

    def get_db_cols(self, table_name):
        """精准获取数据库列名"""
        conn = self.get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
                return [desc[0] for desc in cursor.description]
        finally:
            conn.close()

    def clean_and_map(self, df, table_name, source_label):
        """核心修复：强制打标 + NaN清洗"""
        df = df.copy()
        db_cols = self.get_db_cols(table_name)

        # 1. 转换字段名
        new_cols = {c: (c.split('_')[0] + ''.join(x.title() for x in c.split('_')[1:]))
        if '_' in c else c for c in df.columns}
        df = df.rename(columns=new_cols)

        # 2. 【强制修复】确保 dataSource 每一行都是正确的标签
        df['dataSource'] = source_label

        # 3. 过滤并处理空值
        final_cols = [c for c in df.columns if c in db_cols]
        df = df[final_cols]
        df = df.where(pd.notnull(df), None)
        return df

    def safe_insert(self, df, table_name):
        """带统计面板的稳健插入"""
        if df.empty: return

        # --- 核心诊断面板 ---
        counts = df['dataSource'].value_counts()
        logger.info("=" * 50)
        logger.info(f"📊 准备写入数据库表: {table_name}")
        for src, cnt in counts.items():
            logger.info(f"   >>> 发现数据源 [{src}]: {cnt} 条")

        if 'test' not in counts.index:
            logger.error("❌ 严重警告：待插入数据中完全没有 'test' 标签的数据！")
        logger.info("=" * 50)

        conn = self.get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SET FOREIGN_KEY_CHECKS = 0")
                cursor.execute(f"TRUNCATE TABLE {table_name}")

                cols = df.columns.tolist()
                sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})"

                # 最后的 NaN 检查
                data = [[(None if (isinstance(v, float) and np.isnan(v)) else v) for v in row] for row in
                        df.values.tolist()]

                for i in range(0, len(data), self.batch_size):
                    cursor.executemany(sql, data[i:i + self.batch_size])
                conn.commit()
                logger.info(f"✅ {table_name} 入库成功")
        finally:
            conn.close()

    def process_import(self, is_complete=False):
        """统一导入逻辑"""
        table = "py_happiness_survey_complete" if is_complete else "py_happiness_survey"
        file_suffix = "_complete.csv" if is_complete else "_abbr.csv"

        all_dfs = []
        for tag in ['train', 'test']:
            fname = f"happiness_{tag}{file_suffix}"
            fpath = os.path.join(self.data_dir, fname)
            if os.path.exists(fpath):
                for enc in ['gbk', 'utf-8', 'gb18030']:
                    try:
                        df = pd.read_csv(fpath, low_memory=False, encoding=enc)
                        # 重点：再次强制给 DF 打上当前的 tag 标签
                        df['dataSource'] = tag
                        cleaned = self.clean_and_map(df, table, tag)
                        all_dfs.append(cleaned)
                        logger.info(f"读取成功: {fname}")
                        break
                    except:
                        continue
            else:
                logger.warning(f"缺失文件: {fname}")

        if all_dfs:
            self.safe_insert(pd.concat(all_dfs, ignore_index=True), table)

    def run_import(self):
        try:
            self.process_import(is_complete=False)
            self.process_import(is_complete=True)
            logger.info("🎉 数据导入流程全部圆满完成！")
        except Exception as e:
            logger.error(f"失败: {e}")


if __name__ == '__main__':
    HappinessDataImporter().run_import()