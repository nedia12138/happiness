"""
操作日志服务
"""
from utils.db_utils import get_db_connection
from utils.response import page_response, error
from datetime import datetime


class LogService:
    """操作日志服务类"""

    @staticmethod
    def record_log(user_id=None, username=None, action="", module="", detail="", status=1,
                   ip=None, user_agent=None, request_method=None, request_path=None):
        """
        记录操作日志
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO py_operation_logs
                        (userId, username, action, module, detail, status, ip, userAgent, requestMethod, requestPath, createTime)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    params = [
                        user_id, username, action, module, detail, status,
                        ip, user_agent, request_method, request_path
                    ]
                    print(f"执行SQL: {sql}, 参数: {params}")
                    cursor.execute(sql, params)
                    conn.commit()
        except Exception as e:
            # 日志记录失败不影响主流程
            print(f"记录操作日志失败: {str(e)}")

    @staticmethod
    def get_log_list(page_num=1, page_size=10, keyword=None, module=None,
                     status=None, username=None, action=None):
        """
        分页获取操作日志
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    conditions = []
                    params = []

                    if keyword:
                        conditions.append("(detail LIKE %s OR requestPath LIKE %s)")
                        keyword_param = f"%{keyword}%"
                        params.extend([keyword_param, keyword_param])

                    if module:
                        conditions.append("module = %s")
                        params.append(module)

                    if username:
                        conditions.append("username LIKE %s")
                        params.append(f"%{username}%")

                    if action:
                        conditions.append("action LIKE %s")
                        params.append(f"%{action}%")

                    if status in [0, 1]:
                        conditions.append("status = %s")
                        params.append(status)

                    where_clause = ""
                    if conditions:
                        where_clause = "WHERE " + " AND ".join(conditions)

                    count_sql = f"SELECT COUNT(*) AS total FROM py_operation_logs {where_clause}"
                    print(f"执行SQL: {count_sql}, 参数: {params}")
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone().get('total', 0)

                    offset = (page_num - 1) * page_size
                    data_sql = f"""
                        SELECT id, userId, username, module, action, detail, status,
                               ip, userAgent, requestMethod, requestPath, createTime
                        FROM py_operation_logs
                        {where_clause}
                        ORDER BY createTime DESC
                        LIMIT %s OFFSET %s
                    """
                    params_with_page = params + [page_size, offset]
                    print(f"执行SQL: {data_sql}, 参数: {params_with_page}")
                    cursor.execute(data_sql, params_with_page)
                    rows = cursor.fetchall()

                    for row in rows:
                        if isinstance(row.get('createTime'), datetime):
                            row['createTime'] = row['createTime'].strftime('%Y-%m-%d %H:%M:%S')

                    return page_response(rows, total, page_num, page_size)
        except Exception as e:
            print(f"获取操作日志失败: {str(e)}")
            return error(f"获取操作日志失败: {str(e)}")

