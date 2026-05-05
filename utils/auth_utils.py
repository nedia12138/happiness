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


def auto_record_log(module_name, action_name):
    """
    优雅的操作日志装饰器（隐形摄像头）
    专门用来挂在路由上，自动记录用户的操作轨迹，绝不污染业务代码
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. 先让你的核心业务代码正常运行，拿到结果
            response = f(*args, **kwargs)

            # 2. 业务跑完后，偷偷记录日志
            try:
                # 局部导入 LogService，防止 Flask 启动时发生循环依赖报错
                from service.log_service import LogService

                # 如果没登录（比如前台填问卷的），就默认叫 '前台受访者'，ID为0
                user_id = session.get('user_id', 0)
                username = session.get('username', '前台受访者')

                LogService.record_log(
                    user_id=user_id,
                    username=username,
                    action=action_name,
                    module=module_name,
                    detail=f"访客/用户触发了 {action_name} 操作",
                    status=1,
                    ip=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_method=request.method,
                    request_path=request.path
                )
            except Exception as e:
                logger.error(f"自动记录操作日志失败: {e}")

            return response

        return decorated_function

    return decorator