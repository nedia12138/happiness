"""
数据分析服务层 - 完美修复版
"""
from utils.db_utils import execute_query
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)


class DataAnalysisService:
    @staticmethod
    def get_happiness_overview():
        """
        获取幸福感数据概览统计 - 解决 test 消失的根本方案
        """
        try:
            # 1. 总体统计 (只针对有分数的数据计算平均值)
            sql_total = """
                SELECT
                    COUNT(*) as total_count,
                    AVG(happiness) as avg_happiness,
                    MIN(happiness) as min_happiness,
                    MAX(happiness) as max_happiness,
                    STDDEV(happiness) as std_happiness
                FROM py_happiness_survey_complete
                WHERE happiness IS NOT NULL AND happiness > 0
            """
            overview = execute_query(sql_total)[0]

            # 2. 按数据源统计 (关键：去掉 WHERE 过滤，确保能统计到 test 条数)
            sql_source = """
                SELECT
                    dataSource,
                    COUNT(*) as count,
                    ROUND(AVG(CASE WHEN happiness > 0 THEN happiness ELSE NULL END), 2) as avg_happiness
                FROM py_happiness_survey_complete
                GROUP BY dataSource
            """
            source_stats = execute_query(sql_source)

            # 日志打印，你可以通过控制台看到 [train, test] 两个都在了
            logger.info(f"📊 后端返回统计项: {[s['dataSource'] for s in source_stats]}")

            return success({
                'overview': overview,
                'source_stats': source_stats
            })
        except Exception as e:
            logger.error(f"获取概览失败: {e}")
            return error(str(e))

    # ... 以下其他函数 (get_education_analysis, get_income_analysis 等) 保持原样即可 ...
    # 只需要确保 get_happiness_overview 函数按上面这个逻辑修改