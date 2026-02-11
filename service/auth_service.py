from utils.db_utils import execute_query, execute_insert, execute_update
from utils.auth_utils import hash_password
import time
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务类"""
    
    def login(self, username, password, role):
        """用户登录验证"""
        try:
            # 查询用户信息
            sql = """
                SELECT id, username, password, nickname, avatar, role, status,
                       last_login_time, last_login_ip, createtime, updatetime
                FROM py_user
                WHERE username = %s AND role = %s AND status = 'active'
            """
            users = execute_query(sql, (username, role))
            
            if not users:
                logger.warning(f"用户 {username} 不存在或已被禁用")
                return None
            
            user = users[0]
            
            # 验证密码（这里简化处理，实际项目中应该使用加密）
            if user['password'] != password:
                logger.warning(f"用户 {username} 密码错误")
                return None
            
            # 更新最后登录时间和IP
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            update_sql = """
                UPDATE py_user 
                SET last_login_time = %s, last_login_ip = %s, updatetime = %s
                WHERE id = %s
            """
            execute_update(update_sql, (current_time, '127.0.0.1', current_time, user['id']))
            
            # 返回用户信息（不包含密码）
            user_info = {
                'id': user['id'],
                'username': user['username'],
                'nickname': user['nickname'],
                'avatar': user['avatar'],
                'role': user['role'],
                'status': user['status'],
                'last_login_time': user['last_login_time'],
                'createtime': user['createtime']
            }
            
            logger.info(f"用户 {username} 登录成功")
            return user_info
            
        except Exception as e:
            logger.error(f"用户登录验证异常: {e}")
            return None
    
    def register(self, username, password, nickname=None, email=None, phone=None):
        """用户注册"""
        try:
            # 检查用户名是否已存在
            check_sql = "SELECT id FROM py_user WHERE username = %s"
            existing_users = execute_query(check_sql, (username,))
            
            if existing_users:
                logger.warning(f"用户名 {username} 已存在")
                return False
            
            # 插入新用户
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            insert_sql = """
                INSERT INTO py_user 
                (username, password, nickname, email, phone, role, status, createtime, updatetime)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # 默认角色为普通用户
            role = 'user'
            status = 'active'
            
            execute_insert(insert_sql, (
                username, password, nickname, email, phone, 
                role, status, current_time, current_time
            ))
            
            logger.info(f"用户 {username} 注册成功")
            return True
            
        except Exception as e:
            logger.error(f"用户注册异常: {e}")
            return False
    
    def check_username_exists(self, username):
        """检查用户名是否存在"""
        try:
            sql = "SELECT id FROM py_user WHERE username = %s"
            users = execute_query(sql, (username,))
            return len(users) > 0
            
        except Exception as e:
            logger.error(f"检查用户名存在性异常: {e}")
            return False
    
    def get_user_by_username(self, username):
        """根据用户名获取用户信息"""
        try:
            sql = """
                SELECT id, username, nickname, avatar, role, status, 
                       last_login_time, createtime, updatetime
                FROM py_user 
                WHERE username = %s
            """
            users = execute_query(sql, (username,))
            
            if users:
                return users[0]
            return None
            
        except Exception as e:
            logger.error(f"根据用户名获取用户信息异常: {e}")
            return None
