"""
简化版改进模型训练脚本
"""

import pandas as pd
import numpy as np
import pymysql
import json
import pickle
import os
from datetime import datetime
import warnings

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12121212',
    'database': '0_80123xingfuganwajue',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class SimpleImprovedModel:
    """简化版改进模型"""
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_columns = [
            'edu', 'income', 'health', 'marital', 'age', 
            'gender', 'familyIncome', 'workStatus', 'floorArea'
        ]
        self.target_column = 'happiness'
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(current_dir, 'models')
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def load_data(self):
        """加载数据"""
        print("=" * 60)
        print("步骤 1: 加载数据")
        print("=" * 60)
        
        conn = pymysql.connect(**DB_CONFIG)
        try:
            cursor = conn.cursor()
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
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            df = pd.DataFrame(rows, columns=columns)
            print(f"✓ 加载 {len(df)} 条记录")
            print(f"✓ 列名: {list(df.columns)}")
            return df
            
        finally:
            conn.close()
    
    def feature_engineering(self, df):
        """特征工程"""
        print("\n" + "=" * 60)
        print("步骤 2: 特征工程")
        print("=" * 60)
        
        data = df.copy()
        
        # 处理缺失值
        print("\n处理缺失值...")
        for col in self.feature_columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            missing_count = data[col].isnull().sum()
            if missing_count > 0:
                if col in ['income', 'familyIncome', 'floorArea', 'age']:
                    fill_val = data[col].median()
                    if pd.isna(fill_val):
                        fill_val = 0
                    data[col] = data[col].fillna(fill_val)
                else:
                    mode_val = data[col].mode()
                    fill_val = mode_val[0] if len(mode_val) > 0 else 0
                    data[col] = data[col].fillna(fill_val)
                print(f"  {col}: 填充 {missing_count} 个缺失值")
        
        # 创建交互特征
        print("\n创建交互特征...")
        data['edu_income'] = data['edu'] * np.log1p(data['income'])
        data['health_age'] = data['health'] * data['age']
        data['income_ratio'] = data['income'] / (data['familyIncome'] + 1)
        
        # 处理交互特征中的 NaN 和 inf
        for col in ['edu_income', 'health_age', 'income_ratio']:
            data[col] = data[col].replace([np.inf, -np.inf], 0)
            data[col] = data[col].fillna(0)
        
        # 添加到特征列表
        self.feature_columns.extend(['edu_income', 'health_age', 'income_ratio'])
        
        # 最终检查：确保没有 NaN
        for col in self.feature_columns:
            if data[col].isnull().sum() > 0:
                print(f"  警告: {col} 仍有 {data[col].isnull().sum()} 个缺失值，用0填充")
                data[col] = data[col].fillna(0)
        
        print(f"\n✓ 特征工程完成，共 {len(self.feature_columns)} 个特征")
        print(f"✓ 最终样本数: {len(data)}")
        
        return data
    
    def prepare_data(self, data):
        """准备训练数据"""
        print("\n" + "=" * 60)
        print("步骤 3: 数据准备")
        print("=" * 60)
        
        X = data[self.feature_columns].copy()
        y = data[self.target_column].copy()
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=self.feature_columns, index=X.index)
        
        # 分层抽样
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, 
            test_size=0.2, 
            random_state=42,
            stratify=y
        )
        
        print(f"✓ 训练集: {len(X_train)} 样本")
        print(f"✓ 测试集: {len(X_test)} 样本")
        
        return X_train, X_test, y_train, y_test
    
    def train_models(self, X_train, y_train):
        """训练模型（仅随机森林和线性回归）"""
        print("\n" + "=" * 60)
        print("步骤 4: 模型训练")
        print("=" * 60)
        
        models_config = {
            'linear_regression': LinearRegression(),
            'random_forest': RandomForestRegressor(
                n_estimators=100, 
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1
            )
        }
        
        for name, model in models_config.items():
            print(f"\n训练 {name}...")
            model.fit(X_train, y_train)
            self.models[name] = model
            print(f"  ✓ 完成")
        
        return self.models
    
    def evaluate_models(self, X_train, X_test, y_train, y_test):
        """评估所有模型"""
        print("\n" + "=" * 60)
        print("步骤 5: 模型评估")
        print("=" * 60)
        
        results = {}
        
        # 基线模型
        baseline_pred = np.full(len(y_test), y_train.mean())
        baseline_r2 = r2_score(y_test, baseline_pred)
        baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
        
        print(f"\n基线模型 (预测均值 {y_train.mean():.2f}):")
        print(f"  R²: {baseline_r2:.4f}")
        print(f"  RMSE: {baseline_rmse:.4f}")
        print("-" * 60)
        
        for name, model in self.models.items():
            print(f"\n{name}:")
            
            # 训练集
            y_train_pred = model.predict(X_train)
            train_r2 = r2_score(y_train, y_train_pred)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            
            # 测试集
            y_test_pred = model.predict(X_test)
            test_r2 = r2_score(y_test, y_test_pred)
            test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
            test_mae = mean_absolute_error(y_test, y_test_pred)
            
            # 交叉验证
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, 
                                       scoring='neg_mean_squared_error', n_jobs=-1)
            cv_rmse = np.sqrt(-cv_scores.mean())
            
            results[name] = {
                'train_r2': train_r2,
                'train_rmse': train_rmse,
                'test_r2': test_r2,
                'test_rmse': test_rmse,
                'test_mae': test_mae,
                'cv_rmse': cv_rmse,
                'cv_scores': cv_scores.tolist()
            }
            
            print(f"  训练集 R²: {train_r2:.4f} | RMSE: {train_rmse:.4f}")
            print(f"  测试集 R²: {test_r2:.4f} | RMSE: {test_rmse:.4f} | MAE: {test_mae:.4f}")
            print(f"  交叉验证 RMSE: {cv_rmse:.4f}")
            
            # 判断
            if train_r2 - test_r2 > 0.1:
                print(f"  ⚠️  可能过拟合 (差距 {train_r2-test_r2:.4f})")
            
            if test_r2 > baseline_r2:
                improvement = test_r2 - baseline_r2
                print(f"  ✓ 优于基线 (提升 {improvement:.4f})")
            else:
                print(f"  ✗ 未优于基线")
        
        return results
    
    def save_models(self, results):
        """保存所有模型"""
        print("\n" + "=" * 60)
        print("步骤 6: 保存模型")
        print("=" * 60)
        
        # 选择最佳模型
        best_model_name = max(results.keys(), key=lambda x: results[x]['test_r2'])
        
        print(f"\n最佳模型: {best_model_name}")
        print(f"  测试集 R²: {results[best_model_name]['test_r2']:.4f}")
        print(f"  测试集 RMSE: {results[best_model_name]['test_rmse']:.4f}")
        
        # 获取随机森林的特征重要性
        feature_importance = None
        if 'random_forest' in self.models:
            rf_model = self.models['random_forest']
            if hasattr(rf_model, 'feature_importances_'):
                importance = rf_model.feature_importances_
                feature_importance = dict(zip(self.feature_columns, importance))
                # 按重要性排序
                feature_importance = dict(sorted(feature_importance.items(), 
                                                key=lambda x: x[1], reverse=True))
                
                print(f"\n特征重要性 (随机森林):")
                for feature, imp in list(feature_importance.items())[:5]:
                    print(f"  {feature}: {imp:.4f}")
        
        # 保存所有模型
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_info = {
            'best_model': best_model_name,
            'all_models': {},
            'feature_importance': feature_importance,
            'feature_columns': self.feature_columns,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        for name, metrics in results.items():
            model_filename = f"{name}_{timestamp}.pkl"
            model_path = os.path.join(self.model_dir, model_filename)
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'model': self.models[name],
                    'scaler': self.scaler,
                    'feature_columns': self.feature_columns,
                    'metrics': metrics,
                    'timestamp': timestamp
                }, f)
            
            model_info['all_models'][name] = {
                'metrics': {
                    'model_name': name,
                    'mse': round(metrics['test_rmse']**2, 4),
                    'rmse': round(metrics['test_rmse'], 4),
                    'mae': round(metrics['test_mae'], 4),
                    'r2_score': round(metrics['test_r2'], 4),
                    'cv_rmse': round(metrics['cv_rmse'], 4),
                    'cv_scores': [round(s, 4) for s in metrics['cv_scores']]
                },
                'path': model_filename
            }
            
            print(f"✓ 保存 {name}: {model_filename}")
        
        # 保存model_info.json
        info_path = os.path.join(self.model_dir, 'model_info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 模型信息已保存: {info_path}")
        
        return best_model_name
    
    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 80)
        print(" " * 20 + "改进的幸福感预测模型训练")
        print("=" * 80)
        
        # 1. 加载数据
        df = self.load_data()
        
        # 2. 特征工程
        processed_data = self.feature_engineering(df)
        
        # 3. 准备数据
        X_train, X_test, y_train, y_test = self.prepare_data(processed_data)
        
        # 4. 训练模型
        self.train_models(X_train, y_train)
        
        # 5. 评估模型
        results = self.evaluate_models(X_train, X_test, y_train, y_test)
        
        # 6. 保存模型
        best_model = self.save_models(results)
        
        print("\n" + "=" * 80)
        print("✓ 训练完成！")
        print(f"  最佳模型: {best_model}")
        print(f"  测试集 R²: {results[best_model]['test_r2']:.4f}")
        print(f"  测试集 RMSE: {results[best_model]['test_rmse']:.4f}")
        print("=" * 80)


def main():
    try:
        model = SimpleImprovedModel()
        model.run()
    except Exception as e:
        print(f"\n✗ 训练失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

