"""
数据分析蓝图
"""
from flask import Blueprint, jsonify
from controller.data_analysis_controller import DataAnalysisController
from utils.auth_utils import operation_required

# 创建蓝图
data_analysis_bp = Blueprint('data_analysis', __name__)

# 数据分析接口（需要操作员权限）
@data_analysis_bp.route('/overview', methods=['GET'])
@operation_required
def get_happiness_overview():
    """获取幸福感数据概览"""
    result = DataAnalysisController.get_happiness_overview()
    return jsonify(result)

@data_analysis_bp.route('/marital', methods=['GET'])
@operation_required
def get_marital_analysis():
    """获取婚姻状况分析"""
    result = DataAnalysisController.get_marital_analysis()
    return jsonify(result)

@data_analysis_bp.route('/education', methods=['GET'])
@operation_required
def get_education_analysis():
    """获取教育水平分析"""
    result = DataAnalysisController.get_education_analysis()
    return jsonify(result)

@data_analysis_bp.route('/income', methods=['GET'])
@operation_required
def get_income_analysis():
    """获取收入区间分析"""
    result = DataAnalysisController.get_income_analysis()
    return jsonify(result)

@data_analysis_bp.route('/health', methods=['GET'])
@operation_required
def get_health_analysis():
    """获取健康状况分析"""
    result = DataAnalysisController.get_health_analysis()
    return jsonify(result)

@data_analysis_bp.route('/correlation', methods=['GET'])
@operation_required
def get_correlation_analysis():
    """获取相关性分析"""
    result = DataAnalysisController.get_correlation_analysis()
    return jsonify(result)

@data_analysis_bp.route('/comprehensive', methods=['GET'])
@operation_required
def get_comprehensive_analysis():
    """获取综合分析结论"""
    result = DataAnalysisController.get_comprehensive_analysis()
    return jsonify(result)
@data_analysis_bp.route('/save_chart', methods=['POST'])
def save_chart():
    """接收前端静默保存的图表"""
    # 💡 核心细节：这里咱们故意不加 @operation_required 权限校验，
    # 防止前端纯展示页面因为没登录 token 而被拦截，保证静默截图绝对畅通无阻！
    result = DataAnalysisController.save_chart()
    return jsonify(result)