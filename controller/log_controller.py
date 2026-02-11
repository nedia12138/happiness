"""
操作日志控制器
"""
from flask import request, session
from service.log_service import LogService
from utils.response import error


class LogController:
    """操作日志控制器类"""

    @staticmethod
    def get_log_list():
        """
        获取操作日志列表（分页）
        """
        try:
            if 'user_id' not in session:
                return error("请先登录")

            page_num = int(request.args.get('pageNum', 1))
            page_size = int(request.args.get('pageSize', 10))
            keyword = request.args.get('keyword', '').strip()
            module = request.args.get('module', '').strip()
            username = request.args.get('username', '').strip()
            action = request.args.get('action', '').strip()
            status = request.args.get('status')

            if page_num < 1:
                page_num = 1
            if page_size < 1 or page_size > 100:
                page_size = 10

            status_val = None
            if status is not None and status != '':
                try:
                    status_val = int(status)
                    if status_val not in [0, 1]:
                        status_val = None
                except ValueError:
                    status_val = None

            return LogService.get_log_list(
                page_num=page_num,
                page_size=page_size,
                keyword=keyword,
                module=module if module else None,
                status=status_val,
                username=username if username else None,
                action=action if action else None
            )
        except Exception as e:
            print(f"获取操作日志失败: {str(e)}")
            return error(f"获取操作日志失败: {str(e)}")

