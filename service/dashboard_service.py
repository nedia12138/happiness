"""
仪表盘服务层
处理仪表盘相关的数据查询和统计逻辑
"""
from utils.db_utils import get_db_connection
from datetime import datetime, timedelta
import json

class DashboardService:
    """仪表盘服务类"""
    
    @staticmethod
    def get_user_statistics():
        """获取用户统计数据"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 总用户数
                    cursor.execute("SELECT COUNT(*) as total FROM py_user WHERE status = 'active'")
                    total_users = cursor.fetchone()['total']
                    
                    # 管理员数量
                    cursor.execute("SELECT COUNT(*) as admin_count FROM py_user WHERE role = 'admin' AND status = 'active'")
                    admin_users = cursor.fetchone()['admin_count']

                    # 操作员数量
                    cursor.execute("SELECT COUNT(*) as operation_count FROM py_user WHERE role = 'operation' AND status = 'active'")
                    operation_users = cursor.fetchone()['operation_count']

                    # 普通用户数量
                    cursor.execute("SELECT COUNT(*) as user_count FROM py_user WHERE role = 'user' AND status = 'active'")
                    normal_users = cursor.fetchone()['user_count']

                    # 今日新增用户
                    today = datetime.now().strftime('%Y-%m-%d')
                    cursor.execute("SELECT COUNT(*) as today_count FROM py_user WHERE DATE(createtime) = %s", (today,))
                    today_users = cursor.fetchone()['today_count']

                    return {
                        'total_users': total_users,
                        'admin_users': admin_users,
                        'operation_users': operation_users,
                        'normal_users': normal_users,
                        'today_users': today_users
                    }
        except Exception as e:
            print(f"获取用户统计失败: {e}")
            return {
                'total_users': 0,
                'admin_users': 0,
                'normal_users': 0,
                'today_users': 0
            }

    @staticmethod
    def get_user_trend_data(days=30):
        """获取用户注册趋势数据"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取最近30天的用户注册数据
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days-1)
                    
                    # 生成日期范围
                    date_list = []
                    current_date = start_date
                    while current_date <= end_date:
                        date_list.append(current_date.strftime('%Y-%m-%d'))
                        current_date += timedelta(days=1)
                    
                    # 查询每天的注册用户数
                    trend_data = []
                    for date_str in date_list:
                        cursor.execute("""
                            SELECT COUNT(*) as count 
                            FROM py_user 
                            WHERE DATE(createtime) = %s AND status = 'active'
                        """, (date_str,))
                        count = cursor.fetchone()['count']
                        trend_data.append(count)
                    
                    return {
                        'dates': date_list,
                        'data': trend_data
                    }
        except Exception as e:
            print(f"获取用户趋势数据失败: {e}")
            return {
                'dates': [],
                'data': []
            }
    
    @staticmethod
    def get_role_distribution():
        """获取用户角色分布数据"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT role, COUNT(*) as count 
                        FROM py_user 
                        WHERE status = 'active' 
                        GROUP BY role
                    """)
                    results = cursor.fetchall()
                    
                    distribution = []
                    role_mapping = {
                        'admin': '管理员',
                        'operation': '操作员',
                        'user': '普通用户'
                    }

                    for result in results:
                        role_name = role_mapping.get(result['role'], result['role'])
                        distribution.append({
                            'name': role_name,
                            'value': result['count']
                        })
                    
                    return distribution
        except Exception as e:
            print(f"获取角色分布数据失败: {e}")
            return []
     
    @staticmethod
    def get_dashboard_overview():
        """获取仪表盘总览数据"""
        try:
            user_stats = DashboardService.get_user_statistics()
            user_trend = DashboardService.get_user_trend_data(7)  # 最近7天
            role_distribution = DashboardService.get_role_distribution()
            
            return {
                'user_stats': user_stats,
                'announcement_stats': 0,
                'user_trend': user_trend,
                'role_distribution': role_distribution,
                'recent_activities': 0
            }
        except Exception as e:
            print(f"获取仪表盘总览数据失败: {e}")
            return {
                'user_stats': {'total_users': 0, 'admin_users': 0, 'normal_users': 0, 'today_users': 0},
                'announcement_stats': {'total_announcements': 0, 'today_announcements': 0, 'top_announcements': 0},
                'user_trend': {'dates': [], 'data': []},
                'role_distribution': [],
                'recent_activities': []
            }
