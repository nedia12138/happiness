from flask import Blueprint, request, jsonify
from service.user_service import UserService
from service.log_service import LogService
from utils.response import success, error, page_response, convert_pagination_params
from utils.auth_utils import get_current_user, admin_required
import logging

logger = logging.getLogger(__name__)

# 创建用户蓝图
user_bp = Blueprint('user', __name__)

# 初始化用户服务
user_service = UserService()


def record_user_log(user, action, detail, status=1):
    """记录用户管理相关操作日志"""
    try:
        LogService.record_log(
            user_id=user.get('id') if user else None,
            username=user.get('username') if user else None,
            action=action,
            module='用户管理',
            detail=detail,
            status=status,
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            request_method=request.method,
            request_path=request.path
        )
    except Exception as e:
        logger.warning(f"记录用户管理日志失败: {e}")

@user_bp.route('/list', methods=['GET'])
@admin_required
def get_user_list():
    """获取用户列表（管理员权限）"""
    try:
        # 获取分页参数
        page, limit = convert_pagination_params(request.args)
        
        # 获取搜索参数
        keyword = request.args.get('keyword', '')
        role = request.args.get('role', '')
        status = request.args.get('status', '')
        
        # 获取用户列表
        users, total = user_service.get_user_list(page, limit, keyword, role, status)
        
        logger.info(f"获取用户列表成功，共 {total} 条记录")
        return jsonify(page_response(users, total, page, limit))
        
    except Exception as e:
        logger.error(f"获取用户列表异常: {e}")
        return jsonify(error("获取用户列表失败"))

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user_detail(user_id):
    """获取用户详情"""
    try:
        current_user = get_current_user()
        
        # 普通用户只能查看自己的信息，管理员可以查看所有用户
        if current_user['role'] != 'admin' and current_user['id'] != user_id:
            return jsonify(error("无权限访问", 403))
        
        user = user_service.get_user_by_id(user_id)
        if user:
            return jsonify(success(user, "获取用户信息成功"))
        else:
            return jsonify(error("用户不存在"))
            
    except Exception as e:
        logger.error(f"获取用户详情异常: {e}")
        return jsonify(error("获取用户信息失败"))

@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        # 普通用户只能更新自己的信息，管理员可以更新所有用户
        if current_user['role'] != 'admin' and current_user['id'] != user_id:
            return jsonify(error("无权限修改", 403))
        
        # 移除敏感字段（普通用户不能修改）
        if current_user['role'] != 'admin':
            data.pop('role', None)
            data.pop('status', None)
        
        result = user_service.update_user(user_id, data)
        if result:
            logger.info(f"用户 {user_id} 信息更新成功")
            record_user_log(current_user, '更新用户', f"更新用户ID: {user_id}")
            return jsonify(success(None, "更新成功"))
        else:
            record_user_log(current_user, '更新用户', f"更新用户ID: {user_id} 失败", status=0)
            return jsonify(error("更新失败"))
            
    except Exception as e:
        logger.error(f"更新用户信息异常: {e}")
        record_user_log(get_current_user(), '更新用户', f"异常: {e}", status=0)
        return jsonify(error("更新失败"))

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户（管理员权限）"""
    try:
        current_user = get_current_user()
        
        # 不能删除自己
        if current_user['id'] == user_id:
            return jsonify(error("不能删除自己的账号"))
        
        result = user_service.delete_user(user_id)
        if result:
            logger.info(f"用户 {user_id} 删除成功")
            record_user_log(current_user, '删除用户', f"删除用户ID: {user_id}")
            return jsonify(success(None, "删除成功"))
        else:
            record_user_log(current_user, '删除用户', f"删除用户ID: {user_id} 失败", status=0)
            return jsonify(error("删除失败"))
            
    except Exception as e:
        logger.error(f"删除用户异常: {e}")
        record_user_log(get_current_user(), '删除用户', f"异常: {e}", status=0)
        return jsonify(error("删除失败"))

@user_bp.route('/change-password', methods=['POST'])
def change_password():
    """修改密码"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        old_password = data.get('oldPassword') or data.get('old_password')
        new_password = data.get('newPassword') or data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify(error("原密码和新密码不能为空"))
        
        result = user_service.change_password(current_user['id'], old_password, new_password)
        if result:
            logger.info(f"用户 {current_user['username']} 修改密码成功")
            record_user_log(current_user, '修改密码', '密码修改成功')
            return jsonify(success(None, "密码修改成功"))
        else:
            record_user_log(current_user, '修改密码', '原密码错误', status=0)
            return jsonify(error("原密码错误"))
            
    except Exception as e:
        logger.error(f"修改密码异常: {e}")
        record_user_log(get_current_user(), '修改密码', f"异常: {e}", status=0)
        return jsonify(error("修改密码失败"))

