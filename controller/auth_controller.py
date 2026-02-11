from flask import Blueprint, request, jsonify, session
from service.auth_service import AuthService
from service.log_service import LogService
from utils.response import success, error
from utils.auth_utils import set_user_session, clear_user_session, get_current_user
import logging

logger = logging.getLogger(__name__)

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)

# 初始化认证服务
auth_service = AuthService()


def record_auth_log(user, action, detail, status=1, username=None):
    """记录认证相关操作日志"""
    try:
        LogService.record_log(
            user_id=user['id'] if user and 'id' in user else None,
            username=username or (user.get('username') if user else None),
            action=action,
            module='认证',
            detail=detail,
            status=status,
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            request_method=request.method,
            request_path=request.path
        )
    except Exception as e:
        logger.warning(f"记录认证日志失败: {e}")

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        if not username or not password or not role:
            return jsonify(error("用户名、密码和角色不能为空"))
        
        # 验证用户登录
        user = auth_service.login(username, password, role)
        if user:
            # 设置用户会话
            set_user_session(user)
            
            # 根据角色确定跳转页面
            if user['role'] == 'user':
                redirect_url = '/admin/users.html'
            else:
                redirect_url = '/admin/users.html'
            
            logger.info(f"用户 {username} 登录成功，角色: {user['role']}")
            record_auth_log(user, '登录', '用户登录成功')
            return jsonify(success({
                'user': user,
                'redirect_url': redirect_url
            }, "登录成功"))
        else:
            record_auth_log(None, '登录', '用户名或密码错误', status=0, username=username)
            return jsonify(error("用户名或密码错误"))
            
    except Exception as e:
        logger.error(f"登录异常: {e}")
        record_auth_log(None, '登录', f'登录异常: {e}', status=0, username=username if "username" in locals() else None)
        return jsonify(error("登录失败，请稍后重试"))

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        nickname = data.get('nickname')
        email = data.get('email')
        phone = data.get('phone')
        
        if not username or not password:
            return jsonify(error("用户名和密码不能为空"))
        
        # 注册用户
        result = auth_service.register(username, password, nickname, email, phone)
        if result:
            logger.info(f"用户 {username} 注册成功")
            record_auth_log(None, '注册', '用户注册成功', username=username)
            return jsonify(success(None, "注册成功"))
        else:
            record_auth_log(None, '注册', '注册失败，用户名已存在', status=0, username=username)
            return jsonify(error("注册失败，用户名可能已存在"))
            
    except Exception as e:
        logger.error(f"注册异常: {e}")
        record_auth_log(None, '注册', f'注册异常: {e}', status=0, username=username if "username" in locals() else None)
        return jsonify(error("注册失败，请稍后重试"))

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        # 清除用户会话
        current_user = get_current_user()
        clear_user_session()
        logger.info("用户登出成功")
        record_auth_log(current_user, '登出', '用户登出成功')
        return jsonify(success(None, "登出成功"))
        
    except Exception as e:
        logger.error(f"登出异常: {e}")
        record_auth_log(get_current_user(), '登出', f'登出异常: {e}', status=0)
        return jsonify(error("登出失败"))

@auth_bp.route('/userinfo', methods=['GET'])
def get_user_info():
    """获取当前用户信息"""
    try:
        user = get_current_user()
        if user:
            return jsonify(success(user, "获取用户信息成功"))
        else:
            return jsonify(error("用户未登录", 401))
            
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        return jsonify(error("获取用户信息失败"))

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """检查用户认证状态"""
    try:
        user = get_current_user()
        if user:
            # 根据角色确定可访问的页面
            if user['role'] == 'user':
                available_pages = ['/front/index.html', '/front/about.html', '/front/profile.html']
            else:
                available_pages = ['/admin/index.html', '/admin/users.html', '/admin/profile.html']
            
            return jsonify(success({
                'authenticated': True,
                'user': user,
                'available_pages': available_pages
            }, "用户已认证"))
        else:
            return jsonify(success({
                'authenticated': False,
                'user': None,
                'available_pages': ['/login', '/register']
            }, "用户未认证"))
            
    except Exception as e:
        logger.error(f"检查认证状态异常: {e}")
        return jsonify(error("检查认证状态失败"))
