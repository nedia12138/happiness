"""
快速数据诊断脚本
"""

import pandas as pd
import pymysql

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12121212',
    'database': '0_80123xingfuganwajue',
    'charset': 'utf8mb4'
}

def quick_diagnose():
    conn = pymysql.connect(**DB_CONFIG)
    
    try:
        query = """
            SELECT 
                edu, income, health, marital, 
                (2015 - birth) as age, 
                gender, familyIncome, workStatus, floorArea,
                happiness
            FROM py_happiness_survey
            WHERE happiness IS NOT NULL
            AND happiness > 0
            AND happiness <= 5
            AND dataSource = 'train'
        """
        
        df = pd.read_sql(query, conn)
        
        print("=" * 60)
        print("数据质量诊断报告")
        print("=" * 60)
        
        print(f"\n总样本数: {len(df)}")
        
        # 目标变量分析
        print("\n【目标变量 happiness 分析】")
        y = df['happiness']
        print(f"均值: {y.mean():.4f}")
        print(f"标准差: {y.std():.4f}")
        print(f"方差: {y.var():.4f}")
        
        print("\n分布:")
        for val in sorted(y.unique()):
            count = (y == val).sum()
            pct = count / len(y) * 100
            print(f"  {val}: {count:5d} ({pct:5.1f}%)")
        
        # 特征与目标相关性
        print("\n【特征与目标相关性】")
        features = ['edu', 'income', 'health', 'marital', 'age', 
                   'gender', 'familyIncome', 'workStatus', 'floorArea']
        
        correlations = []
        for feat in features:
            col = pd.to_numeric(df[feat], errors='coerce').fillna(0)
            corr = col.corr(y)
            correlations.append((feat, corr))
        
        correlations.sort(key=lambda x: abs(x[1]), reverse=True)
        
        for feat, corr in correlations:
            print(f"  {feat:15s}: {corr:7.4f}")
        
        max_corr = max(abs(c[1]) for c in correlations)
        
        # 诊断结论
        print("\n【诊断结论】")
        if y.var() < 0.5:
            print("✗ 问题1: 目标变量方差过小，数据集中度过高")
        
        if max_corr < 0.3:
            print(f"✗ 问题2: 特征与目标相关性很弱 (最大相关系数={max_corr:.4f})")
            print("  建议: 需要更多有效特征或进行特征工程")
        
        # 检查多重共线性
        print("\n【多重共线性检查】")
        X = df[features].copy()
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
        
        corr_matrix = X.corr()
        high_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > 0.7:
                    high_corr.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_matrix.iloc[i, j]
                    ))
        
        if high_corr:
            print("发现高度相关的特征对:")
            for f1, f2, c in high_corr:
                print(f"  {f1} <-> {f2}: {c:.4f}")
        else:
            print("✓ 未发现严重多重共线性")
        
        print("\n" + "=" * 60)
        
    finally:
        conn.close()

if __name__ == "__main__":
    quick_diagnose()

