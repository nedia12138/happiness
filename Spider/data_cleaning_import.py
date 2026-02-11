#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
幸福感数据集清洗和导入脚本
功能：读取CSV文件，进行数据清洗，导入MySQL数据库
"""

import pandas as pd
import numpy as np
import pymysql
import logging
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from config.config import DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HappinessDataImporter:
    """幸福感数据导入器"""

    def __init__(self):
        self.db_config = DB_CONFIG
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.batch_size = 1000  # 批量插入大小

        # 字段名映射：CSV字段名 -> 数据库字段名
        self.field_mapping_abbr = {
            'survey_type': 'surveyType',
            'survey_time': 'surveyTime',
            'religion_freq': 'religionFreq',
            'floor_area': 'floorArea',
            'height_cm': 'heightCm',
            'weight_jin': 'weightJin',
            'health_problem': 'healthProblem',
            'work_exper': 'workExper',
            'work_status': 'workStatus',
            'work_yr': 'workYr',
            'work_type': 'workType',
            'work_manage': 'workManage',
            'family_income': 'familyIncome',
            'family_m': 'familyM',
            'family_status': 'familyStatus',
            'status_peer': 'statusPeer',
            'status_3_before': 'status3Before',
            'inc_ability': 'incAbility',
            'data_source': 'dataSource'
        }

        # 完整版字段名映射（更多字段）
        self.field_mapping_complete = {
            'survey_type': 'surveyType',
            'survey_time': 'surveyTime',
            'religion_freq': 'religionFreq',  # 缺失的映射
            'socia_outing': 'socialOuting',   # 拼写错误修复
            'marital_now': 'maritalNow',      # 缺失的映射
            'edu_other': 'eduOther',
            'edu_status': 'eduStatus',
            'edu_yr': 'eduYr',
            'join_party': 'joinParty',
            'floor_area': 'floorArea',
            'property_0': 'property0',
            'property_1': 'property1',
            'property_2': 'property2',
            'property_3': 'property3',
            'property_4': 'property4',
            'property_5': 'property5',
            'property_6': 'property6',
            'property_7': 'property7',
            'property_8': 'property8',
            'property_other': 'propertyOther',
            'height_cm': 'heightCm',
            'weight_jin': 'weightJin',
            'health_problem': 'healthProblem',
            'hukou_loc': 'hukouLoc',
            'media_1': 'media1',
            'media_2': 'media2',
            'media_3': 'media3',
            'media_4': 'media4',
            'media_5': 'media5',
            'media_6': 'media6',
            'leisure_1': 'leisure1',
            'leisure_2': 'leisure2',
            'leisure_3': 'leisure3',
            'leisure_4': 'leisure4',
            'leisure_5': 'leisure5',
            'leisure_6': 'leisure6',
            'leisure_7': 'leisure7',
            'leisure_8': 'leisure8',
            'leisure_9': 'leisure9',
            'leisure_10': 'leisure10',
            'leisure_11': 'leisure11',
            'leisure_12': 'leisure12',
            'social_neighbor': 'socialNeighbor',
            'social_friend': 'socialFriend',
            'social_outing': 'socialOuting',
            'class_10_before': 'class10Before',
            'class_10_after': 'class10After',
            'class_14': 'class14',
            'work_exper': 'workExper',
            'work_status': 'workStatus',
            'work_yr': 'workYr',
            'work_type': 'workType',
            'work_manage': 'workManage',
            'insur_1': 'insur1',
            'insur_2': 'insur2',
            'insur_3': 'insur3',
            'insur_4': 'insur4',
            'family_m': 'familyM',
            'family_status': 'familyStatus',
            'invest_0': 'invest0',
            'invest_1': 'invest1',
            'invest_2': 'invest2',
            'invest_3': 'invest3',
            'invest_4': 'invest4',
            'invest_5': 'invest5',
            'invest_6': 'invest6',
            'invest_7': 'invest7',
            'invest_8': 'invest8',
            'invest_other': 'investOther',
            'son': 'son',
            'daughter': 'daughter',
            'minor_child': 'minorChild',
            'marital_1st': 'marital1st',
            's_birth': 'sBirth',
            's_edu': 'sEdu',
            's_political': 'sPolitical',
            's_hukou': 'sHukou',
            's_income': 'sIncome',
            's_work_exper': 'sWorkExper',
            's_work_status': 'sWorkStatus',
            's_work_type': 'sWorkType',
            'f_birth': 'fBirth',
            'f_edu': 'fEdu',
            'f_political': 'fPolitical',
            'f_work_14': 'fWork14',
            'm_birth': 'mBirth',
            'm_edu': 'mEdu',
            'm_political': 'mPolitical',
            'm_work_14': 'mWork14',
            'status_peer': 'statusPeer',
            'status_3_before': 'status3Before',
            'inc_ability': 'incAbility',
            'inc_exp': 'incExp',
            'trust_1': 'trust1',
            'trust_2': 'trust2',
            'trust_3': 'trust3',
            'trust_4': 'trust4',
            'trust_5': 'trust5',
            'trust_6': 'trust6',
            'trust_7': 'trust7',
            'trust_8': 'trust8',
            'trust_9': 'trust9',
            'trust_10': 'trust10',
            'trust_11': 'trust11',
            'trust_12': 'trust12',
            'trust_13': 'trust13',
            'neighbor_familiarity': 'neighborFamiliarity',
            'public_service_1': 'publicService1',
            'public_service_2': 'publicService2',
            'public_service_3': 'publicService3',
            'public_service_4': 'publicService4',
            'public_service_5': 'publicService5',
            'public_service_6': 'publicService6',
            'public_service_7': 'publicService7',
            'public_service_8': 'publicService8',
            'public_service_9': 'publicService9',
            'data_source': 'dataSource'
        }

    def get_db_connection(self):
        """获取数据库连接"""
        try:
            connection = pymysql.connect(**self.db_config)
            return connection
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise e

    def clean_numeric_value(self, value, default=None):
        """清洗数值型字段"""
        if pd.isna(value) or value == '' or str(value).lower() in ['nan', 'null', 'none']:
            return default

        # 处理负值表示的缺失数据
        if isinstance(value, (int, float)) and value < 0:
            return default

        try:
            # 转换为数值类型
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return default
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            return default

    def clean_string_value(self, value, max_length=None):
        """清洗字符串字段"""
        if pd.isna(value) or str(value).lower() in ['nan', 'null', 'none']:
            return None

        value = str(value).strip()
        if value == '':
            return None

        # 处理负值表示的缺失数据
        try:
            if float(value) < 0:
                return None
        except (ValueError, TypeError):
            pass

        if max_length and len(value) > max_length:
            return value[:max_length]

        return value

    def preprocess_abbreviated_data(self, df, data_source='train'):
        """预处理简化版数据"""
        logger.info(f"开始预处理{data_source}数据集，原始数据量: {len(df)}")

        # 复制数据避免修改原数据
        df_clean = df.copy()

        # 数据清洗和类型转换
        df_clean['id'] = df_clean['id'].astype(int)

        # 清洗数值字段
        numeric_fields = [
            'happiness', 'survey_type', 'province', 'city', 'county', 'gender', 'birth',
            'nationality', 'religion', 'religion_freq', 'edu', 'political', 'floor_area',
            'height_cm', 'weight_jin', 'health', 'health_problem', 'depression', 'hukou',
            'socialize', 'relax', 'learn', 'equity', 'class', 'work_exper', 'work_status',
            'work_yr', 'work_type', 'work_manage', 'family_m', 'family_status', 'house',
            'car', 'marital', 'status_peer', 'status_3_before', 'view', 'inc_ability'
        ]

        for field in numeric_fields:
            if field in df_clean.columns:
                df_clean[field] = df_clean[field].apply(lambda x: self.clean_numeric_value(x))

        # 清洗特殊字段
        df_clean['income'] = df_clean['income'].apply(lambda x: self.clean_numeric_value(x))
        df_clean['family_income'] = df_clean['family_income'].apply(lambda x: self.clean_numeric_value(x))

        # 清洗字符串字段
        df_clean['survey_time'] = df_clean['survey_time'].apply(lambda x: self.clean_string_value(x, 50))

        # 添加数据来源标识
        df_clean['data_source'] = data_source

        # 字段名映射：将CSV下划线命名转换为数据库驼峰命名
        df_clean = df_clean.rename(columns=self.field_mapping_abbr)

        # 移除完全为空的行
        df_clean = df_clean.dropna(how='all')

        logger.info(f"{data_source}数据集预处理完成，清洗后数据量: {len(df_clean)}")
        return df_clean

    def preprocess_complete_data(self, df, data_source='train'):
        """预处理完整版数据"""
        logger.info(f"开始预处理完整版{data_source}数据集，原始数据量: {len(df)}")

        # 复制数据避免修改原数据
        df_clean = df.copy()

        # 数据清洗和类型转换
        df_clean['id'] = df_clean['id'].astype(int)

        # 清洗数值字段
        numeric_fields = [
            'happiness', 'survey_type', 'province', 'city', 'county', 'gender', 'birth',
            'nationality', 'religion', 'religion_freq', 'edu', 'edu_status', 'edu_yr',
            'political', 'floor_area', 'property_0', 'property_1', 'property_2', 'property_3',
            'property_4', 'property_5', 'property_6', 'property_7', 'property_8', 'height_cm',
            'weight_jin', 'health', 'health_problem', 'depression', 'hukou', 'media_1',
            'media_2', 'media_3', 'media_4', 'media_5', 'media_6', 'leisure_1', 'leisure_2',
            'leisure_3', 'leisure_4', 'leisure_5', 'leisure_6', 'leisure_7', 'leisure_8',
            'leisure_9', 'leisure_10', 'leisure_11', 'leisure_12', 'socialize', 'relax',
            'learn', 'social_neighbor', 'social_friend', 'social_outing', 'equity', 'class',
            'class_10_before', 'class_10_after', 'class_14', 'work_exper', 'work_status',
            'work_yr', 'work_type', 'work_manage', 'insur_1', 'insur_2', 'insur_3', 'insur_4',
            'family_m', 'family_status', 'house', 'car', 'invest_0', 'invest_1', 'invest_2',
            'invest_3', 'invest_4', 'invest_5', 'invest_6', 'invest_7', 'invest_8', 'son',
            'daughter', 'minor_child', 'marital', 's_birth', 's_edu', 's_political', 's_hukou',
            's_work_exper', 's_work_status', 'f_birth', 'f_edu', 'f_political', 'm_birth',
            'm_edu', 'm_political', 'status_peer', 'status_3_before', 'view', 'inc_ability',
            'inc_exp', 'trust_1', 'trust_2', 'trust_3', 'trust_4', 'trust_5', 'trust_6', 'trust_7',
            'trust_8', 'trust_9', 'trust_10', 'trust_11', 'trust_12', 'trust_13',
            'neighbor_familiarity', 'public_service_1', 'public_service_2', 'public_service_3',
            'public_service_4', 'public_service_5', 'public_service_6', 'public_service_7',
            'public_service_8', 'public_service_9'
        ]

        for field in numeric_fields:
            if field in df_clean.columns:
                df_clean[field] = df_clean[field].apply(lambda x: self.clean_numeric_value(x))

        # 清洗特殊数值字段
        df_clean['income'] = df_clean['income'].apply(lambda x: self.clean_numeric_value(x))
        df_clean['family_income'] = df_clean['family_income'].apply(lambda x: self.clean_numeric_value(x))
        df_clean['s_income'] = df_clean['s_income'].apply(lambda x: self.clean_numeric_value(x))

        # 确保所有需要的字段都在映射中
        additional_mappings = {
            'income': 'income',  # 这个字段不需要映射，保持原名
            'family_income': 'familyIncome',
            's_income': 'sIncome'
        }
        for key, value in additional_mappings.items():
            if key not in self.field_mapping_complete:
                self.field_mapping_complete[key] = value

        # 清洗字符串字段
        string_fields = [
            'edu_other', 'join_party', 'property_other', 'hukou_loc', 'invest_other',
            'marital_1st', 'marital_now', 's_work_type', 'f_work_14', 'm_work_14'
        ]

        for field in string_fields:
            if field in df_clean.columns:
                df_clean[field] = df_clean[field].apply(lambda x: self.clean_string_value(x))

        df_clean['survey_time'] = df_clean['survey_time'].apply(lambda x: self.clean_string_value(x, 50))

        # 添加数据来源标识
        df_clean['data_source'] = data_source

        # 字段名映射：将CSV下划线命名转换为数据库驼峰命名
        df_clean = df_clean.rename(columns=self.field_mapping_complete)

        # 移除完全为空的行
        df_clean = df_clean.dropna(how='all')

        logger.info(f"完整版{data_source}数据集预处理完成，清洗后数据量: {len(df_clean)}")
        return df_clean

    def batch_insert_data(self, df, table_name, connection):
        """批量插入数据"""
        if df.empty:
            logger.warning(f"数据框为空，跳过插入{table_name}")
            return

        cursor = connection.cursor()

        # 获取列名
        columns = df.columns.tolist()
        columns_str = ', '.join([f'`{col}`' for col in columns])

        # 构建占位符
        placeholders = ', '.join(['%s'] * len(columns))

        # 构建插入语句
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # 批量处理数据，将NaN替换为None
        data_tuples = []
        for _, row in df[columns].iterrows():
            row_tuple = tuple(None if (pd.isna(x) or (isinstance(x, float) and np.isnan(x))) else x for x in row)
            data_tuples.append(row_tuple)

        try:
            # 分批插入
            for i in range(0, len(data_tuples), self.batch_size):
                batch_data = data_tuples[i:i + self.batch_size]
                cursor.executemany(sql, batch_data)
                connection.commit()
                logger.info(f"已插入{table_name}表第{i//self.batch_size + 1}批数据，共{len(batch_data)}条记录")

            logger.info(f"成功插入{table_name}表总计{len(data_tuples)}条记录")

        except Exception as e:
            connection.rollback()
            logger.error(f"插入{table_name}表失败: {e}")
            raise e
        finally:
            cursor.close()

    def import_abbreviated_data(self):
        """导入简化版数据"""
        logger.info("开始导入简化版数据...")

        try:
            # 先清空表数据
            connection = self.get_db_connection()
            cursor = connection.cursor()
            cursor.execute("TRUNCATE TABLE py_happiness_survey")
            connection.commit()
            cursor.close()
            connection.close()
            logger.info("已清空 py_happiness_survey 表")
            # 读取训练数据
            train_file = os.path.join(self.data_dir, 'happiness_train_abbr.csv')
            test_file = os.path.join(self.data_dir, 'happiness_test_abbr.csv')

            if os.path.exists(train_file):
                train_df = pd.read_csv(train_file, low_memory=False)
                train_clean = self.preprocess_abbreviated_data(train_df, 'train')
            else:
                logger.warning(f"训练数据文件不存在: {train_file}")
                train_clean = pd.DataFrame()

            if os.path.exists(test_file):
                test_df = pd.read_csv(test_file, low_memory=False)
                test_clean = self.preprocess_abbreviated_data(test_df, 'test')
            else:
                logger.warning(f"测试数据文件不存在: {test_file}")
                test_clean = pd.DataFrame()

            # 合并训练和测试数据
            if not train_clean.empty and not test_clean.empty:
                all_data = pd.concat([train_clean, test_clean], ignore_index=True)
            elif not train_clean.empty:
                all_data = train_clean
            elif not test_clean.empty:
                all_data = test_clean
            else:
                logger.error("没有找到有效的简化版数据文件")
                return

            # 连接数据库并插入数据
            with self.get_db_connection() as connection:
                self.batch_insert_data(all_data, 'py_happiness_survey', connection)

            logger.info("简化版数据导入完成")

        except Exception as e:
            logger.error(f"导入简化版数据失败: {e}")
            raise e

    def import_complete_data(self):
        """导入完整版数据"""
        logger.info("开始导入完整版数据...")

        try:
            # 先清空表数据
            connection = self.get_db_connection()
            cursor = connection.cursor()
            cursor.execute("TRUNCATE TABLE py_happiness_survey_complete")
            connection.commit()
            cursor.close()
            connection.close()
            logger.info("已清空 py_happiness_survey_complete 表")

            # 读取完整版数据
            train_file = os.path.join(self.data_dir, 'happiness_train_complete.csv')
            test_file = os.path.join(self.data_dir, 'happiness_test_complete.csv')

            # 尝试多种编码方式读取完整版数据
            if os.path.exists(train_file):
                encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'cp1252', 'latin1']
                train_df = None

                for encoding in encodings_to_try:
                    try:
                        logger.info(f"尝试使用 {encoding} 编码读取完整版数据...")
                        train_df = pd.read_csv(train_file, low_memory=False, encoding=encoding)
                        logger.info(f"成功使用 {encoding} 编码读取数据")
                        break
                    except UnicodeDecodeError:
                        logger.warning(f"{encoding} 编码读取失败，继续尝试其他编码...")
                        continue
                    except Exception as e:
                        logger.warning(f"使用 {encoding} 编码读取时出现其他错误: {e}")
                        continue

                if train_df is None:
                    logger.error("所有编码方式都无法读取完整版数据文件")
                    return

                try:
                    train_clean = self.preprocess_complete_data(train_df, 'train')
                except Exception as e:
                    logger.error(f"完整版数据预处理失败: {e}")
                    return
            else:
                logger.warning(f"完整版训练数据文件不存在: {train_file}")
                return

            # 连接数据库并插入数据
            with self.get_db_connection() as connection:
                self.batch_insert_data(train_clean, 'py_happiness_survey_complete', connection)

            logger.info("完整版数据导入完成")

        except Exception as e:
            logger.error(f"导入完整版数据失败: {e}")
            raise e

    def create_indexes_and_constraints(self):
        """创建额外的索引和约束"""
        logger.info("开始创建额外的索引和约束...")

        # 首先检查哪些索引不存在，然后只创建不存在的索引
        check_index_sqls = [
            ("idx_happiness_gender", "py_happiness_survey"),
            ("idx_province_city", "py_happiness_survey"),
            ("idx_edu_income", "py_happiness_survey"),
            ("idx_marital_status", "py_happiness_survey"),
            ("idx_complete_happiness_gender", "py_happiness_survey_complete"),
            ("idx_complete_province_city", "py_happiness_survey_complete"),
            ("idx_complete_edu_income", "py_happiness_survey_complete"),
            ("idx_complete_marital", "py_happiness_survey_complete"),
        ]

        create_index_sqls = [
            "CREATE INDEX idx_happiness_gender ON py_happiness_survey(happiness, gender);",
            "CREATE INDEX idx_province_city ON py_happiness_survey(province, city);",
            "CREATE INDEX idx_edu_income ON py_happiness_survey(edu, income);",
            "CREATE INDEX idx_marital_status ON py_happiness_survey(marital);",
            "CREATE INDEX idx_complete_happiness_gender ON py_happiness_survey_complete(happiness, gender);",
            "CREATE INDEX idx_complete_province_city ON py_happiness_survey_complete(province, city);",
            "CREATE INDEX idx_complete_edu_income ON py_happiness_survey_complete(edu, income);",
            "CREATE INDEX idx_complete_marital ON py_happiness_survey_complete(marital);",
        ]

        with self.get_db_connection() as connection:
            cursor = connection.cursor()

            # 检查并创建索引
            for (index_name, table_name), create_sql in zip(check_index_sqls, create_index_sqls):
                try:
                    # 首先尝试直接创建索引，如果已存在会报错
                    cursor.execute(create_sql)
                    connection.commit()
                    logger.info(f"成功创建索引: {index_name}")
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'duplicate key name' in error_msg or 'already exists' in error_msg:
                        logger.info(f"索引 {index_name} 已存在，跳过")
                    else:
                        logger.warning(f"创建索引失败 {index_name}: {e}")
                        # 尝试使用ALTER TABLE方式创建
                        try:
                            alt_create_sql = create_sql.replace('CREATE INDEX', f'ALTER TABLE {table_name} ADD INDEX')
                            cursor.execute(alt_create_sql)
                            connection.commit()
                            logger.info(f"使用ALTER TABLE成功创建索引: {index_name}")
                        except Exception as e2:
                            logger.warning(f"ALTER TABLE创建索引也失败 {index_name}: {e2}")

            cursor.close()

    def run_import(self):
        """运行完整的数据导入流程"""
        start_time = datetime.now()
        logger.info("开始幸福感数据集导入流程...")

        try:
            # 导入简化版数据
            self.import_abbreviated_data()

            # 尝试导入完整版数据
            try:
                self.import_complete_data()
            except Exception as e:
                logger.warning(f"完整版数据导入失败，跳过: {e}")

            # 创建额外的索引
            self.create_indexes_and_constraints()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"数据导入流程完成，总耗时: {duration:.2f}秒")

        except Exception as e:
            logger.error(f"数据导入流程失败: {e}")
            raise e


def main():
    """主函数"""
    importer = HappinessDataImporter()
    importer.run_import()


if __name__ == '__main__':
    main()
