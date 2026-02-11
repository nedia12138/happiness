from flask import Blueprint, request, jsonify
import os
import sys

# 自动处理路径，确保能找到 Predictive 文件夹
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Predictive.happiness_predictor import HappinessPredictor

# 创建蓝图
prediction_bp = Blueprint('prediction', __name__)
predictor = None


def get_predictor():
    """获取或初始化预测器实例"""
    global predictor
    if predictor is None:
        try:
            predictor = HappinessPredictor()
        except Exception as e:
            print(f"❌ 预测器实例创建失败: {e}")
            return None
    return predictor


@prediction_bp.route('/predict', methods=['POST'])
def predict():
    p = get_predictor()
    if not p:
        return jsonify({"code": 500, "msg": "模型加载失败"})

    try:
        data = request.json
        res = p.predict(data)
        return jsonify({"code": 200, "data": res, "msg": "预测成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@prediction_bp.route('/model_info', methods=['GET'])
def get_model_info():
    p = get_predictor()
    if p:
        return jsonify({"code": 200, "data": p.get_model_info()})
    return jsonify({"code": 500, "msg": "模型未在线"})