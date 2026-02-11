"""
幸福感预测控制器
提供Web API接口进行幸福感预测
"""

import json
from flask import Blueprint, request, jsonify
from Predictive.happiness_predictor import HappinessPredictor
from utils.response import success, error

# 创建蓝图
prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')

# 全局预测器实例
predictor = None

def init_predictor():
    """初始化预测器"""
    global predictor
    try:
        predictor = HappinessPredictor()
        print("幸福感预测服务初始化成功")
    except Exception as e:
        print(f"幸福感预测服务初始化失败: {e}")
        predictor = None

# 在模块加载时初始化预测器
init_predictor()

@prediction_bp.route('/predict', methods=['POST'])
def predict_happiness():
    """幸福感预测接口"""
    try:
        if predictor is None:
            return jsonify(error("预测服务未初始化")), 500

        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify(error("请求数据不能为空")), 400

        # 获取算法选择，默认使用auto（最佳模型）
        algorithm = data.get('algorithm', 'auto')
        prediction_data = data.get('prediction_data', data)

        # 验证必要字段
        required_fields = ['education', 'income', 'health', 'marital_status', 'age', 'gender']
        missing_fields = [field for field in required_fields if field not in prediction_data]

        if missing_fields:
            return jsonify(error(f"缺少必要字段: {', '.join(missing_fields)}")), 400

        # 进行预测
        result = predictor.predict(prediction_data, algorithm)

        return jsonify(success(result))

    except ValueError as e:
        return jsonify(error(str(e))), 400
    except Exception as e:
        print(f"预测接口错误: {e}")
        return jsonify(error("预测服务内部错误")), 500

@prediction_bp.route('/batch_predict', methods=['POST'])
def batch_predict_happiness():
    """批量幸福感预测接口"""
    try:
        if predictor is None:
            return jsonify(error("预测服务未初始化")), 500

        # 获取请求数据
        data = request.get_json()
        if not data or 'predictions' not in data:
            return jsonify(error("请求数据格式错误，需包含'predictions'字段")), 400

        predictions_data = data['predictions']
        if not isinstance(predictions_data, list):
            return jsonify(error("'predictions'字段必须是数组")), 400

        if len(predictions_data) > 100:
            return jsonify(error("批量预测最多支持100个样本")), 400

        # 获取算法选择
        algorithm = data.get('algorithm', 'auto')

        # 进行批量预测
        results = predictor.batch_predict(predictions_data, algorithm)

        return jsonify(success({'results': results, 'total': len(results), 'algorithm': algorithm}))

    except Exception as e:
        print(f"批量预测接口错误: {e}")
        return jsonify(error("批量预测服务内部错误")), 500

@prediction_bp.route('/model_info', methods=['GET'])
def get_model_info():
    """获取模型信息接口"""
    try:
        if predictor is None:
            return jsonify(error("预测服务未初始化")), 500

        model_info = predictor.get_model_info()
        return jsonify(success(model_info))

    except Exception as e:
        print(f"获取模型信息错误: {e}")
        return jsonify(error("获取模型信息失败")), 500

@prediction_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    if predictor is not None:
        return jsonify(success({"status": "healthy", "service": "happiness_prediction"}))
    else:
        return jsonify(error("预测服务未初始化")), 503

@prediction_bp.route('/sample_input', methods=['GET'])
def get_sample_input():
    """获取示例输入数据"""
    from Predictive.happiness_predictor import create_sample_input

    sample = create_sample_input()
    return jsonify(success({
        "sample_input": sample,
        "field_descriptions": {
            "education": "教育水平 (1-12, 1=文盲, 4=高中, 6=本科, 12=大专)",
            "income": "个人年收入 (元)",
            "health": "健康状况 (1-5, 1=非常健康, 5=不健康)",
            "marital_status": "婚姻状况 (1-7, 1=未婚, 3=已婚, 5=离婚)",
            "age": "年龄",
            "gender": "性别 (1=男, 2=女)",
            "family_income": "家庭年收入 (元)",
            "work_status": "工作状态 (1-5)",
            "floor_area": "住房面积 (平方米)"
        }
    }))
