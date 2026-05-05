from flask import Blueprint, request, jsonify, session
import os
import sys
import pymysql
import datetime

# 自动处理路径，确保能找到 Predictive 文件夹
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Predictive.happiness_predictor import HappinessPredictor

# 👇 引入你项目里已经写好的神器 👇
from service.log_service import LogService
from config.config import DB_CONFIG

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
        # 调用底层算法大脑，res 字典里已经包含了 'lr', 'rf', 'hybrid' 三个分数
        res = p.predict(data)

        # ====================================================
        # 👇 数据库保存逻辑：三路分数同步持久化 👇

        # 1. 记录操作日志 (表 5.4)
        user_id = session.get('user_id')
        username = session.get('username', '匿名受访者')
        try:
            LogService.record_log(
                user_id=user_id,
                username=username,
                action="发起双轨预测推演",
                module="智能预测模块",
                detail=f"混合得分:{res.get('hybrid')}, 岭回归:{res.get('lr')}, 随机森林:{res.get('rf')}",
                status=1,
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_path=request.path
            )
        except Exception as log_e:
            print(f"⚠️ 日志记录失败: {log_e}")

        # 2. 存入预测结果表 (表 5.3) - 增加 ridgeScore 和 rfScore
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 提取算法输出的三个核心分值
            lr_score = res.get('lr', 0)
            rf_score = res.get('rf', 0)
            hybrid_score = res.get('hybrid', 0)

            survey_id = data.get('id', 0)
            # 状态判定：依然以最终混合分为准
            predicted_class = 1 if hybrid_score >= 3.5 else 0
            predict_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 更新后的 SQL 语句，加入了 ridgeScore 和 rfScore 两个新列
            sql = """
                INSERT INTO py_happiness_prediction 
                (surveyId, modelName, modelVersion, ridgeScore, rfScore, predictedHappiness, predictedClass, predictionTime)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                survey_id,
                "Hybrid_Ensemble",
                "v1.0",
                lr_score,  # 岭回归分数
                rf_score,  # 随机森林分数
                hybrid_score,  # 混合最终分数
                predicted_class,
                predict_time
            ))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ 三轨分数({lr_score}/{rf_score}/{hybrid_score})已成功同步入库！")
        except Exception as db_e:
            print(f"❌ 预测结果写入失败，请检查数据库是否已添加 ridgeScore/rfScore 字段: {db_e}")

        # ====================================================

        # 终端炫技打印
        print("\n" + "🚀" * 15)
        print(f" [模型 1] 岭回归 (Ridge) 分数 : {res.get('lr'):.3f}")
        print(f" [模型 2] 随机森林 (RF) 分数    : {res.get('rf'):.3f}")
        print(f" [最终决策] 混合权重融合 (Hybrid) : {res.get('hybrid'):.3f}")
        print("🚀" * 15 + "\n")

        return jsonify({"code": 200, "data": res, "msg": "预测成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})

@prediction_bp.route('/model_info', methods=['GET'])
def get_model_info():
    p = get_predictor()
    if p:
        return jsonify({"code": 200, "data": p.get_model_info()})
    return jsonify({"code": 500, "msg": "模型未在线"})