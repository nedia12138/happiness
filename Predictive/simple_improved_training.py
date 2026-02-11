import pandas as pd
import numpy as np
import pymysql
import json
import pickle
import os
from datetime import datetime
import warnings
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings('ignore')


# ==========================================
# 1. 核心算法类 (内置封装，确保加载永不报错)
# ==========================================

class SuperiorLinearRegression:
    def __init__(self, alpha=5.0):
        self.alpha = alpha
        self.weights = None
        self.bias = 0

    def fit(self, X, y):
        X_b = np.c_[np.ones(X.shape[0]), X]
        I = np.eye(X_b.shape[1]);
        I[0, 0] = 0
        params, _, _, _ = np.linalg.lstsq(X_b.T @ X_b + self.alpha * I, X_b.T @ y, rcond=None)
        self.bias = params[0]
        self.weights = params[1:]

    def predict(self, X):
        return X @ self.weights + self.bias


class SuperiorRandomForest:
    def __init__(self, n_estimators=300, max_depth=15):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.trees = []

    def fit(self, X, y):
        for i in range(self.n_estimators):
            idx = np.random.choice(len(y), len(y), replace=True)
            tree = DecisionTreeRegressor(max_depth=self.max_depth, max_features='sqrt', random_state=i)
            tree.fit(X[idx], y[idx])
            self.trees.append(tree)

    def predict(self, X):
        return np.mean([t.predict(X) for t in self.trees], axis=0)


# ==========================================
# 2. 核心特征工程：全字段接入
# ==========================================

class SimpleImprovedModel:
    def __init__(self):
        self.model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
        if not os.path.exists(self.model_dir): os.makedirs(self.model_dir)
        self.scaler = RobustScaler()

    def load_data(self):
        conn = pymysql.connect(host='127.0.0.1', user='root', password='12121212', database='0_80123xingfuganwajue',
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        try:
            cursor = conn.cursor()
            # 冲击 0.15 的关键：把这些高解释力字段全部加入查询
            query = """
            SELECT 
                happiness, depression, familyStatus, class, equity, statusPeer, 
                health, incAbility, healthProblem, status3Before, view, relax, 
                car, learn, edu, political, income, familyIncome, floorArea, 
                gender, (2015-birth) as age, marital, workStatus
            FROM py_happiness_survey 
            WHERE happiness BETWEEN 1 AND 5 AND dataSource = 'train'
            """
            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall())
            return df.apply(pd.to_numeric, errors='coerce')
        finally:
            conn.close()

    def feature_engineering(self, df):
        data = df.copy()
        # 1. 基础清理
        target = 'happiness'
        cols = [c for c in data.columns if c != target]

        # 2. 补全缺失值
        for col in cols:
            data[col] = data[col].fillna(data[col].median())

        # 3. 核心非线性特征
        data['age_u'] = (data['age'] - 48) ** 2
        data['log_income'] = np.log1p(data['income'])

        # 4. 关键交互 (阶层 x 资产)
        data['class_wealth'] = data['class'] * data['log_income']

        final_cols = cols + ['age_u', 'log_income', 'class_wealth']
        return data, final_cols

    def run(self):
        print(f"-> 正在执行【全字段增强方案】。正在整合社会学深度特征...")
        df = self.load_data()
        data, all_cols = self.feature_engineering(df)

        X_raw = data[all_cols].values
        y = data['happiness'].values

        X = self.scaler.fit_transform(X_raw)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 训练两个模型
        lr = SuperiorLinearRegression(alpha=10.0)
        rf = SuperiorRandomForest(n_estimators=400, max_depth=12)

        print(f"-> 特征空间已扩展至 {len(all_cols)} 维，开始极限拟合...")
        lr.fit(X_train, y_train)
        rf.fit(X_train, y_train)

        # 混合预测 (0.5 : 0.5 此时全字段下森林表现会极其出色)
        y_pred = 0.5 * lr.predict(X_test) + 0.5 * rf.predict(X_test)
        y_pred = np.clip(y_pred, 1, 5)

        r2 = r2_score(y_test, y_pred)
        print(f"\n[终极全字段结果] 最终 R2 Score: {r2:.4f}")
        print(f"[终极全字段结果] 最终 RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.4f}")

        # 保存闭环模型 (保存为 random_forest.pkl)
        with open(os.path.join(self.model_dir, "random_forest.pkl"), 'wb') as f:
            pickle.dump({
                'lr': lr, 'rf': rf,
                'scaler': self.scaler,
                'cols': all_cols
            }, f)
        print("✓ 训练任务全部结束。")


if __name__ == "__main__":
    SimpleImprovedModel().run()