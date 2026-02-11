"""
改进的幸福感预测模型训练
解决R²为负值的问题，包含完整的数据分析和特征工程
"""

import pandas as pd
import numpy as np
import pymysql
import json
import pickle
import os
from datetime import datetime
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import boxcox

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

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

class ImprovedHappinessModel:
    """改进的幸福感预测模型"""
    
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
        self.analysis_dir = os.path.join(current_dir, 'analysis')
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        if not os.path.exists(self.analysis_dir):
            os.makedirs(self.analysis_dir)
    
    def get_db_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**DB_CONFIG)
    
    def load_data_from_db(self):
        """从数据库加载数据"""
        print("=" * 60)
        print("步骤 1: 加载数据")
        print("=" * 60)
        
        conn = self.get_db_connection()
        try:
            query = f"""
                SELECT 
                    edu, income, health, marital, 
                    (2015 - birth) as age, 
                    gender, familyIncome, workStatus, floorArea,
                    {self.target_column}, id
                FROM py_happiness_survey
                WHERE happiness IS NOT NULL
                AND happiness > 0
                AND happiness <= 5
                AND dataSource = 'train'
            """
            
            print(f"执行SQL: {query}")
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            df = pd.DataFrame(rows, columns=columns)
            print(f"✓ 成功加载 {len(df)} 条记录")
            print(f"✓ 特征数量: {len(self.feature_columns)}")
            
            return df
            
        except Exception as e:
            print(f"✗ 数据加载失败: {e}")
            return None
        finally:
            conn.close()
    
    def analyze_target_variable(self, df):
        """分析目标变量"""
        print("\n" + "=" * 60)
        print("步骤 2: 目标变量分析")
        print("=" * 60)
        
        y = df[self.target_column]
        
        print(f"\n基本统计:")
        print(f"  样本数: {len(y)}")
        print(f"  均值: {y.mean():.4f}")
        print(f"  中位数: {y.median():.4f}")
        print(f"  标准差: {y.std():.4f}")
        print(f"  方差: {y.var():.4f}")
        print(f"  最小值: {y.min()}")
        print(f"  最大值: {y.max()}")
        
        print(f"\n分布情况:")
        value_counts = y.value_counts().sort_index()
        for val, count in value_counts.items():
            pct = count / len(y) * 100
            print(f"  幸福感={val}: {count} ({pct:.1f}%)")
        
        # 检查方差
        if y.var() < 0.1:
            print(f"\n⚠️  警告: 目标变量方差过小 ({y.var():.4f})，模型难以学习")
        
        # 保存分布图
        try:
            plt.figure(figsize=(12, 4))
            
            plt.subplot(1, 3, 1)
            y.hist(bins=5, edgecolor='black')
            plt.xlabel('Happiness')
            plt.ylabel('Frequency')
            plt.title('Happiness Distribution')
            
            plt.subplot(1, 3, 2)
            y.value_counts().sort_index().plot(kind='bar')
            plt.xlabel('Happiness Level')
            plt.ylabel('Count')
            plt.title('Happiness Count by Level')
            
            plt.subplot(1, 3, 3)
            plt.boxplot(y)
            plt.ylabel('Happiness')
            plt.title('Happiness Boxplot')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.analysis_dir, 'target_distribution.png'))
            print(f"\n✓ 分布图已保存到: {self.analysis_dir}/target_distribution.png")
            plt.close()
        except Exception as e:
            print(f"⚠️  无法生成图表: {e}")
        
        return y
    
    def check_multicollinearity(self, df):
        """检查多重共线性"""
        print("\n" + "=" * 60)
        print("步骤 3: 多重共线性检查")
        print("=" * 60)
        
        X = df[self.feature_columns].copy()
        
        # 处理缺失值
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
        
        # 计算相关系数矩阵
        print("\n相关系数矩阵 (绝对值 > 0.7 需要注意):")
        corr_matrix = X.corr()
        
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > 0.7:
                    high_corr_pairs.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_matrix.iloc[i, j]
                    ))
                    print(f"  {corr_matrix.columns[i]} <-> {corr_matrix.columns[j]}: {corr_matrix.iloc[i, j]:.4f}")
        
        if not high_corr_pairs:
            print("  ✓ 未发现高度相关的特征对")
        else:
            print(f"\n⚠️  发现 {len(high_corr_pairs)} 对高度相关的特征，建议考虑特征选择")
        
        # 计算VIF
        print("\nVIF (方差膨胀因子，> 10 表示严重共线性):")
        try:
            vif_data = pd.DataFrame()
            vif_data["Feature"] = X.columns
            vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
            vif_data = vif_data.sort_values('VIF', ascending=False)
            
            for _, row in vif_data.iterrows():
                status = "⚠️" if row['VIF'] > 10 else "✓"
                print(f"  {status} {row['Feature']}: {row['VIF']:.2f}")
            
            # 保存VIF结果
            vif_data.to_csv(os.path.join(self.analysis_dir, 'vif_analysis.csv'), index=False)
            
        except Exception as e:
            print(f"  ⚠️  VIF计算失败: {e}")
        
        # 保存相关系数热力图
        try:
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0)
            plt.title('Feature Correlation Matrix')
            plt.tight_layout()
            plt.savefig(os.path.join(self.analysis_dir, 'correlation_matrix.png'))
            print(f"\n✓ 相关系数热力图已保存")
            plt.close()
        except Exception as e:
            print(f"⚠️  无法生成热力图: {e}")
        
        return high_corr_pairs
    
    def feature_engineering(self, df, high_corr_pairs):
        """特征工程优化"""
        print("\n" + "=" * 60)
        print("步骤 4: 特征工程")
        print("=" * 60)
        
        data = df.copy()
        
        # 处理缺失值
        print("\n处理缺失值...")
        for col in self.feature_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
                if data[col].isnull().sum() > 0:
                    if col in ['income', 'familyIncome', 'floorArea', 'age']:
                        fill_val = data[col].median()
                    else:
                        fill_val = data[col].mode()[0] if len(data[col].mode()) > 0 else 0
                    data[col] = data[col].fillna(fill_val)
                    print(f"  {col}: 填充 {data[col].isnull().sum()} 个缺失值")
        
        # 处理高度相关的特征
        if high_corr_pairs:
            print("\n处理多重共线性...")
            # 如果 income 和 familyIncome 高度相关，创建组合特征
            if any('income' in str(pair[0]).lower() and 'income' in str(pair[1]).lower() 
                   for pair in high_corr_pairs):
                print("  创建收入比例特征: incomeRatio = income / (familyIncome + 1)")
                data['incomeRatio'] = data['income'] / (data['familyIncome'] + 1)
                self.feature_columns.append('incomeRatio')
        
        # 创建交互特征
        print("\n创建交互特征...")
        data['edu_income'] = data['edu'] * np.log1p(data['income'])
        data['health_age'] = data['health'] * data['age']
        
        interaction_features = ['edu_income', 'health_age']
        self.feature_columns.extend(interaction_features)
        print(f"  添加交互特征: {interaction_features}")
        
        # 删除目标变量缺失的记录
        data = data.dropna(subset=[self.target_column])
        
        print(f"\n✓ 特征工程完成")
        print(f"  最终特征数: {len(self.feature_columns)}")
        print(f"  最终样本数: {len(data)}")
        
        return data
    
    def prepare_data(self, data):
        """准备训练数据"""
        print("\n" + "=" * 60)
        print("步骤 5: 数据准备")
        print("=" * 60)
        
        X = data[self.feature_columns].copy()
        y = data[self.target_column].copy()
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=self.feature_columns, index=X.index)
        
        # 分层抽样划分数据集
        print("\n使用分层抽样划分数据集...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, 
            test_size=0.2, 
            random_state=42,
            stratify=y  # 按目标变量分层
        )
        
        print(f"  训练集: {len(X_train)} 样本")
        print(f"  测试集: {len(X_test)} 样本")
        
        print("\n训练集目标变量分布:")
        for val, count in y_train.value_counts().sort_index().items():
            print(f"  幸福感={val}: {count} ({count/len(y_train)*100:.1f}%)")
        
        print("\n测试集目标变量分布:")
        for val, count in y_test.value_counts().sort_index().items():
            print(f"  幸福感={val}: {count} ({count/len(y_test)*100:.1f}%)")
        
        return X_train, X_test, y_train, y_test
    
    def train_models(self, X_train, y_train):
        """训练多个模型"""
        print("\n" + "=" * 60)
        print("步骤 6: 模型训练")
        print("=" * 60)
        
        models_to_train = {
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0, random_state=42),
            'lasso': Lasso(alpha=0.1, random_state=42),
            'random_forest': RandomForestRegressor(
                n_estimators=100, 
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        for name, model in models_to_train.items():
            print(f"\n训练 {name}...")
            model.fit(X_train, y_train)
            self.models[name] = model
            print(f"  ✓ {name} 训练完成")
        
        return self.models
    
    def evaluate_models(self, X_train, X_test, y_train, y_test):
        """评估所有模型"""
        print("\n" + "=" * 60)
        print("步骤 7: 模型评估")
        print("=" * 60)
        
        results = {}
        
        # 计算基线（使用均值预测）
        baseline_pred = np.full(len(y_test), y_train.mean())
        baseline_r2 = r2_score(y_test, baseline_pred)
        baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
        
        print(f"\n基线模型 (预测均值 {y_train.mean():.2f}):")
        print(f"  R² Score: {baseline_r2:.4f}")
        print(f"  RMSE: {baseline_rmse:.4f}")
        print("-" * 60)
        
        for name, model in self.models.items():
            print(f"\n{name}:")
            
            # 训练集评估
            y_train_pred = model.predict(X_train)
            train_r2 = r2_score(y_train, y_train_pred)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            
            # 测试集评估
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
            
            print(f"  训练集 R²: {train_r2:.4f}")
            print(f"  训练集 RMSE: {train_rmse:.4f}")
            print(f"  测试集 R²: {test_r2:.4f}")
            print(f"  测试集 RMSE: {test_rmse:.4f}")
            print(f"  测试集 MAE: {test_mae:.4f}")
            print(f"  交叉验证 RMSE: {cv_rmse:.4f}")
            
            # 判断过拟合
            if train_r2 - test_r2 > 0.1:
                print(f"  ⚠️  可能存在过拟合 (训练R²-测试R² = {train_r2-test_r2:.4f})")
            
            # 判断是否优于基线
            if test_r2 > baseline_r2:
                print(f"  ✓ 优于基线模型 (提升 {test_r2-baseline_r2:.4f})")
            else:
                print(f"  ✗ 未优于基线模型 (差距 {test_r2-baseline_r2:.4f})")
        
        return results
    
    def save_best_model(self, results):
        """保存最佳模型"""
        print("\n" + "=" * 60)
        print("步骤 8: 保存模型")
        print("=" * 60)
        
        # 选择测试集R²最高的模型
        best_model_name = max(results.keys(), key=lambda x: results[x]['test_r2'])
        best_model = self.models[best_model_name]
        
        print(f"\n最佳模型: {best_model_name}")
        print(f"  测试集 R²: {results[best_model_name]['test_r2']:.4f}")
        print(f"  测试集 RMSE: {results[best_model_name]['test_rmse']:.4f}")
        
        # 保存模型
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_filename = f"{best_model_name}_{timestamp}.pkl"
        model_path = os.path.join(self.model_dir, model_filename)
        
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': best_model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'metrics': results[best_model_name],
                'timestamp': timestamp
            }, f)
        
        print(f"\n✓ 模型已保存: {model_path}")
        
        # 保存所有模型信息
        model_info = {
            'best_model': best_model_name,
            'all_models': {},
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
        
        # 保存model_info.json
        info_path = os.path.join(self.model_dir, 'model_info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 模型信息已保存: {info_path}")
        
        return best_model_name, model_path
    
    def run_pipeline(self):
        """运行完整流水线"""
        print("\n" + "=" * 80)
        print(" " * 20 + "改进的幸福感预测模型训练")
        print("=" * 80)
        
        # 1. 加载数据
        df = self.load_data_from_db()
        if df is None or len(df) == 0:
            print("✗ 数据加载失败")
            return
        
        # 2. 分析目标变量
        self.analyze_target_variable(df)
        
        # 3. 检查多重共线性
        high_corr_pairs = self.check_multicollinearity(df)
        
        # 4. 特征工程
        processed_data = self.feature_engineering(df, high_corr_pairs)
        
        # 5. 准备数据
        X_train, X_test, y_train, y_test = self.prepare_data(processed_data)
        
        # 6. 训练模型
        self.train_models(X_train, y_train)
        
        # 7. 评估模型
        results = self.evaluate_models(X_train, X_test, y_train, y_test)
        
        # 8. 保存最佳模型
        best_model_name, model_path = self.save_best_model(results)
        
        print("\n" + "=" * 80)
        print("✓ 训练流水线完成！")
        print(f"  最佳模型: {best_model_name}")
        print(f"  模型路径: {model_path}")
        print(f"  分析结果: {self.analysis_dir}")
        print("=" * 80)


def main():
    """主函数"""
    try:
        model = ImprovedHappinessModel()
        model.run_pipeline()
    except Exception as e:
        print(f"\n✗ 训练失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

