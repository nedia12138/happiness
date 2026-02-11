"""
幸福感预测模型
基于机器学习算法构建幸福感预测模型，聚焦教育水平、收入状况、健康状况等关键特征
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pymysql
import json
import pickle
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12121212',
    'database': '0_80123xingfuganwajue',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class HappinessPredictionModel:
    """幸福感预测模型类"""

    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_columns = [
            # 核心特征（已在研究中被验证为显著影响因素）
            'edu',           # 教育水平
            'income',        # 个人收入
            'health',        # 健康状况
            # 辅助特征
            'marital',       # 婚姻状况
            'age',           # 年龄（从出生年份计算）
            'gender',        # 性别
            'familyIncome',  # 家庭收入
            'workStatus',    # 工作状态
            'floorArea',     # 住房面积
        ]
        self.target_column = 'happiness'
        
        # 使用os.path.join确保跨平台兼容
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(current_dir, 'models')

        # 创建模型保存目录
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def get_db_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**DB_CONFIG)

    def load_data_from_db(self, table_name='py_happiness_survey'):
        """从数据库加载数据"""
        print(f"正在从数据库表 {table_name} 加载数据...")

        conn = self.get_db_connection()
        try:
            # 构建查询语句 - 明确指定字段别名
            base_columns = [
                "edu as edu",
                "income as income",
                "health as health",
                "marital as marital",
                "(2015 - birth) as age",
                "gender as gender",
                "familyIncome as familyIncome",
                "workStatus as workStatus",
                "floorArea as floorArea",
                f"{self.target_column} as {self.target_column}",
                "id as id"
            ]

            query = f"""
                SELECT {', '.join(base_columns)}
                FROM {table_name}
                WHERE happiness IS NOT NULL
                AND happiness > 0
                AND happiness <= 5
                AND dataSource = 'train'
            """

            print(f"执行SQL查询: {query}")
            # 使用cursor直接执行查询并手动构建DataFrame
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]  # 获取列名
            rows = cursor.fetchall()

            # 手动构建DataFrame
            df = pd.DataFrame(rows, columns=columns)
            print(f"成功加载 {len(df)} 条记录")

            # 检查数据
            print(f"列名: {list(df.columns)}")
            print(f"数据形状: {df.shape}")

            return df

        except Exception as e:
            print(f"数据加载失败: {e}")
            return None
        finally:
            conn.close()

    def preprocess_data(self, df):
        """数据预处理"""
        print("开始数据预处理...")

        # 创建副本避免修改原数据
        data = df.copy()

        # 年龄已在SQL中计算完成

        # 处理缺失值
        print("处理缺失值...")

        # 检查数据加载后的情况
        print("数据加载后的样本:")
        print(data.head())
        print("\n数据加载后的缺失值统计:")
        missing_before = data.isnull().sum()
        for col, count in missing_before.items():
            if count > 0:
                print(f"  {col}: {count} 缺失")

        # 转换数据类型并填充缺失值
        print("转换数据类型并填充缺失值...")

        # 数值型特征转换为float并填充
        numeric_features = ['income', 'familyIncome', 'floorArea', 'age']
        for col in numeric_features:
            if col in data.columns:
                # 先转换为数值，NULL变为NaN
                data[col] = pd.to_numeric(data[col], errors='coerce')
                # 用中位数填充NaN
                median_val = data[col].median()
                if pd.isna(median_val):
                    median_val = 0  # 如果中位数也是NaN，用0填充
                data[col] = data[col].fillna(median_val)
                print(f"{col} 转换为数值类型，用 {median_val:.2f} 填充缺失值")

        # 分类特征转换为int并填充
        categorical_features = ['edu', 'health', 'marital', 'gender', 'workStatus']
        for col in categorical_features:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
                # 用0填充缺失值（表示未知类别）
                data[col] = data[col].fillna(0)
                print(f"{col} 转换为数值类型，用 0 填充缺失值")

        # 分类特征用众数填充
        categorical_features = ['edu', 'health', 'marital', 'gender', 'workStatus']
        for col in categorical_features:
            if col in data.columns:
                mode_series = data[col].mode()
                if len(mode_series) > 0:
                    mode_val = mode_series.iloc[0]
                    data[col] = data[col].fillna(mode_val)
                    print(f"{col} 缺失值用众数 {mode_val} 填充")
                else:
                    # 如果没有众数，用固定值填充
                    data[col] = data[col].fillna(0)
                    print(f"{col} 缺失值用默认值 0 填充")

        # 检查剩余缺失值
        missing_after_fill = data.isnull().sum()
        print("填充后的缺失值统计:")
        for col, count in missing_after_fill.items():
            if count > 0:
                print(f"{col}: {count} 缺失 ({count/len(data)*100:.1f}%)")

        # 只删除目标变量缺失的记录
        initial_count = len(data)
        data = data.dropna(subset=[self.target_column])
        final_count = len(data)
        print(f"删除目标变量缺失的记录: {initial_count - final_count} 条，剩余 {final_count} 条记录")

        # 对于特征的缺失值，用0填充（作为缺失值标记）
        feature_cols = [col for col in self.feature_columns if col in data.columns]
        for col in feature_cols:
            data[col] = data[col].fillna(0)

        # 数据类型转换 - 先处理NULL值
        data[self.target_column] = pd.to_numeric(data[self.target_column], errors='coerce')
        data = data.dropna(subset=[self.target_column])  # 删除happiness为NULL的记录
        data[self.target_column] = data[self.target_column].astype(int)

        # 确保特征列存在
        available_features = [col for col in self.feature_columns if col in data.columns]
        print(f"可用特征: {available_features}")

        # 检查每列的数据类型和取值范围
        print("特征数据检查:")
        for col in available_features:
            unique_vals = data[col].nunique()
            print(f"  {col}: {unique_vals} 个唯一值, 类型: {data[col].dtype}")

        final_data = data[available_features + [self.target_column, 'id']].copy()
        print(f"最终数据集大小: {len(final_data)} 行, {len(available_features)} 个特征")

        return final_data

    def prepare_features_and_target(self, data):
        """准备特征和目标变量"""
        print("准备特征和目标变量...")

        # 分离特征和目标
        X = data[self.feature_columns]
        y = data[self.target_column]

        print(f"特征矩阵形状: {X.shape}")
        print(f"目标变量形状: {y.shape}")

        # 特征标准化
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=self.feature_columns)

        print("特征标准化完成")
        print(f"幸福感分布: {y.value_counts().sort_index()}")

        return X_scaled, y

    def train_random_forest(self, X_train, y_train):
        """训练随机森林模型（使用ExtraTreesRegressor避免兼容性问题）"""
        print("训练随机森林模型...")

        # 使用ExtraTreesRegressor替代RandomForestRegressor，避免monotonic_cst问题
        rf = ExtraTreesRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=1
        )

        print("开始训练ExtraTrees模型...")
        rf.fit(X_train, y_train)
        print("ExtraTrees模型训练完成")

        self.models['random_forest'] = rf
        return rf

    def train_linear_regression(self, X_train, y_train):
        """训练线性回归模型"""
        print("训练线性回归模型...")

        lr = LinearRegression()
        lr.fit(X_train, y_train)

        print("线性回归模型训练完成")
        self.models['linear_regression'] = lr
        return lr

    def evaluate_model(self, model, X_test, y_test, model_name):
        """评估模型性能"""
        print(f"\n评估{model_name}模型性能...")

        # 预测
        y_pred = model.predict(X_test)

        # 计算评估指标
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # 交叉验证分数
        cv_scores = cross_val_score(model, X_test, y_test, cv=5, scoring='neg_mean_squared_error')
        cv_rmse = np.sqrt(-cv_scores.mean())

        metrics = {
            'model_name': model_name,
            'mse': round(mse, 4),
            'rmse': round(rmse, 4),
            'mae': round(mae, 4),
            'r2_score': round(r2, 4),
            'cv_rmse': round(cv_rmse, 4),
            'cv_scores': [round(score, 4) for score in cv_scores]
        }

        print(f"MSE (均方误差): {metrics['mse']}")
        print(f"RMSE (均方根误差): {metrics['rmse']}")
        print(f"MAE (平均绝对误差): {metrics['mae']}")
        print(f"R2 得分: {metrics['r2_score']}")
        print(f"交叉验证RMSE: {metrics['cv_rmse']}")

        return metrics, y_pred

    def get_feature_importance(self, model, model_name):
        """获取特征重要性"""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            feature_importance = dict(zip(self.feature_columns, importance))
            # 按重要性排序
            sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_importance)
        return None

    def save_model(self, model, model_name, metrics):
        """保存模型"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_filename = f"{model_name}_{timestamp}.pkl"
        model_path = os.path.join(self.model_dir, model_filename)

        # 保存模型
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'metrics': metrics,
                'timestamp': timestamp
            }, f)

        print(f"模型已保存到: {model_path}")
        return model_path

    def save_metrics_to_db(self, metrics, model_name, dataset_type='test'):
        """保存评估指标到数据库"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO py_happiness_model_metrics
                    (modelName, modelVersion, datasetType, mse, rmse, mae, r2Score,
                     crossValidationScores, evaluationTime)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """

                cv_scores_json = json.dumps(metrics.get('cv_scores', []))

                cursor.execute(sql, (
                    model_name,
                    'v1.0',
                    dataset_type,
                    metrics.get('mse'),
                    metrics.get('rmse'),
                    metrics.get('mae'),
                    metrics.get('r2_score'),
                    cv_scores_json
                ))

                conn.commit()
                print(f"{model_name} 评估指标已保存到数据库")

        except Exception as e:
            print(f"保存评估指标失败: {e}")
        finally:
            conn.close()

    def run_pipeline(self):
        """运行完整的模型训练流水线"""
        print("=" * 60)
        print("幸福感预测模型训练流水线")
        print("=" * 60)

        # 1. 加载数据
        data = self.load_data_from_db()
        if data is None or len(data) == 0:
            print("无法加载数据，程序退出")
            return

        # 2. 数据预处理
        processed_data = self.preprocess_data(data)
        if len(processed_data) == 0:
            print("预处理后无有效数据，程序退出")
            return

        # 3. 准备特征和目标
        X, y = self.prepare_features_and_target(processed_data)

        # 4. 数据分割
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"\n训练集大小: {len(X_train)}")
        print(f"测试集大小: {len(X_test)}")

        # 5. 训练随机森林模型
        rf_model = self.train_random_forest(X_train, y_train)

        # 6. 训练线性回归模型
        lr_model = self.train_linear_regression(X_train, y_train)

        # 7. 评估模型
        rf_metrics, rf_predictions = self.evaluate_model(rf_model, X_test, y_test, "随机森林")
        lr_metrics, lr_predictions = self.evaluate_model(lr_model, X_test, y_test, "线性回归")

        # 8. 获取特征重要性
        rf_feature_importance = self.get_feature_importance(rf_model, "随机森林")

        # 9. 比较模型性能并选择最佳模型
        models_metrics = {
            'random_forest': rf_metrics,
            'linear_regression': lr_metrics
        }

        # 基于R²和RMSE选择最佳模型
        best_model_name = max(models_metrics.keys(),
                            key=lambda x: (models_metrics[x]['r2_score'], -models_metrics[x]['rmse']))

        print(f"\n最佳模型: {best_model_name}")
        print(".4f")

        # 10. 保存所有模型
        saved_models = {}
        for model_name, model in self.models.items():
            metrics = models_metrics[model_name]
            model_path = self.save_model(model, model_name, metrics)
            saved_models[model_name] = model_path

        # 确定最佳模型路径
        best_model_path = saved_models[best_model_name]

        # 11. 保存评估指标到数据库
        for model_name, metrics in models_metrics.items():
            self.save_metrics_to_db(metrics, model_name)

        # 12. 输出特征重要性
        if rf_feature_importance:
            print("\n随机森林特征重要性:")
            for feature, importance in rf_feature_importance.items():
                print(".4f")

        # 13. 保存模型信息到文件
        self.save_model_info(best_model_name, models_metrics, rf_feature_importance, saved_models)

        print("\n" + "=" * 60)
        print("模型训练完成！")
        print(f"最佳模型: {best_model_name}")
        print(f"模型文件: {model_path}")
        print("=" * 60)

        return best_model_name, model_path

    def save_model_info(self, best_model_name, all_metrics, feature_importance, model_paths):
        """保存模型信息到文件"""
        # 将路径转换为相对路径（仅保存文件名）
        relative_paths = {}
        for model_name, path in model_paths.items():
            if path:
                relative_paths[model_name] = os.path.basename(path)
            else:
                relative_paths[model_name] = ''
        
        info = {
            'best_model': best_model_name,
            'all_models': {
                'random_forest': {
                    'metrics': all_metrics.get('random_forest', {}),
                    'path': relative_paths.get('random_forest', '')
                },
                'linear_regression': {
                    'metrics': all_metrics.get('linear_regression', {}),
                    'path': relative_paths.get('linear_regression', '')
                }
            },
            'feature_importance': feature_importance,
            'feature_columns': self.feature_columns,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        info_path = os.path.join(self.model_dir, 'model_info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

        print(f"模型信息已保存到: {info_path}")


def main():
    """主函数"""
    try:
        # 创建预测模型实例
        predictor = HappinessPredictionModel()

        # 运行完整的训练流水线
        best_model, model_path = predictor.run_pipeline()

        print("\n幸福感预测模型构建完成！")
        print(f"最佳模型: {best_model}")
        print(f"模型保存路径: {model_path}")

    except Exception as e:
        print(f"模型训练过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
