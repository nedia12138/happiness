"""
数据分析服务层 - EDA探索大一统版 (SQL物理级清洗锁定)
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
            # 基础大盘：展示全库真实的 100% 物理人数
            sql_total = """
                SELECT 
                    COUNT(*) as total_count, 
                    AVG(CASE WHEN happiness > 0 THEN happiness ELSE NULL END) as avg_happiness 
                FROM py_happiness_survey_complete
            """
            overview = execute_query(sql_total)[0]

            # 数据集分布：不再过滤happiness，让测试集(Test)完美复活！
            sql_source = "SELECT dataSource, COUNT(*) as count FROM py_happiness_survey_complete GROUP BY dataSource"
            source_stats = execute_query(sql_source)

            return success({'overview': overview, 'source_stats': source_stats})
        except Exception as e:
            return error(str(e))

    @staticmethod
    def get_marital_analysis():
        """获取婚姻状况分析 (后端物理级清洗：绝对锁定总人数)"""
        try:
            sql = """
            SELECT 
                CASE 
                    WHEN marital = 1 THEN '未婚'
                    WHEN marital = 2 THEN '同居'
                    WHEN marital = 3 THEN '初婚'
                    WHEN marital = 4 THEN '再婚'
                    WHEN marital = 5 THEN '分居'
                    WHEN marital = 6 THEN '离婚'
                    WHEN marital = 7 THEN '丧偶'
                    ELSE '拒绝回答/未知'
                END as name,
                COUNT(*) as value
            FROM py_happiness_survey_complete
            GROUP BY name
            """
            return success(execute_query(sql))
        except Exception as e:
            return error(str(e))

    @staticmethod
    def get_education_analysis():
        """获取教育水平分析 (后端物理级清洗：绝对锁定总人数)"""
        try:
            sql = """
            SELECT 
                CASE 
                    WHEN edu = 1 THEN '未受教育'
                    WHEN edu = 2 THEN '私塾/扫盲'
                    WHEN edu = 3 THEN '小学'
                    WHEN edu = 4 THEN '初中'
                    WHEN edu = 5 THEN '职高'
                    WHEN edu = 6 THEN '普高'
                    WHEN edu = 7 THEN '中专'
                    WHEN edu = 8 THEN '技校'
                    WHEN edu = 9 THEN '大专'
                    WHEN edu = 10 THEN '本科'
                    WHEN edu IN (11, 12, 13) THEN '研究生及以上'
                    ELSE '拒绝回答/未知'
                END as name,
                COUNT(*) as value
            FROM py_happiness_survey_complete
            GROUP BY name
            """
            return success(execute_query(sql))
        except Exception as e:
            return error(str(e))

    @staticmethod
    def get_health_analysis():
        """获取健康状况分析 (后端物理级清洗：绝对锁定总人数)"""
        try:
            sql = """
            SELECT 
                CASE 
                    WHEN health = 1 THEN '很不健康'
                    WHEN health = 2 THEN '比较不健康'
                    WHEN health = 3 THEN '一般'
                    WHEN health = 4 THEN '比较健康'
                    WHEN health = 5 THEN '很健康'
                    ELSE '拒绝回答/未知'
                END as name,
                COUNT(*) as value
            FROM py_happiness_survey_complete
            GROUP BY name
            """
            return success(execute_query(sql))
        except Exception as e:
            return error(str(e))

    @staticmethod
    def get_income_analysis():
        """获取收入区间分析 (后端物理级清洗：精准年收入梯队)"""
        try:
            sql = """
            SELECT 
                CASE 
                    WHEN income <= 30000 AND income >= 0 THEN '低收入 (<3万)'
                    WHEN income <= 80000 AND income > 30000 THEN '中下收入 (3万-8万)'
                    WHEN income <= 150000 AND income > 80000 THEN '中等收入 (8万-15万)'
                    WHEN income <= 300000 AND income > 150000 THEN '较高收入 (15万-30万)'
                    WHEN income > 300000 THEN '高收入 (>30万)' 
                    ELSE '拒绝回答/未知'
                END as name, 
                COUNT(*) as value 
            FROM py_happiness_survey_complete 
            GROUP BY name
            """
            return success(execute_query(sql))
        except Exception as e:
            return error(str(e))

    @staticmethod
    def get_correlation_analysis():
        """获取相关性分析 (因为要计算关系散点，必须保留过滤，这不会影响前端展示总数)"""
        try:
            sql = "SELECT health, class, happiness FROM py_happiness_survey_complete WHERE happiness > 0 AND health > 0 AND class > 0 LIMIT 100"
            return success(execute_query(sql))
        except Exception as e:
            return error(str(e))

    @staticmethod
    def get_comprehensive_analysis():
        """获取综合分析 (计算平均分时必须剔除无效的，否则数学报错)"""
        try:
            sql = "SELECT gender as name, AVG(happiness) as value FROM py_happiness_survey_complete WHERE happiness > 0 AND gender > 0 GROUP BY gender"
            return success(execute_query(sql))
        except Exception as e:
            return error(str(e))