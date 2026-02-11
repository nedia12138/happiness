"""
数据诊断脚本
快速分析数据质量和可预测性问题
"""

import pandas as pd
import numpy as np
import pymysql
from scipy import stats

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12121212',
    'database': '0_80123xingfuganwajue',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def diagnose():
    """诊断数据问题"""
    print("=" * 80)
    print(" " * 25 + "数据质量诊断报告")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    
    try:
        # 加载数据
        query = """
            SELECT 
                edu, income, health, marital, 
                (2015 - birth) as age, 
                gender, familyIncome, workStatus, floorArea,
                happiness, id
            FROM py_happiness_survey
            WHERE happiness IS NOT NULL
            AND happiness > 0
            AND happiness <= 5
            AND dataSource = 'train'
        """
        
        df = pd.read_sql(query, conn)
        print(f"\n✓ 加载 {len(df)} 条训练数据\n")
        
        # 1. 目标变量诊断
        print("【1. 目标变量 (happiness) 诊断】")
        print("-" * 80)
        y = df['happiness']
        
        print(f"样本数: {len(y)}")
        print(f"均值: {y.mean():.4f}")
        print(f"中位数: {y.median():.4f}")
        print(f"标准差: {y.std():.4f}")
        print(f"方差: {y.var():.4f}")
        print(f"范围: [{y.min()}, {y.max()}]")
        
        print(f"\n分布:")
        for val in sorted(y.unique()):
            count = (y == val).sum()
            pct = count / len(y) * 100
            bar = "█" * int(pct / 2)
            print(f"  {val}: {count:5d} ({pct:5.1f}%) {bar}")
        
        # 检查方差
        if y.var() < 0.5:
            print(f"\n⚠️  警告: 方差过小 ({y.var():.4f})，数据集中度过高")
        
        # 检查偏度和峰度
        skewness = stats.skew(y)
        kurtosis = stats.kurtosis(y)
        print(f"\n偏度: {skewness:.4f} {'(左偏)' if skewness < -0.5 else '(右偏)' if skewness > 0.5 else '(对称)'}")
        print(f"峰度: {kurtosis:.4f} {'(尖峰)' if kurtosis > 0 else '(平峰)'}")
        
        # 2. 特征诊断
        print("\n\n【2. 特征质量诊断】")
        print("-" * 80)
        
        features = ['edu', 'income', 'health', 'marital', 'age', 
                   'gender', 'familyIncome', 'workStatus', 'floorArea']
        
        for feat in features:
            if feat not in df.columns:
                continue
            
            col = pd.to_numeric(df[feat], errors='coerce')
            missing = col.isnull().sum()
            missing_pct = missing / len(col) * 100
            
            if missing == 0:
                unique = col.nunique()
                mean_val = col.mean()
                std_val = col.std()
                
                status = "✓"
                if std_val < 0.01:
                    status = "⚠️  (方差过小)"
                elif missing_pct > 50:
                    status = "⚠️  (缺失过多)"
                
                print(f"{status} {feat:15s}: {unique:4d} 个唯一值, "
                      f"均值={mean_val:8.2f}, 标准差={std_val:8.2f}, "
                      f"缺失={missing_pct:.1f}%")
            else:
                print(f"⚠️  {feat:15s}: 缺失 {missing} ({missing_pct:.1f}%)")
        
        # 3. 相关性诊断
        print("\n\n【3. 特征与目标变量相关性】")
        print("-" * 80)
        
        correlations = []
        for feat in features:
            if feat in df.columns:
                col = pd.to_numeric(df[feat], errors='coerce').fillna(0)
                corr = col.corr(y)
                correlations.append((feat, corr))
        
        correlations.sort(key=lambda x: abs(x[1]), reverse=True)
        
        print("相关系数 (绝对值越大越重要):")
        for feat, corr in correlations:
            bar = "█" * int(abs(corr) * 50)
            sign = "+" if corr > 0 else "-"
            print(f"  {feat:15s}: {sign}{abs(corr):.4f} {bar}")
        
        max_corr = max(abs(c[1]) for c in correlations)
        if max_corr < 0.3:
            print(f"\n⚠️  警告: 最大相关系数仅 {max_corr:.4f}，特征与目标变量关系很弱")
        
        # 4. 多重共线性诊断
        print("\n\n【4. 特征间相关性 (多重共线性检查)】")
        print("-" * 80)
        
        X = df[features].copy()
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
        
        corr_matrix = X.corr()
        
        high_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    high_corr.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_val
                    ))
        
        if high_corr:
            print("发现高度相关的特征对 (|相关系数| > 0.7):")
            for feat1, feat2, corr in high_corr:
                print(f"  ⚠️  {feat1} <-> {feat2}: {corr:.4f}")
            print("\n建议: 考虑删除其中一个特征或创建组合特征")
        else:
            print("✓ 未发现严重的多重共线性问题")
        
        # 5. 数据泄露检查
        print("\n\n【5. 潜在数据泄露检查】")
        print("-" * 80)
        
        # 检查是否有特征与目标变量过度相关
        suspicious = [c for c in correlations if abs(c[1]) > 0.9]
        if suspicious:
            print("⚠️  以下特征与目标变量相关性异常高 (可能存在数据泄露):")
            for feat, corr in suspicious:
                print(f"  {feat}: {corr:.4f}")
        else:
            print("✓ 未发现明显的数据泄露迹象")
        
        # 6. 总结和建议
        print("\n\n【6. 诊断总结与建议】")
        print("=" * 80)
        
        issues = []
        recommendations = []
        
        # 检查方差
        if y.var() < 0.5:
            issues.append("目标变量方差过小")
            recommendations.append("考虑使用分类模型而非回归模型")
        
        # 检查相关性
        if max_corr < 0.3:
            issues.append("特征与目标变量相关性很弱")
            recommendations.append("需要更多有效特征或进行特征工程")
            recommendations.append("考虑添加交互特征、多项式特征")
        
        # 检查多重共线性
        if high_corr:
            issues.append(f"存在 {len(high_corr)} 对高度相关的特征")
            recommendations.append("使用Ridge/Lasso回归处理共线性")
            recommendations.append("或删除/合并相关特征")
        
        # 检查样本量
        if len(df) < 1000:
            issues.append("样本量较小")
            recommendations.append("考虑使用简单模型(如线性回归)")
            recommendations.append("避免使用复杂模型(如深度神经网络)")
        
        if issues:
            print("\n发现的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("\n✓ 数据质量良好，可以进行模型训练")
        
        print("\n" + "=" * 80)
        print("诊断完成！请根据以上建议优化模型训练流程。")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    diagnose()