@user_bp.route('/admin/change-user-password', methods=['POST'])
@admin_required
def admin_change_user_password():
    """管理员修改用户密码（不需要验证旧密码）"""
    try:
        current_user = get_current_user()
        data = request.get_json()

        user_id = data.get('userId') or data.get('user_id')
        new_password = data.get('newPassword') or data.get('new_password')

        if not user_id or not new_password:
            return jsonify(error("用户ID和新密码不能为空"))

        result = user_service.admin_change_user_password(user_id, new_password)
        if result:
            logger.info(f"管理员 {current_user['username']} 修改用户 {user_id} 密码成功")
            record_user_log(current_user, '修改用户密码', f"修改用户ID:{user_id}的密码")
            return jsonify(success(None, "密码修改成功"))
        else:
            record_user_log(current_user, '修改用户密码', f"修改用户ID:{user_id}的密码失败", status=0)
            return jsonify(error("密码修改失败"))

    except Exception as e:
        logger.error(f"管理员修改用户密码异常: {e}")
        record_user_log(get_current_user(), '修改用户密码', f"异常: {e}", status=0)
        return jsonify(error("修改密码失败"))

@user_bp.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    """上传头像"""
    try:
        current_user = get_current_user()
        
        if 'file' not in request.files:
            return jsonify(error("没有选择文件"))
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(error("没有选择文件"))
        
        # 上传文件并更新用户头像
        avatar_url = user_service.upload_avatar(current_user['id'], file)
        if avatar_url:
            logger.info(f"用户 {current_user['username']} 上传头像成功")
            record_user_log(current_user, '上传头像', '上传头像成功')
            return jsonify(success({'avatar_url': avatar_url}, "头像上传成功"))
        else:
            record_user_log(current_user, '上传头像', '上传头像失败', status=0)
            return jsonify(error("头像上传失败"))
            
    except Exception as e:
        logger.error(f"上传头像异常: {e}")
        record_user_log(get_current_user(), '上传头像', f"异常: {e}", status=0)
        return jsonify(error("头像上传失败"))

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """获取当前用户个人信息"""
    try:
        current_user = get_current_user()
        if current_user:
            user_detail = user_service.get_user_by_id(current_user['id'])
            return jsonify(success(user_detail, "获取个人信息成功"))
        else:
            return jsonify(error("用户未登录", 401))
            
    except Exception as e:
        logger.error(f"获取个人信息异常: {e}")
        return jsonify(error("获取个人信息失败"))

@user_bp.route('/add', methods=['POST'])
@admin_required
def add_user():
    """添加用户（管理员权限）"""
    try:
        current_user = get_current_user()
        data = request.get_json()


        # 验证必填字段
        required_fields = ['username', 'password', 'nickname']
        for field in required_fields:
            if not data.get(field):
                return jsonify(error(f"{field}不能为空"))
        
        # 添加用户
        result = user_service.add_user(data)
        if result:
            logger.info(f"管理员添加用户 {data['username']} 成功")
            record_user_log(current_user, '新增用户', f"新增用户: {data['username']}")
            return jsonify(success(None, "添加用户成功"))
        else:
            record_user_log(current_user, '新增用户', f"新增用户 {data.get('username')} 失败", status=0)
            return jsonify(error("添加用户失败，用户名可能已存在"))
            
    except Exception as e:
        logger.error(f"添加用户异常: {e}")
        record_user_log(get_current_user(), '新增用户', f"异常: {e}", status=0)
        return jsonify(error("添加用户失败"))
