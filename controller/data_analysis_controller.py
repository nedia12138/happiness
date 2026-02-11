"""
数据分析控制器
"""
from flask import request, session
from service.data_analysis_service import DataAnalysisService
from service.log_service import LogService
from utils.response import success, error
from utils.auth_utils import operation_required


class DataAnalysisController:
    """数据分析控制器类"""

    @staticmethod
    def _record_log(user_id, username, action, detail, status=1):
        """记录数据分析相关操作日志"""
        try:
            LogService.record_log(
                user_id=user_id,
                username=username,
                action=action,
                module="数据分析",
                detail=detail,
                status=status,
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_path=request.path
            )
        except Exception as e:
            print(f"记录数据分析日志失败: {str(e)}")

    @staticmethod
    @operation_required
    def get_happiness_overview():
        """
        获取幸福感数据概览

        Returns:
            dict: 概览数据响应
        """
        try:
            current_user = session.get('user_id')
            username = session.get('username')

            result = DataAnalysisService.get_happiness_overview()

            if result['code'] == 200:
                DataAnalysisController._record_log(
                    current_user, username,
                    "查看概览", "获取幸福感数据概览统计"
                )

            return result

        except Exception as e:
            DataAnalysisController._record_log(
                session.get('user_id'), session.get('username'),
                "查看概览", f"获取幸福感数据概览失败: {str(e)}", 0
            )
            return error(f"获取幸福感数据概览失败: {str(e)}")

    @staticmethod
    @operation_required
    def get_marital_analysis():
        """
        获取婚姻状况分析

        Returns:
            dict: 婚姻状况分析数据响应
        """
        try:
            current_user = session.get('user_id')
            username = session.get('username')

            result = DataAnalysisService.get_marital_analysis()

            if result['code'] == 200:
                DataAnalysisController._record_log(
                    current_user, username,
                    "婚姻分析", "获取婚姻状况对幸福感的影响分析"
                )

            return result

        except Exception as e:
            DataAnalysisController._record_log(
                session.get('user_id'), session.get('username'),
                "婚姻分析", f"获取婚姻状况分析失败: {str(e)}", 0
            )
            return error(f"获取婚姻状况分析失败: {str(e)}")

    @staticmethod
    @operation_required
    def get_education_analysis():
        """
        获取教育水平分析

        Returns:
            dict: 教育水平分析数据响应
        """
        try:
            current_user = session.get('user_id')
            username = session.get('username')

            result = DataAnalysisService.get_education_analysis()

            if result['code'] == 200:
                DataAnalysisController._record_log(
                    current_user, username,
                    "教育分析", "获取教育水平对幸福感的影响分析"
                )

            return result

        except Exception as e:
            DataAnalysisController._record_log(
                session.get('user_id'), session.get('username'),
                "教育分析", f"获取教育水平分析失败: {str(e)}", 0
            )
            return error(f"获取教育水平分析失败: {str(e)}")

    @staticmethod
    @operation_required
    def get_income_analysis():
        """
        获取收入区间分析

        Returns:
            dict: 收入区间分析数据响应
        """
        try:
            current_user = session.get('user_id')
            username = session.get('username')

            result = DataAnalysisService.get_income_analysis()

            if result['code'] == 200:
                DataAnalysisController._record_log(
                    current_user, username,
                    "收入分析", "获取收入区间对幸福感的影响分析"
                )

            return result

        except Exception as e:
            DataAnalysisController._record_log(
                session.get('user_id'), session.get('username'),
                "收入分析", f"获取收入区间分析失败: {str(e)}", 0
            )
            return error(f"获取收入区间分析失败: {str(e)}")

    @staticmethod
    @operation_required
    def get_health_analysis():
        """
        获取健康状况分析

        Returns:
            dict: 健康状况分析数据响应
        """
        try:
            current_user = session.get('user_id')
            username = session.get('username')

            result = DataAnalysisService.get_health_analysis()

            if result['code'] == 200:
                DataAnalysisController._record_log(
                    current_user, username,
                    "健康分析", "获取健康状况对幸福感的影响分析"
                )

            return result

        except Exception as e:
            DataAnalysisController._record_log(
                session.get('user_id'), session.get('username'),
                "健康分析", f"获取健康状况分析失败: {str(e)}", 0
            )
            return error(f"获取健康状况分析失败: {str(e)}")

    @staticmethod
    @operation_required
    def get_correlation_analysis():
        """
        获取相关性分析

        Returns:
            dict: 相关性分析数据响应
        """
        try:
            current_user = session.get('user_id')
            username = session.get('username')

            result = DataAnalysisService.get_correlation_analysis()

            if result['code'] == 200:
                DataAnalysisController._record_log(
                    current_user, username,
                    "相关性分析", "获取各因素间的相关性分析"
                )

            return result

        except Exception as e:
            DataAnalysisController._record_log(
                session.get('user_id'), session.get('username'),
                "相关性分析", f"获取相关性分析失败: {str(e)}", 0
            )
            return error(f"获取相关性分析失败: {str(e)}")

    @staticmethod
    @operation_required
    def get_comprehensive_analysis():
        """
        获取综合分析结论

        Returns:
            dict: 综合分析结论响应
        """
        try:
            current_user = session.get('user_id')
            username = session.get('username')

            result = DataAnalysisService.get_comprehensive_analysis()

            if result['code'] == 200:
                DataAnalysisController._record_log(
                    current_user, username,
                    "综合分析", "获取多维度分析结论"
                )

            return result

        except Exception as e:
            DataAnalysisController._record_log(
                session.get('user_id'), session.get('username'),
                "综合分析", f"获取综合分析失败: {str(e)}", 0
            )
            return error(f"获取综合分析失败: {str(e)}")
