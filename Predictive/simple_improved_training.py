import pandas as pd
import numpy as np
import pymysql
import pickle
import os
import warnings
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import RobustScaler

# 设置绘图中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')


# ==========================================
# 1. 核心算法类
# ==========================================

class SuperiorLinearRegression:
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.weights = None
        self.bias = 0

    def fit(self, X, y):
        X_b = np.c_[np.ones(X.shape[0]), X]
        I = np.eye(X_b.shape[1])
        I[0, 0] = 0
        params, _, _, _ = np.linalg.lstsq(X_b.T @ X_b + self.alpha * I, X_b.T @ y, rcond=None)
        self.bias = params[0]
        self.weights = params[1:]

    def predict(self, X):
        return X @ self.weights + self.bias


class SuperiorRandomForest:
    def __init__(self, n_estimators=400, max_depth=14):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.trees = []

    def fit(self, X, y):
        self.trees = []
        for _ in range(self.n_estimators):
            indices = np.random.choice(len(X), len(X), replace=True)
            tree = DecisionTreeRegressor(max_depth=self.max_depth, random_state=np.random.randint(1000))
            tree.fit(X[indices], y[indices])
            self.trees.append(tree)

    def predict(self, X):
        return np.mean([t.predict(X) for t in self.trees], axis=0)


# ==========================================
# 2. 训练与多指标分析引擎
# ==========================================

class SimpleImprovedModel:
    def __init__(self):
        self.db_config = {"host": "localhost", "user": "root", "password": "12121212", "database": "0_80123xingfuganwajue",
                          "charset": "utf8mb4"}
        self.scaler = RobustScaler()
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.model_save_path = os.path.join(self.base_path, 'models')
        if not os.path.exists(self.model_save_path): os.makedirs(self.model_save_path)

    def load_data(self):
        conn = pymysql.connect(**self.db_config)
        df = pd.read_sql("SELECT * FROM py_happiness_survey_complete WHERE dataSource='train' AND happiness>0", conn)
        conn.close()
        df.columns = [c.lower().replace('_', '') for c in df.columns]
        return df

    def feature_engineering(self, df):
        data = df.copy()
        # 精选 25 个核心社会学特征
        core_cols = [
            'income', 'health', 'edu', 'marital', 'gender', 'house', 'car', 'status_peer', 'view', 'birth',
            'depression', 'equity', 'class', 'socialize', 'relax', 'learn', 'workstatus', 'familystatus',
            'political', 'hukou', 'religion', 'floorarea', 'heightcm', 'weightjin', 'familyincome'
        ]
        valid_features = [c for c in core_cols if c in data.columns]
        for c in valid_features:
            data[c] = pd.to_numeric(data[c], errors='coerce').fillna(data[c].median())
        # class_wealth（体现主观地位与财富的交互）：
        # age_u（体现幸福感随年龄的U型波动）：
        # log_income（解决收入边际效用递减）：
        data['log_income'] = np.log1p(data['income'].clip(lower=0))
        data['age'] = 2015 - data['birth']
        data['age_u'] = (data['age'] - 48) ** 2
        data['class_wealth'] = data.get('status_peer', 0) * data['log_income']

        final_cols = valid_features + ['age_u', 'log_income', 'class_wealth']
        return data.replace([np.inf, -np.inf], 0).fillna(0), final_cols

    def print_metrics_table(self, y_true, y_pred, name):
        """格式化打印评估指标"""
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        print(f"| {name:<12} | {r2:.4f} | {mse:.4f} | {rmse:.4f} | {mae:.4f} |")

    def run(self):
        print(f"-> 🚨 启动全指标对比训练流程...")
        df = self.load_data()
        data, all_cols = self.feature_engineering(df)
        X, y = self.scaler.fit_transform(data[all_cols].values), data['happiness'].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 初始化模型
        lr = SuperiorLinearRegression(alpha=0.5)
        rf = SuperiorRandomForest(n_estimators=400, max_depth=14)

        # 训练
        print("-> 正在进行模型拟合...")
        lr.fit(X_train, y_train)
        rf.fit(X_train, y_train)

        # 分别获取预测结果
        y_pred_lr = np.clip(lr.predict(X_test), 1, 5)
        y_pred_rf = np.clip(rf.predict(X_test), 1, 5)
        y_pred_hybrid = np.clip(0.3 * y_pred_lr + 0.7 * y_pred_rf, 1, 5)

        # 打印结果表格
        print("\n" + "=" * 65)
        print(f"| {'算法模型':<10} | {'R2 (↑)':<6} | {'MSE (↓)':<6} | {'RMSE (↓)':<6} | {'MAE (↓)':<6} |")
        print("-" * 65)
        self.print_metrics_table(y_test, y_pred_lr, "线性回归")
        self.print_metrics_table(y_test, y_pred_rf, "随机森林")
        self.print_metrics_table(y_test, y_pred_hybrid, "混合模型")
        print("=" * 65)

        # 保存为网页端需要的格式
        save_path = os.path.join(self.model_save_path, 'random_forest.pkl')
        with open(save_path, 'wb') as f:
            pickle.dump({
                'lr': lr,
                'rf': rf,
                'scaler': self.scaler,
                'cols': all_cols
            }, f)
        print(f"\n✅ 最佳模型（混合权重版）已同步至: {save_path}")


if __name__ == '__main__':
    SimpleImprovedModel().run()