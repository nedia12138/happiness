import pandas as pd
import numpy as np
import pymysql
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
from config.config import DB_CONFIG

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def run_feature_funnel():
    print("🚀 [特征工程漏斗] 启动！正在连接数据库读取海量原始特征...")
    output_dir = '/Users/nan/Desktop/paper/happiness/Predictive/feature_tools/pic'
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 【终极完美解】：复制配置，并专门为 Pandas 剔除 DictCursor 毒药！
        pandas_db_config = DB_CONFIG.copy()
        pandas_db_config.pop('cursorclass', None)  # 👈 核心杀招：让 Pandas 吃它能消化的 Tuple！

        conn = pymysql.connect(**pandas_db_config)
        query = "SELECT * FROM py_happiness_survey_complete"
        df = pd.read_sql(query, conn)
        conn.close()
        print(f"✅ 成功读取物理数据库，原始行数: {len(df)}")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return

    if 'age' not in df.columns and 'birth' in df.columns:
        df['age'] = 2021 - pd.to_numeric(df['birth'], errors='coerce')

    exclude_cols = ['happiness', 'id', 'index', 'user_id', 'uuid', 'surveytype', 'province', 'city', 'county',
                    'surveytime', 'nationality']
    initial_features = [col for col in df.columns if col.lower() not in exclude_cols]

    df['happiness'] = pd.to_numeric(df['happiness'], errors='coerce')
    df = df.dropna(subset=['happiness'])
    df = df[df['happiness'] > 0]

    print(f"✅ 读取并清洗目标变量后，有效样本数: {len(df)}")

    for col in initial_features:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    print("\n==================================================")
    print("🛡️ 【第一关】缺失值与稀疏度过滤")
    df_clean = df.copy()

    missing_rates = df_clean[initial_features].isnull().mean()
    stage1_features = missing_rates[missing_rates < 0.95].index.tolist()
    print(f"-> 剔除极高缺失率变量后，剩余特征数: {len(stage1_features)}")

    if len(stage1_features) == 0:
        print("❌ 特征全部被过滤，停止执行")
        return

    df_clean[stage1_features] = df_clean[stage1_features].fillna(df_clean[stage1_features].mean())

    print("\n==================================================")
    print("🛡️ 【第二关】皮尔逊相关性检验")
    corr_matrix = df_clean[stage1_features + ['happiness']].corr()
    happiness_corr = corr_matrix['happiness'].drop('happiness')

    stage2_features = happiness_corr[abs(happiness_corr) > 0.01].index.tolist()

    if len(stage2_features) < 6:
        stage2_features = happiness_corr.abs().sort_values(ascending=False).head(20).index.tolist()

    print(f"-> 剔除低相关性噪音后，剩余强/中等相关特征数: {len(stage2_features)}")

    top_corr_features = happiness_corr[stage2_features].abs().sort_values(ascending=False).head(10).index.tolist()

    plt.figure(figsize=(10, 8))
    sns.heatmap(df_clean[top_corr_features + ['happiness']].corr(), annot=True, cmap='RdBu_r', center=0, fmt='.2f')
    plt.title('核心特征与主观幸福感的皮尔逊相关性热力图', fontsize=16)
    heatmap_path = os.path.join(output_dir, '1_Correlation_Heatmap.png')
    plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📸 成功保存相关性热力图至: {heatmap_path}")

    print("\n==================================================")
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
        if len(stage3_features) < 6:
            stage3_features = stage2_features
        print(f"-> 剔除高共线性变量。剩余特征数: {len(stage3_features)}")
    except Exception:
        print("-> VIF 计算跳过，保留原特征池。")
        stage3_features = stage2_features

    print("\n==================================================")
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

    print("\n🏆 核心特征排行榜 (Top 6):")
    for f, imp, cum in zip(sorted_features[:6], sorted_importances[:6], cumulative_importances[:6]):
        print(f"{f:<15}: 单项贡献 {imp:.3f} | 累计贡献 {cum:.3f}")

    plot_features = sorted_features[:6]
    plot_importances = sorted_importances[:6]
    plot_cumulative = cumulative_importances[:6]

    plt.figure(figsize=(10, 6))
    plt.bar(range(len(plot_features)), plot_importances, align='center', color='#8ec5fc')
    plt.xticks(range(len(plot_features)), plot_features, rotation=45, ha='right')
    plt.plot(range(len(plot_features)), plot_cumulative, 'ro-', color='#ff9a9e', linewidth=2, markersize=8)

    plt.title('基于随机森林的 Top 6 核心特征重要度分析', fontsize=15)
    plt.xlabel('特征名称')
    plt.ylabel('重要度 / 累计贡献率')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    importance_path = os.path.join(output_dir, '2_Feature_Importance_Top6.png')
    plt.savefig(importance_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📸 成功保存特征重要度帕累托图至: {importance_path}")

    print("\n" + "🔥" * 25)

    category_weights = {
        '财务自由度': 0.0, '心理抗压能力': 0.0, '人际支持网络': 0.0,
        '身体健康指数': 0.0, '职业满意度': 0.0, '居住环境质量': 0.0
    }

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

    top6_features = sorted_features[:6]
    top6_importances = sorted_importances[:6]

    for col, imp in zip(top6_features, top6_importances):
        cat = category_map.get(col.lower(), '财务自由度')
        category_weights[cat] += float(imp)

    top6_total_w = sum(top6_importances)

    print("\n👇 请把以下代码直接复制替换到 data_analysis.html 里的 ECharts data 中 👇\n")

    for cat, weight in sorted(category_weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0:
            percent = round((weight / top6_total_w) * 100, 1)
        else:
            percent = 0.1
        print(f"{{ value: {percent}, name: '{cat}' }},")

    print("\n" + "🔥" * 25)


if __name__ == '__main__':
    run_feature_funnel()