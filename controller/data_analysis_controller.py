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

    @staticmethod
    def save_chart():
        """
        接收前端传来的 Base64 图像并开展静默保存工作 (防重复覆盖高性能版)
        """
        try:
            import os
            import base64
            from flask import request
            # 确保你文件顶部有从 utils.response 导入 success, error

            data = request.json
            image_base64 = data.get('image')
            file_name = data.get('fileName', 'default_chart.png')

            # 1. 严格锁定你要求的论文模型绝对路径
            save_dir = "/Users/nan/Desktop/paper/happiness/Predictive/models"

            # 2. 开展路径的核验与创建工作
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # 3. 拼接最终将要生成的文件路径
            file_path = os.path.join(save_dir, file_name)

            # ================= 核心防抖逻辑：如果存在直接打回，不消耗性能 =================
            if os.path.exists(file_path):
                # 直接返回 200，告诉前端稳得很，但后端偷偷省了力气
                return success({"path": file_path, "msg": "文件已存在，为节省磁盘性能已自动跳过落盘"})
            # ==============================================================================

            # 4. 只有文件不存在时，才开展耗时的 Base64 解码与物理写入工作
            if image_base64 and "," in image_base64:
                header, encoded = image_base64.split(",", 1)
                image_data = base64.b64decode(encoded)

                with open(file_path, "wb") as f:
                    f.write(image_data)

                return success({"path": file_path, "msg": "图表首次渲染，已成功落盘"})
            else:
                return error("图像数据异常")

        except Exception as e:
            return error(f"静默保存图像失败: {str(e)}")



    # @staticmethod
    # def save_chart():
    #     """
    #     接收前端传来的 Base64 图像并开展静默保存工作
    #     """
    #     try:
    #         import os
    #         import base64
    #         data = request.json
    #         image_base64 = data.get('image')
    #         file_name = data.get('fileName', 'default_chart.png')
    #
    #         # 1. 严格锁定你要求的论文模型绝对路径
    #         save_dir = "/Users/nan/Desktop/paper/happiness/Predictive/models"
    #
    #         # 2. 开展路径的核验与创建工作
    #         if not os.path.exists(save_dir):
    #             os.makedirs(save_dir)
    #
    #         # 3. 对前端传来的 Base64 数据开展剥离与解码工作
    #         if image_base64 and "," in image_base64:
    #             header, encoded = image_base64.split(",", 1)
    #             image_data = base64.b64decode(encoded)
    #
    #             # 4. 执行最终的物理文件写入工作
    #             file_path = os.path.join(save_dir, file_name)
    #             with open(file_path, "wb") as f:
    #                 f.write(image_data)
    #
    #             # 返回成功字典格式，交由蓝图去 jsonify
    #             return success({"path": file_path, "msg": "图表已成功落盘"})
    #         else:
    #             return error("图像数据异常")
    #
    #     except Exception as e:
    #         return error(f"静默保存图像失败: {str(e)}")