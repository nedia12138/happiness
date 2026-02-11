#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较数据字段和数据库表字段，找出不匹配的地方
"""

import pandas as pd
import pymysql
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from config.config import DB_CONFIG

def compare_fields():
    """比较数据字段和数据库表字段"""

    print("=" * 60)
    print("字段对比分析")
    print("=" * 60)

    # 读取完整版数据列名
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    train_file = os.path.join(data_dir, 'happiness_train_complete.csv')

    encodings_to_try = ['utf-8', 'gbk', 'gb2312']
    df = None

    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(train_file, nrows=1, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取数据")
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        print("无法读取数据文件")
        return

    data_columns = set(df.columns)
    print(f"\n数据文件字段数: {len(data_columns)}")

    # 获取数据库表字段
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 查询完整版表的字段
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'py_happiness_survey_complete'
            ORDER BY COLUMN_NAME
        """)

        db_columns_result = cursor.fetchall()
        db_columns = set(row[0] for row in db_columns_result)

        print(f"数据库表字段数: {len(db_columns)}")

        # 找出数据中有但数据库表中没有的字段
        missing_in_db = data_columns - db_columns
        print(f"\n数据中有但数据库表中没有的字段 ({len(missing_in_db)} 个):")
        for col in sorted(missing_in_db):
            print(f"  - {col}")

        # 找出数据库表中有但数据中没有的字段
        missing_in_data = db_columns - data_columns
        print(f"\n数据库表中有但数据中没有的字段 ({len(missing_in_data)} 个):")
        for col in sorted(missing_in_data):
            print(f"  - {col}")

        # 显示匹配的字段
        matched = data_columns & db_columns
        print(f"\n匹配的字段 ({len(matched)} 个):")
        for col in sorted(list(matched)[:20]):  # 只显示前20个
            print(f"  - {col}")
        if len(matched) > 20:
            print(f"  ... 还有 {len(matched) - 20} 个字段")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"数据库查询失败: {e}")

if __name__ == '__main__':
    compare_fields()
