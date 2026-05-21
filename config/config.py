import os
import pymysql

# 应用配置
DEBUG = True
SECRET_KEY = 'your-secret-key-here'
VALID_TIMESTAMP = 1772294400

def _get_int_env(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default

# --- 数据库配置（已更新密码并增强兼容性） ---
_BASE_DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': _get_int_env('MYSQL_PORT', 3306),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '12121212'), # <--- 密码已更新
    'database': os.getenv('MYSQL_DATABASE', 'happiness_db'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor

}

def get_db_connection():
    """
    适配器函数：自动解决 PyMySQL 在 Python 3.12 环境下的参数名冲突
    """
    auth_method = 'mysql_native_password'
    try:
        # 尝试新版参数名
        return pymysql.connect(**_BASE_DB_CONFIG, plugin_auth=auth_method)
    except TypeError:
        try:
            # 尝试旧版参数名
            return pymysql.connect(**_BASE_DB_CONFIG, auth_plugin=auth_method)
        except TypeError:
            # 自动协商模式
            return pymysql.connect(**_BASE_DB_CONFIG)

# 保持对现有代码的兼容
DB_CONFIG = _BASE_DB_CONFIG.copy()

# 上传文件配置
UPLOAD_FOLDER = 'upload'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024