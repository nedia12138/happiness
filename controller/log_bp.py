"""
操作日志蓝图
"""
from flask import Blueprint, jsonify
from controller.log_controller import LogController
from utils.auth_utils import operation_required

# 创建蓝图
log_bp = Blueprint('log', __name__)


@log_bp.route('/admin/list', methods=['GET'])
@operation_required
def admin_log_list():
    """后台获取操作日志列表"""
    result = LogController.get_log_list()
    return jsonify(result)

