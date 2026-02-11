"""
幸福感预测服务
提供基于训练好的模型进行幸福感预测的服务接口
"""

import json
import pickle
import numpy as np
import os
from datetime import datetime

class HappinessPredictor:
    """幸福感预测服务类"""

    def __init__(self, model_info_path=None):
        self.models = {}  # 存储所有模型
        self.scaler = None
        self.feature_columns = None
        self.model_info = None

        # 如果未指定路径，使用相对于当前文件的路径
        if model_info_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_info_path = os.path.join(current_dir, 'models', 'model_info.json')

        # 加载模型信息
        self.load_model_info(model_info_path)

    def load_model_info(self, model_info_path):
        """加载模型信息"""
        try:
            # 检查model_info.json是否存在
            if not os.path.exists(model_info_path):
                raise FileNotFoundError(f"模型信息文件不存在: {model_info_path}")

            print(f"正在加载模型信息: {model_info_path}")
            
            with open(model_info_path, 'r', encoding='utf-8') as f:
                self.model_info = json.load(f)

            # 获取模型文件所在目录
            model_dir = os.path.dirname(model_info_path)

            # 加载所有模型
            all_models_info = self.model_info.get('all_models', {})
            for model_name, model_info in all_models_info.items():
                model_path = model_info.get('path', '')
                
                # 如果是相对路径，转换为绝对路径
                if model_path and not os.path.isabs(model_path):
                    # 尝试相对于model_info.json所在目录
                    abs_model_path = os.path.join(model_dir, os.path.basename(model_path))
                    if os.path.exists(abs_model_path):
                        model_path = abs_model_path
                    else:
                        # 尝试相对于项目根目录
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        abs_model_path = os.path.join(project_root, model_path)
                        if os.path.exists(abs_model_path):
                            model_path = abs_model_path
                
                if model_path and os.path.exists(model_path):
                    print(f"正在加载模型: {model_name} from {model_path}")
                    try:
                        with open(model_path, 'rb') as f:
                            model_data = pickle.load(f)
                            self.models[model_name] = {
                                'model': model_data['model'],
                                'scaler': model_data['scaler'],
                                'metrics': model_info.get('metrics', {})
                            }
                            # 使用第一个模型的scaler和feature_columns
                            if self.scaler is None:
                                self.scaler = model_data['scaler']
                                self.feature_columns = model_data['feature_columns']
                    except (ModuleNotFoundError, AttributeError) as e:
                        print(f"警告: 模型 {model_name} 加载失败（版本不兼容）: {e}")
                        print(f"  跳过此模型，继续加载其他模型...")
                        continue
                else:
                    print(f"警告: 模型文件不存在: {model_path}")

            if not self.models:
                raise ValueError("没有找到可用的模型")

            print(f"成功加载模型: {list(self.models.keys())}")
            
            # 如果最佳模型不可用，选择第一个可用的模型
            best_model = self.model_info['best_model']
            if best_model not in self.models:
                best_model = list(self.models.keys())[0]
                print(f"警告: 原最佳模型 {self.model_info['best_model']} 不可用")
                print(f"使用备选模型: {best_model}")
                self.model_info['best_model'] = best_model
            else:
                print(f"最佳模型: {best_model}")
            
            print(f"特征列表: {self.feature_columns}")

        except Exception as e:
            print(f"加载模型失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def preprocess_input(self, input_data):
        """预处理输入数据"""
        try:
            # 创建特征字典
            features = {}

            # 映射输入字段到模型特征
            field_mapping = {
                'education': 'edu',
                'income': 'income',
                'health': 'health',
                'marital_status': 'marital',
                'age': 'age',
                'gender': 'gender',
                'family_income': 'familyIncome',
                'work_status': 'workStatus',
                'floor_area': 'floorArea'
            }

            # 提取特征值
            for input_field, model_field in field_mapping.items():
                if input_field in input_data:
                    value = input_data[input_field]
                    # 转换为数值类型
                    if value is not None:
                        features[model_field] = float(value)
                    else:
                        features[model_field] = 0.0  # 缺失值用0填充
                else:
                    features[model_field] = 0.0  # 缺失字段用0填充

            # 确保所有特征都存在
            for col in self.feature_columns:
                if col not in features:
                    features[col] = 0.0

            # 转换为DataFrame并标准化（确保列顺序与训练时一致）
            import pandas as pd

            # 创建DataFrame时直接指定列名和顺序
            features_df = pd.DataFrame([features], columns=self.feature_columns)

            # 使用训练时的scaler进行标准化
            features_scaled = self.scaler.transform(features_df)

            return features_scaled

        except Exception as e:
            raise ValueError(f"输入数据预处理失败: {e}")

    def predict(self, input_data, algorithm='auto'):
        """进行幸福感预测"""
        try:
            # 选择算法
            if algorithm == 'auto':
                model_name = self.model_info['best_model']
            elif algorithm in self.models:
                model_name = algorithm
            else:
                raise ValueError(f"不支持的算法: {algorithm}")

            model_info = self.models[model_name]
            model = model_info['model']

            # 预处理输入数据
            features_scaled = self.preprocess_input(input_data)

            # 进行预测
            try:
                prediction = model.predict(features_scaled)[0]
            except AttributeError as e:
                if 'monotonic_cst' in str(e):
                    # 如果遇到monotonic_cst错误，使用线性回归作为备选
                    print(f"模型 {model_name} 出现兼容性问题，使用线性回归作为备选")
                    if 'linear_regression' in self.models:
                        alt_model = self.models['linear_regression']['model']
                        prediction = alt_model.predict(features_scaled)[0]
                        model_name = 'linear_regression_fallback'
                    else:
                        raise ValueError(f"模型 {model_name} 出现兼容性问题，且无备选模型")
                else:
                    raise

            # 计算预测置信度
            # 对于回归问题，使用模型的R²分数作为模型整体的置信度指标
            # R² > 0 表示模型比简单平均值预测更好
            confidence = float(model_info['metrics'].get('r2_score', 0))

            # 确保预测值在合理范围内
            prediction = max(1, min(5, round(prediction)))

            result = {
                'prediction': int(prediction),
                'confidence': round(confidence, 4),
                'model_name': model_name,
                'algorithm': algorithm,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'features_used': self.feature_columns.copy()
            }

            return result

        except Exception as e:
            raise ValueError(f"预测失败: {e}")

    def get_model_info(self):
        """获取模型信息"""
        all_metrics = {}
        for model_name, model_info in self.models.items():
            all_metrics[model_name] = model_info['metrics']

        return {
            'best_model': self.model_info['best_model'],
            'all_models': list(self.models.keys()),
            'all_metrics': all_metrics,
            'feature_importance': self.model_info.get('feature_importance', {}),
            'feature_columns': self.feature_columns,
            'timestamp': self.model_info['timestamp']
        }

    def batch_predict(self, input_data_list, algorithm='auto'):
        """批量预测"""
        results = []
        for input_data in input_data_list:
            try:
                result = self.predict(input_data, algorithm)
                results.append(result)
            except Exception as e:
                results.append({
                    'error': str(e),
                    'input_data': input_data
                })

        return results


def create_sample_input():
    """创建示例输入数据"""
    return {
        'education': 4,      # 教育水平 (1-12)
        'income': 50000,     # 个人收入 (元)
        'health': 4,         # 健康状况 (1-5)
        'marital_status': 3, # 婚姻状况 (1-7)
        'age': 35,           # 年龄
        'gender': 1,         # 性别 (1男2女)
        'family_income': 80000,  # 家庭收入 (元)
        'work_status': 1,    # 工作状态
        'floor_area': 100    # 住房面积 (平方米)
    }


if __name__ == "__main__":
    # 测试预测服务
    try:
        predictor = HappinessPredictor()

        # 获取模型信息
        model_info = predictor.get_model_info()
        print("模型信息:")
        print(json.dumps(model_info, indent=2, ensure_ascii=False))

        # 单次预测测试
        sample_input = create_sample_input()
        print(f"\n预测输入: {sample_input}")

        result = predictor.predict(sample_input)
        print(f"预测结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 批量预测测试
        batch_inputs = [
            create_sample_input(),
            {**create_sample_input(), 'age': 25, 'income': 30000},
            {**create_sample_input(), 'age': 50, 'health': 2}
        ]

        print(f"\n批量预测 ({len(batch_inputs)} 个样本):")
        batch_results = predictor.batch_predict(batch_inputs)
        for i, result in enumerate(batch_results):
            print(f"样本 {i+1}: {result}")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
