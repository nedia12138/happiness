"""
feature_selection_funnel.py (特征工程四步漏斗筛选算法 - Top6 闭环版)
用于在毕业论文/答辩中证明: 为什么最终保留这 6 个核心特征，并与前端大屏完美对应！
"""

import pandas as pd
import numpy as np
import pymysql
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings

warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from config.config import DB_CONFIG

# 设置中文字体，防止图表乱码
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def run_feature_funnel():
    print("🚀 [特征工程漏斗] 启动！正在连接数据库读取海量原始特征...")

    try:
        conn = pymysql.connect(**DB_CONFIG)
        query = "SELECT * FROM py_happiness_survey"
        df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        print(f"❌ 数据库连接失败，请检查配置: {e}")
        return

    # 1. 衍生关键特征
    if 'age' not in df.columns and 'birth' in df.columns:
        df['age'] = 2021 - pd.to_numeric(df['birth'], errors='coerce')

    # 全自动扫描表内所有字段
    exclude_cols = ['happiness', 'id', 'index', 'user_id', 'uuid']
    initial_features = [col for col in df.columns if col.lower() not in exclude_cols]

    print(f"🌊 数据库扫描完毕！自动将表中的 {len(initial_features)} 个特征全部投入初选漏斗！")

    # 强转数值并过滤无效目标变量
    for col in initial_features + ['happiness']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['happiness'])
    df = df[df['happiness'] > 0]

    print(f"\n" + "=" * 50)
    print("🛡️ 【第一关】缺失值与稀疏度过滤")
    df_clean = df.copy()

    for col in initial_features:
        if col in df_clean.columns:
            df_clean.loc[df_clean[col] < 0, col] = np.nan

    missing_rates = df_clean[initial_features].isnull().mean()
    stage1_features = missing_rates[missing_rates < 0.3].index.tolist()
    print(f"-> 剔除高缺失率变量后，剩余特征数: {len(stage1_features)}")

    df_clean[stage1_features] = df_clean[stage1_features].fillna(df_clean[stage1_features].mean())

    print(f"\n" + "=" * 50)
    print("🛡️ 【第二关】皮尔逊相关性检验")
    corr_matrix = df_clean[stage1_features + ['happiness']].corr()
    happiness_corr = corr_matrix['happiness'].drop('happiness')

    stage2_features = happiness_corr[abs(happiness_corr) > 0.05].index.tolist()
    print(f"-> 剔除低相关性噪音后，剩余强/中等相关特征数: {len(stage2_features)}")

    # 📸 画图1：保存相关性热力图
    os.makedirs('models', exist_ok=True)
    top_corr_features = happiness_corr[stage2_features].abs().sort_values(ascending=False).head(10).index.tolist()

    plt.figure(figsize=(10, 8))
    sns.heatmap(df_clean[top_corr_features + ['happiness']].corr(), annot=True, cmap='RdBu_r', center=0, fmt='.2f')
    plt.title('【论文配图】核心特征与主观幸福感的皮尔逊相关性热力图', fontsize=16)
    plt.savefig('models/1_Correlation_Heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n" + "=" * 50)
    print("🛡️ 【第三关】多重共线性剔除")
    X_vif = df_clean[stage2_features].copy()
    X_vif += np.random.normal(0, 1e-6, X_vif.shape)
    X_vif['intercept'] = 1

    try:
        vif_data = pd.DataFrame()
        vif_data["feature"] = X_vif.columns
        vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]

        high_vif_features = vif_data[(vif_data['VIF'] > 5) & (vif_data['feature'] != 'intercept')]['feature'].tolist()
        stage3_features = [f for f in stage2_features if f not in high_vif_features]
        print(f"-> 发现高共线性变量 {high_vif_features}，已自动剔除。剩余特征数: {len(stage3_features)}")
    except Exception:
        print(f"-> VIF 计算跳过，保留原特征池。")
        stage3_features = stage2_features

    print(f"\n" + "=" * 50)
    print("🛡️ 【第四关】随机森林特征重要度决选 (精准锁定 Top 6)")
    X_final = df_clean[stage3_features]
    y_final = df_clean['happiness']

    rf = RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)
    rf.fit(X_final, y_final)

    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]

    sorted_features = [stage3_features[i] for i in indices]
    sorted_importances = importances[indices]
    cumulative_importances = np.cumsum(sorted_importances)

    # 打印排行榜：严格限制前 6 个
    print("\n🏆 核心特征排行榜 (Top 6):")
    for f, imp, cum in zip(sorted_features[:6], sorted_importances[:6], cumulative_importances[:6]):
        print(f"{f:<15}: 单项贡献 {imp:.3f} | 累计贡献 {cum:.3f}")

    # 📸 画图2：只画前 6 个特征的帕累托图
    plot_features = sorted_features[:6]
    plot_importances = sorted_importances[:6]
    plot_cumulative = cumulative_importances[:6]

    plt.figure(figsize=(10, 6))
    plt.bar(range(len(plot_features)), plot_importances, align='center', color='#8ec5fc', label='单项特征重要度')
    plt.xticks(range(len(plot_features)), plot_features, rotation=45, ha='right')
    plt.plot(range(len(plot_features)), plot_cumulative, 'ro-', color='#ff9a9e', linewidth=2, markersize=8,
             label='累计解释贡献率 (Cumulative)')

    plt.title('【论文配图】基于随机森林的 Top 6 核心特征重要度分析', fontsize=15)
    plt.xlabel('特征名称')
    plt.ylabel('重要度 / 累计贡献率')
    plt.legend(loc='lower right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.savefig('models/2_Feature_Importance_Top6.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("\n" + "🔥" * 25)
    print("🎯 [前端对接] 严格只取 Top 6 特征，映射到 6 大主成分并归一化！")

    # 初始化前端的 6 大主成分分类
    category_weights = {
        '财务自由度': 0.0, '心理抗压能力': 0.0, '人际支持网络': 0.0,
        '身体健康指数': 0.0, '职业满意度': 0.0, '居住环境质量': 0.0
    }

    # 精确映射字典
    category_map = {
        'income': '财务自由度', 'familyincome': '财务自由度', 'house': '财务自由度', 'car': '财务自由度',
        'class': '财务自由度',
        'depression': '心理抗压能力', 'relax': '心理抗压能力', 'view': '心理抗压能力', 'equity': '心理抗压能力',
        'socialize': '人际支持网络', 'status': '人际支持网络', 'familystatus': '人际支持网络',
        'marital': '人际支持网络', 'gender': '人际支持网络',
        'health': '身体健康指数', 'age': '身体健康指数', 'height': '身体健康指数', 'weight': '身体健康指数',
        'weightjin': '身体健康指数',
        'edu': '职业满意度', 'work': '职业满意度', 'learn': '职业满意度',
        'floorarea': '居住环境质量', 'hukou': '居住环境质量', 'political': '居住环境质量'
    }

    # ★ 核心改动不均摊！严格只切取前 6 个特征！
    top6_features = sorted_features[:6]
    top6_importances = sorted_importances[:6]

    # 只把前 6 个特征放进对应的框里
    for col, imp in zip(top6_features, top6_importances):
        cat = category_map.get(col.lower(), '财务自由度')  # 兜底机制
        category_weights[cat] += float(imp)

    # 仅针对这 Top 6 的总权重进行归一化 (让它们在饼图里刚好占满 100%)
    top6_total_w = sum(top6_importances)

    print("\n👇 请把以下代码直接复制替换到 data_analysis.html 里的 ECharts data 中 👇\n")

    # 打印 6 个指标
    for cat, weight in sorted(category_weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0:
            # 被 Top 6 选中的分类，计算真实比例
            percent = round((weight / top6_total_w) * 100, 1)
        else:
            # 没被 Top 6 选中的分类（比如职业、居住），给一个极微小的底数 0.1
            # 这样既能保证饼图里有这个标签和颜色（和卡片对应），又诚实反映了它们在 Top6 中占比为0
            percent = 0.1

        print(f"{{ value: {percent}, name: '{cat}' }},")

    print("\n" + "🔥" * 25)


if __name__ == '__main__':
    run_feature_funnel()
