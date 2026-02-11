"""
幸福感调查表控制器
"""
from flask import request, session
from service.happiness_survey_service import HappinessSurveyService
from service.log_service import LogService
from utils.response import success, error


class HappinessSurveyController:
    """幸福感调查表控制器类"""

    @staticmethod
    def _record_log(user_id, username, action, detail, status=1):
        """记录幸福感调查表相关操作日志"""
        try:
            LogService.record_log(
                user_id=user_id,
                username=username,
                action=action,
                module="幸福感调查表管理",
                detail=detail,
                status=status,
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_path=request.path
            )
        except Exception as e:
            print(f"记录幸福感调查表日志失败: {str(e)}")

    @staticmethod
    def get_happiness_survey_list():
        """
        获取幸福感调查表列表（分页）

        Returns:
            dict: 分页响应数据
        """
        try:
            # 获取请求参数
            page_num = int(request.args.get('pageNum', 1))
            page_size = int(request.args.get('pageSize', 10))

            # 构建筛选条件
            filters = {}

            # 获取筛选参数
            happiness = request.args.get('happiness')
            province = request.args.get('province')
            city = request.args.get('city')
            gender = request.args.get('gender')
            edu = request.args.get('edu')
            data_source = request.args.get('dataSource')
            keyword = request.args.get('keyword', '').strip()

            # 参数验证和转换
            if page_num < 1:
                page_num = 1
            if page_size < 1 or page_size > 100:
                page_size = 10

            # 转换筛选参数
            if happiness is not None and happiness != '':
                try:
                    filters['happiness'] = int(happiness)
                except ValueError:
                    pass

            if province is not None and province != '':
                try:
                    filters['province'] = int(province)
                except ValueError:
                    pass

            if city is not None and city != '':
                try:
                    filters['city'] = int(city)
                except ValueError:
                    pass

            if gender is not None and gender != '':
                try:
                    filters['gender'] = int(gender)
                except ValueError:
                    pass

            if edu is not None and edu != '':
                try:
                    filters['edu'] = int(edu)
                except ValueError:
                    pass

            if data_source:
                filters['dataSource'] = data_source

            if keyword:
                filters['keyword'] = keyword

            return HappinessSurveyService.get_happiness_survey_list(page_num, page_size, filters)

        except Exception as e:
            print(f"获取幸福感调查表列表失败: {str(e)}")
            return error(f"获取幸福感调查表列表失败: {str(e)}")

    @staticmethod
    def get_happiness_survey_detail():
        """
        获取幸福感调查表详情

        Returns:
            dict: 响应数据
        """
        try:
            survey_id = request.args.get('id')
            if not survey_id:
                return error("缺少调查记录ID参数")

            try:
                survey_id = int(survey_id)
            except ValueError:
                return error("调查记录ID格式错误")

            return HappinessSurveyService.get_happiness_survey_by_id(survey_id)

        except Exception as e:
            print(f"获取幸福感调查表详情失败: {str(e)}")
            return error(f"获取幸福感调查表详情失败: {str(e)}")

    @staticmethod
    def get_happiness_statistics():
        """
        获取幸福感统计数据

        Returns:
            dict: 响应数据
        """
        try:
            # 检查用户登录状态
            if 'user_id' not in session:
                return error("请先登录")

            result = HappinessSurveyService.get_happiness_statistics()
            if result.get('code') == 200:
                HappinessSurveyController._record_log(
                    session.get('user_id'),
                    session.get('username'),
                    '查看幸福感统计',
                    '获取幸福感调查表统计数据'
                )
            return result

        except Exception as e:
            print(f"获取幸福感统计数据失败: {str(e)}")
            return error(f"获取幸福感统计数据失败: {str(e)}")
