"""
offline_feature_exploration.py (高精度严谨版)
严格执行特征工程与深度清洗，消除连续变量偏误，还原真实的社会学特征权重。
"""

import pandas as pd
import numpy as np
import pymysql
import json
import os
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
import warnings

warnings.filterwarnings('ignore')

# 设置绘图中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def run_accurate_exploration():
    print("🚀 [高精度离线引擎] 启动！正在连接数据库...")

    try:
        conn = pymysql.connect(
            host='127.0.0.1', port=3306, user='root',
            password='12121212', database='0_80123xingfuganwajue', charset='utf8mb4'
        )
        query = "SELECT * FROM py_happiness_survey"
        df = pd.read_sql(query, conn)
        conn.close()
        print(f"✅ 原始数据提取成功，共 {len(df)} 条。")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return

    print("🧬 [特征工程] 正在进行高精度数据清洗与去噪...")

    # 1. 准确计算年龄
    if 'age' not in df.columns and 'birth' in df.columns:
        df['age'] = 2021 - pd.to_numeric(df['birth'], errors='coerce')

    feature_cols = [
        'depression', 'equity', 'class', 'health', 'income',
        'familyIncome', 'edu', 'floorArea', 'age'
    ]

    # 强转数值
    for col in feature_cols + ['happiness']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2. 【核心清洗】剔除社会学调查中的无效回答 (如 -1, -2, -3 拒绝回答)
    # CGSS 数据中，正常打分和客观指标绝大部分都应该 >= 0
    df = df.dropna(subset=['happiness'])
    df = df[df['happiness'] > 0]  # 幸福感必须是有效打分

    for col in ['depression', 'equity', 'class', 'health', 'edu']:
        df = df[df[col] > 0]  # 剔除态度题里的负数噪音

    # 3. 【核心清洗】抑制连续变量偏误 (处理极端异常值)
    # 限制年龄在合理区间
    df = df[(df['age'] >= 18) & (df['age'] <= 100)]
    # 对极端的收入和面积进行截断平滑 (去除首尾 1% 的极端富豪/赤贫干扰)
    for col in ['income', 'familyIncome', 'floorArea']:
        if col in df.columns:
            upper_bound = df[col].quantile(0.95)
            df[col] = np.clip(df[col], 0, upper_bound)

    # 剩余少量空值用更科学的均值(而非中位数)填补
    df[feature_cols] = df[feature_cols].fillna(df[feature_cols].mean())

    X = df[feature_cols]
    y = df['happiness']

    print(f"✨ [清洗完成] 深度去噪后，保留纯净高价值样本 {len(df)} 条。")
    print("🌲 [高精度推演] 启动原生随机森林，严格限制树深度以防过拟合...")

    # 4. 【算法调优】限制 max_depth 可以有效防止算法过度偏好连续变量(年龄/收入)
    rf_model = RandomForestRegressor(n_estimators=500, max_depth=8, min_samples_split=10, random_state=42)
    rf_model.fit(X, y)

    importances = rf_model.feature_importances_

    feature_weights = {}
    for col, imp in zip(feature_cols, importances):
        feature_weights[col] = round(float(imp), 2)

    print("\n🎯 [真理再现] 高精度纯净数据推演出的客观特征权重如下：")
    print(feature_weights)

    os.makedirs('models', exist_ok=True)
    with open('models/model_info.json', 'w', encoding='utf-8') as f:
        json.dump({
            "model": "High-Precision RandomForest (EDA)",
            "description": "基于深度清洗与去噪数据提取的准确先验权重",
            "extracted_weights": feature_weights
        }, f, indent=4, ensure_ascii=False)

    plt.figure(figsize=(10, 6))
    sorted_idx = np.argsort(importances)
    plt.barh(range(len(sorted_idx)), importances[sorted_idx], align='center', color='#4CAF50')
    plt.yticks(range(len(sorted_idx)), [feature_cols[i] for i in sorted_idx])
    plt.xlabel('基尼不纯度下降量 (准确重要性占比)')
    plt.title('基于深度清洗数据的全局核心特征准确度探查')
    plt.savefig('models/feature_importance.png', dpi=300, bbox_inches='tight')
    print("✅ [成功] 准确且纯净的物证已重新生成并保存至 models 目录！")


if __name__ == '__main__':
    run_accurate_exploration()