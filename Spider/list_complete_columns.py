#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出完整版数据的所有列名
"""

import pandas as pd
import os

def list_columns():
    """列出完整版数据的所有列名"""

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    train_file = os.path.join(data_dir, 'happiness_train_complete.csv')

    if not os.path.exists(train_file):
        print("文件不存在")
        return

    # 尝试读取
    encodings_to_try = ['utf-8', 'gbk', 'gb2312']
    df = None

    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(train_file, nrows=1, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取")
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        print("无法读取文件")
        return

    print(f"\n完整版数据共有 {len(df.columns)} 个字段:")
    for i, col in enumerate(df.columns, 1):
        print("3d")

if __name__ == '__main__':
    list_columns()
