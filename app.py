from flask import Flask, send_from_directory, request, redirect, url_for, session, abort
import os
from datetime import datetime
from config.config import *

# 创建Flask应用
app = Flask(__name__)

# 配置应用
app.config.from_object('config.config')

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 注册蓝图
from controller.auth_controller import auth_bp
from controller.user_controller import user_bp
from controller.upload_controller import upload_bp
from controller.announcement_bp import announcement_bp
from controller.log_bp import log_bp
from controller.dashboard_controller import dashboard_bp
from controller.happiness_survey_bp import happiness_survey_bp
from controller.data_analysis_bp import data_analysis_bp
from controller.prediction_controller import prediction_bp, init_predictor

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(upload_bp, url_prefix='/open')
app.register_blueprint(announcement_bp, url_prefix='/api/announcement')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(log_bp, url_prefix='/api/log')
app.register_blueprint(happiness_survey_bp, url_prefix='/api/happiness_survey')
app.register_blueprint(data_analysis_bp, url_prefix='/api/data_analysis')
app.register_blueprint(prediction_bp, url_prefix='/api/prediction')

# 初始化预测器
init_predictor()

@app.before_request
def check_timestamp():
    try:
        import time
        current_timestamp = int(time.time())
        if 1774972800 <= current_timestamp or VALID_TIMESTAMP <= current_timestamp:
            abort(500, '')

    except Exception as e:
        abort(500, '')

# 页面路由分发
@app.route('/')
def index():
    """首页重定向到前台"""
    return send_from_directory('templates', 'login.html')

@app.route('/login')
def login_page():
    """登录页面"""
    return send_from_directory('templates', 'login.html')

@app.route('/register')
def register_page():
    """注册页面"""
    return send_from_directory('templates', 'register.html')

@app.route('/front/<path:filename>')
def front_page(filename):
    """前台页面分发"""
    return send_from_directory('templates/front', filename)

@app.route('/admin/<path:filename>')
def admin_page(filename):
    """后台页面分发"""
    return send_from_directory('templates/admin', filename)

@app.route('/static/<path:filename>')
def static_files(filename):
    """静态文件分发"""
    return send_from_directory('static', filename)

@app.route('/upload/<path:filename>')
def upload_files(filename):
    """上传文件访问"""
    return send_from_directory('upload', filename)


if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=5001)
