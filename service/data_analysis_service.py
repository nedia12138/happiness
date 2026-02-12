"""
数据分析服务层 - 完整补全版
"""
from utils.db_utils import execute_query
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)

class DataAnalysisService:
    @staticmethod
    def get_happiness_overview():
        """获取幸福感概览"""
        try:
            sql_total = "SELECT COUNT(*) as total_count, AVG(happiness) as avg_happiness FROM py_happiness_survey_complete WHERE happiness > 0"
            overview = execute_query(sql_total)[0]
            sql_source = "SELECT dataSource, COUNT(*) as count FROM py_happiness_survey_complete GROUP BY dataSource"
            source_stats = execute_query(sql_source)
            return success({'overview': overview, 'source_stats': source_stats})
        except Exception as e: return error(str(e))

    @staticmethod
    def get_marital_analysis():
        """获取婚姻状况分析 (补全)"""
        try:
            sql = "SELECT marital as name, COUNT(*) as value FROM py_happiness_survey_complete WHERE happiness > 0 GROUP BY marital"
            return success(execute_query(sql))
        except Exception as e: return error(str(e))

    @staticmethod
    def get_education_analysis():
        """获取教育水平分析 (补全)"""
        try:
            sql = "SELECT edu as name, COUNT(*) as value FROM py_happiness_survey_complete WHERE happiness > 0 GROUP BY edu"
            return success(execute_query(sql))
        except Exception as e: return error(str(e))

    @staticmethod
    def get_health_analysis():
        """获取健康状况分析 (补全)"""
        try:
            sql = "SELECT health as name, COUNT(*) as value FROM py_happiness_survey_complete WHERE happiness > 0 GROUP BY health"
            return success(execute_query(sql))
        except Exception as e: return error(str(e))

    @staticmethod
    def get_income_analysis():
        """获取收入区间分析 (补全)"""
        try:
            sql = "SELECT CASE WHEN income < 5000 THEN '低收入' WHEN income < 15000 THEN '中收入' ELSE '高收入' END as name, COUNT(*) as value FROM py_happiness_survey_complete WHERE happiness > 0 GROUP BY name"
            return success(execute_query(sql))
        except Exception as e: return error(str(e))

    @staticmethod
    def get_correlation_analysis():
        """获取相关性分析 (补全)"""
        try:
            sql = "SELECT health, class, happiness FROM py_happiness_survey_complete WHERE happiness > 0 LIMIT 100"
            return success(execute_query(sql))
        except Exception as e: return error(str(e))

    @staticmethod
    def get_comprehensive_analysis():
        """获取综合分析 (补全)"""
        try:
            sql = "SELECT gender as name, AVG(happiness) as value FROM py_happiness_survey_complete WHERE happiness > 0 GROUP BY gender"
            return success(execute_query(sql))
        except Exception as e: return error(str(e))