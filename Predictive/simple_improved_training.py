import pandas as pd
import numpy as np
import pymysql
import pickle
import os
import warnings
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import RobustScaler

# 设置绘图中文字体（适配 Mac/Windows）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')


# ==========================================
# 1. 核心算法类 (锁定 0.2626 高分的强力参数)
# ==========================================

class SuperiorLinearRegression:
    def __init__(self, alpha=0.1):
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
    def __init__(self, n_estimators=500, max_depth=16):  # 500棵树，16层深度
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
# 2. 训练与可视化分析引擎
# ==========================================

class SimpleImprovedModel:
    def __init__(self):
        self.db_config = {
            "host": "localhost", "user": "root", "password": "12121212",
            "database": "0_80123xingfuganwajue", "charset": "utf8mb4"
        }
        self.scaler = RobustScaler()
        # 统一模型保存路径
        self.base_path = os.path.dirname(__file__)
        self.model_save_path = os.path.join(self.base_path, '../models')
        if not os.path.exists(self.model_save_path):
            os.makedirs(self.model_save_path)

    def load_data(self):
        conn = pymysql.connect(**self.db_config)
        # 读取全部列，确保 137 维特征可见
        df = pd.read_sql("SELECT * FROM py_happiness_survey_complete WHERE dataSource='train' AND happiness>0", conn)
        conn.close()

        # 兼容性字段处理
        df.columns = [c.lower().replace('_', '') for c in df.columns]
        mapping = {'statuspeer': 'status_peer', 'edustatus': 'edu_status', 'workstatus': 'work_status'}
        for k, v in mapping.items():
            if k in df.columns: df = df.rename(columns={k: v})
        return df

    def feature_engineering(self, df):
        data = df.copy()
        # 自动识别数值特征
        exclude = ['id', 'datasource', 'happiness', 'surveyid', 'id_duplicate']
        potential_features = [c for c in data.columns if c not in exclude]

        valid_features = []
        for c in potential_features:
            # 强制转换为数值，解决 Median 报错问题
            numeric_col = pd.to_numeric(data[c], errors='coerce')
            if numeric_col.isna().all(): continue
            data[c] = numeric_col.fillna(numeric_col.median())
            valid_features.append(c)

        # 0.26 分数的“神级”衍生特征
        data['log_income'] = np.log1p(data['income'].clip(lower=0))
        data['age'] = 2015 - data['birth']
        data['age_u'] = (data['age'] - 48) ** 2  # 48岁幸福感 U 型拐点
        data['class_wealth'] = data.get('status_peer', 0) * data['log_income']

        final_cols = valid_features + ['age_u', 'log_income', 'class_wealth']
        final_cols = list(dict.fromkeys([c for c in final_cols if c in data.columns]))

        # 数值安全：替换 inf 为 0
        data = data.replace([np.inf, -np.inf], 0).fillna(0)
        return data, final_cols

    def run(self):
        print(f"-> 🚨 正在启动【全字段分析版】训练。目标分数: 0.26+")
        try:
            df = self.load_data()
            data, all_cols = self.feature_engineering(df)
            print(f"-> 特征维度已就绪：{len(all_cols)} 维")

            X_raw = data[all_cols].values
            y = pd.to_numeric(data['happiness'], errors='coerce').fillna(3).values
            X_raw = np.nan_to_num(X_raw)

            X = self.scaler.fit_transform(X_raw)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            lr = SuperiorLinearRegression(alpha=0.1)
            rf = SuperiorRandomForest(n_estimators=500, max_depth=16)

            print(f"-> 正在进行深度非线性拟合...")
            lr.fit(X_train, y_train)
            rf.fit(X_train, y_train)

            # 融合预测 (0.3 : 0.7)
            y_pred = (0.3 * lr.predict(X_test)) + (0.7 * rf.predict(X_test))
            y_pred = np.clip(y_pred, 1, 5)
            r2 = r2_score(y_test, y_pred)

            print("\n" + "💎" * 25)
            print(f" [任务完成] 最终 R2 Score: {r2:.4f}")
            print("💎" * 25)

            # === 特征重要性可视化 ===
            print("\n" + "📊" * 15)
            print(" 影响幸福感的核心因素排行 (TOP 10):")
            # 计算森林中所有树的平均重要性
            importances = np.mean([tree.feature_importances_ for tree in rf.trees], axis=0)
            feature_rank = sorted(zip(all_cols, importances), key=lambda x: x[1], reverse=True)

            top_features = feature_rank[:10]
            names, scores = zip(*top_features)

            for i, (name, score) in enumerate(top_features):
                print(f"{i + 1}. {name:<15} 贡献权重: {score:.4f}")

            # 绘制柱状图
            plt.figure(figsize=(10, 6))
            y_pos = np.arange(len(names))
            plt.barh(y_pos, scores[::-1], align='center', color='skyblue', alpha=0.8)
            plt.yticks(y_pos, names[::-1])
            plt.xlabel('特征重要性得分')
            plt.title('影响居民幸福感的主要因素排行 (TOP 10)')
            plt.tight_layout()

            # 保存图表
            img_path = os.path.join(self.model_save_path, 'feature_importance.png')
            plt.savefig(img_path)
            print(f"✅ 可视化报告已保存至: models/feature_importance.png")
            print("📊" * 15)

            # 保存模型
            with open(os.path.join(self.model_save_path, 'happiness_model_advanced.pkl'), 'wb') as f:
                pickle.dump({'model': rf, 'scaler': self.scaler, 'features': all_cols}, f)
            return r2

        except Exception as e:
            print(f"❌ 运行失败: {e}")


if __name__ == '__main__':
    SimpleImprovedModel().run()