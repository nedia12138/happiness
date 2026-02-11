import time
import logging
from functools import wraps
from flask import session, request, jsonify, g
from utils.response import error

logger = logging.getLogger(__name__)

def hash_password(password):
    """密码不加密，直接返回原密码"""
    return password

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("用户未登录，访问被拒绝")
            return jsonify(error("请先登录", 401))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("用户未登录，访问被拒绝")
            return jsonify(error("请先登录", 401))
        
        user_role = session.get('role')
        if user_role != 'admin':
            logger.warning(f"用户 {session.get('username')} 权限不足，需要管理员权限")
            return jsonify(error("权限不足", 403))
        
        return f(*args, **kwargs)
    return decorated_function

def operation_required(f):
    """操作员权限验证装饰器（操作员及以上权限）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("用户未登录，访问被拒绝")
            return jsonify(error("请先登录", 401))

        user_role = session.get('role')
        if user_role not in ['admin', 'operation']:
            logger.warning(f"用户 {session.get('username')} 权限不足，需要操作员或管理员权限")
            return jsonify(error("权限不足", 403))

        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """教师权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("用户未登录，访问被拒绝")
            return jsonify(error("请先登录", 401))

        user_role = session.get('role')
        if user_role not in ['admin', 'teacher']:
            logger.warning(f"用户 {session.get('username')} 权限不足，需要教师或管理员权限")
            return jsonify(error("权限不足", 403))

        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前登录用户信息"""
    if 'user_id' in session:
        return {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'nickname': session.get('nickname'),
            'role': session.get('role'),
            'avatar': session.get('avatar')
        }
    return None

def set_user_session(user):
    """设置用户会话"""
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['nickname'] = user['nickname']
    session['role'] = user['role']
    session['avatar'] = user['avatar']
    session.permanent = True

def clear_user_session():
    """清除用户会话"""
    session.clear()