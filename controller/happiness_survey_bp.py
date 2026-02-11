"""
幸福感调查表蓝图
"""
from flask import Blueprint, jsonify
from controller.happiness_survey_controller import HappinessSurveyController
from utils.auth_utils import operation_required

# 创建蓝图
happiness_survey_bp = Blueprint('happiness_survey', __name__)

# 后台管理接口（需要登录）
@happiness_survey_bp.route('/admin/list', methods=['GET'])
@operation_required
def admin_happiness_survey_list():
    """后台获取幸福感调查表列表"""
    result = HappinessSurveyController.get_happiness_survey_list()
    return jsonify(result)

@happiness_survey_bp.route('/admin/detail', methods=['GET'])
@operation_required
def admin_happiness_survey_detail():
    """后台获取幸福感调查表详情"""
    result = HappinessSurveyController.get_happiness_survey_detail()
    return jsonify(result)

@happiness_survey_bp.route('/admin/statistics', methods=['GET'])
@operation_required
def admin_happiness_statistics():
    """后台获取幸福感统计数据"""
    result = HappinessSurveyController.get_happiness_statistics()
    return jsonify(result)
