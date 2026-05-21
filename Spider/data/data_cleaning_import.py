
# -*- coding: utf-8 -*-
import logging
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import pymysql

project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
from config.config import DB_CONFIG


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("../data_import.log", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


TABLE_SPECS = {

    "py_happiness_survey_complete": [
        ("happiness_train_complete.csv", "train"),
        ("happiness_test_complete.csv", "test"),
    ],
}

INDEX_SPECS = [
    ("idx_{table}_data_source", ["dataSource"]),
    ("idx_{table}_happiness", ["happiness"]),
    ("idx_{table}_province_city", ["province", "city"]),
    ("idx_{table}_edu_income", ["edu", "income"]),
    ("idx_{table}_marital", ["marital"]),
    ("idx_{table}_gender", ["gender"]),
]


def snake_to_camel(name):
    if "_" not in name:
        return name
    head, *tail = name.split("_")
    return head + "".join(part.title() for part in tail)


class HappinessDataImporter:
    def __init__(self):
        self.db_config = DB_CONFIG.copy()
        self.server_config = self.db_config.copy()
        self.database_name = self.server_config.pop("database")
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.batch_size = 1000

    def get_server_conn(self):
        return pymysql.connect(**self.server_config)

    def get_db_conn(self):
        return pymysql.connect(**self.db_config)

    def read_csv(self, path):
        encodings = ("utf-8", "gbk", "gb18030")
        last_error = None
        for encoding in encodings:
            try:
                return pd.read_csv(path, encoding=encoding, low_memory=False)
            except Exception as exc:
                last_error = exc
        raise last_error

    def load_table_dataframe(self, table_name):
        frames = []
        for filename, source_label in TABLE_SPECS[table_name]:
            file_path = os.path.join(self.data_dir, filename)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"缺少数据文件: {file_path}")

            df = self.read_csv(file_path)
            df = df.rename(columns={column: snake_to_camel(column) for column in df.columns})
            df["dataSource"] = source_label
            frames.append(df)
            logger.info(f"已读取 {filename}，记录数 {len(df)}")

        combined = pd.concat(frames, ignore_index=True, sort=False)
        return combined

    def infer_sql_type(self, column_name, series):
        if column_name == "id":
            return "BIGINT NOT NULL"

        if column_name == "dataSource":
            return "VARCHAR(16) NOT NULL"

        if column_name in {"createTime", "updateTime"}:
            return "DATETIME NOT NULL"

        non_null = series.dropna()
        if non_null.empty:
            return "DOUBLE NULL"

        if column_name == "surveyTime":
            return "VARCHAR(32) NULL"

        numeric = pd.to_numeric(non_null, errors="coerce")
        if numeric.notna().all():
            numeric = numeric.astype(float)
            integer_like = np.all(np.isclose(numeric, np.round(numeric)))
            if integer_like:
                return "BIGINT NULL"
            return "DOUBLE NULL"

        max_length = int(non_null.astype(str).str.len().max())
        if max_length <= 255:
            return f"VARCHAR({max(32, max_length)}) NULL"
        return "TEXT NULL"

    def create_database(self):
        logger.info(f"准备创建数据库 {self.database_name}")
        with self.get_server_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database_name}` "
                    "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.commit()
        logger.info(f"数据库 {self.database_name} 已就绪")

    def create_table(self, table_name, dataframe):
        sql_columns = []

        ordered_columns = list(dataframe.columns)
        if "id" in ordered_columns:
            ordered_columns.insert(0, ordered_columns.pop(ordered_columns.index("id")))

        for column_name in ordered_columns:
            sql_type = self.infer_sql_type(column_name, dataframe[column_name])
            sql_columns.append(f"`{column_name}` {sql_type}")

        sql_columns.append("`createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
        sql_columns.append(
            "`updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )

        if "id" in ordered_columns:
            sql_columns.append("PRIMARY KEY (`id`)")

        create_sql = (
            f"DROP TABLE IF EXISTS `{table_name}`; "
            f"CREATE TABLE `{table_name}` ({', '.join(sql_columns)}) "
            "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        )

        with self.get_db_conn() as conn:
            with conn.cursor() as cursor:
                for statement in create_sql.split("; "):
                    cursor.execute(statement)
                self.create_indexes(cursor, table_name, ordered_columns)
            conn.commit()

        logger.info(f"表 {table_name} 已重建完成")

    def create_indexes(self, cursor, table_name, available_columns):
        for template, columns in INDEX_SPECS:
            if not all(column in available_columns for column in columns):
                continue
            index_name = template.format(table=table_name.replace("py_", ""))
            column_sql = ", ".join(f"`{column}`" for column in columns)
            cursor.execute(f"CREATE INDEX `{index_name}` ON `{table_name}` ({column_sql})")

    def insert_dataframe(self, table_name, dataframe):
        insert_columns = list(dataframe.columns)
        column_sql = ", ".join(f"`{column}`" for column in insert_columns)
        placeholder_sql = ", ".join(["%s"] * len(insert_columns))
        insert_sql = f"INSERT INTO `{table_name}` ({column_sql}) VALUES ({placeholder_sql})"

        normalized = dataframe.replace({np.nan: None})
        rows = list(normalized.itertuples(index=False, name=None))

        with self.get_db_conn() as conn:
            with conn.cursor() as cursor:
                for start in range(0, len(rows), self.batch_size):
                    batch = rows[start : start + self.batch_size]
                    cursor.executemany(insert_sql, batch)
            conn.commit()

        logger.info(f"表 {table_name} 已写入 {len(rows)} 条记录")

    def verify_table(self, table_name):
        with self.get_db_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT dataSource, COUNT(*) AS total FROM `{table_name}` GROUP BY dataSource ORDER BY dataSource"
                )
                stats = cursor.fetchall()
        logger.info(f"{table_name} 数据分布: {stats}")
        return stats

    def run_import(self):
        self.create_database()
        for table_name in TABLE_SPECS:
            logger.info("=" * 60)
            logger.info(f"开始初始化表 {table_name}")
            dataframe = self.load_table_dataframe(table_name)
            self.create_table(table_name, dataframe)
            self.insert_dataframe(table_name, dataframe)
            self.verify_table(table_name)
        logger.info("🎉 幸福感数据库初始化完成")


if __name__ == "__main__":
    HappinessDataImporter().run_import()
