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
        # 调用底层算法大脑，算出三个分数，存入 res 字典
        res = p.predict(data)

        # ====================================================
        # 👇 答辩终端炫技专属：打印后台运行日志 👇
        print("\n" + "🚀" * 15)
        print(">>> 收到新的前端个体特征数据，开启在线智能预测！")
        print(">>> 正在启动底层混合算法引擎 (Hybrid Engine)...")
        # 从 res 字典中提取出三个分数进行终端打印
        print(f" [模型 1] 岭回归 (Ridge) 并行推演结果 : {res.get('lr', 0):.3f}")
        print(f" [模型 2] 随机森林 (RF) 并行推演结果 : {res.get('rf', 0):.3f}")
        print("-" * 37)
        print(f" [最终决策] 软投票加权融合输出 (Hybrid) : {res.get('hybrid', 0):.3f}")
        print("<<< 预测完成！JSON 结果已通过 RESTful API 返回给 Vue 前端")
        print("🚀" * 15 + "\n")
        # ====================================================

        return jsonify({"code": 200, "data": res, "msg": "预测成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@prediction_bp.route('/model_info', methods=['GET'])
def get_model_info():
    p = get_predictor()
    if p:
        return jsonify({"code": 200, "data": p.get_model_info()})
    return jsonify({"code": 500, "msg": "模型未在线"})