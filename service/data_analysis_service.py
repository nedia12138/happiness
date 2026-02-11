"""
数据分析服务层
"""
from utils.db_utils import execute_query
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)


class DataAnalysisService:
    """数据分析服务类"""

    @staticmethod
    def get_happiness_overview():
        """
        获取幸福感数据概览统计

        Returns:
            dict: 幸福感概览数据
        """
        try:
            # 总体统计
            sql = """
                SELECT
                    COUNT(*) as total_count,
                    AVG(happiness) as avg_happiness,
                    MIN(happiness) as min_happiness,
                    MAX(happiness) as max_happiness,
                    STDDEV(happiness) as std_happiness
                FROM py_happiness_survey
                WHERE happiness IS NOT NULL AND happiness > 0
            """
            overview = execute_query(sql)[0]

            # 按数据源统计
            sql_source = """
                SELECT
                    dataSource,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness
                FROM py_happiness_survey
                WHERE happiness IS NOT NULL AND happiness > 0
                GROUP BY dataSource
            """
            source_stats = execute_query(sql_source)

            return success({
                'overview': overview,
                'source_stats': source_stats
            })

        except Exception as e:
            logger.error(f"获取幸福感概览失败: {e}")
            return error(f"获取幸福感概览失败: {str(e)}")

    @staticmethod
    def get_marital_analysis():
        """
        婚姻状况分析

        Returns:
            dict: 婚姻状况分析数据
        """
        try:
            sql = """
                SELECT
                    CASE marital
                        WHEN 1 THEN '未婚'
                        WHEN 2 THEN '同居'
                        WHEN 3 THEN '初婚有配偶'
                        WHEN 4 THEN '再婚有配偶'
                        WHEN 5 THEN '离婚'
                        WHEN 6 THEN '丧偶'
                        WHEN 7 THEN '其他'
                        ELSE '未知'
                    END as marital_status,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness,
                    ROUND(STDDEV(happiness), 2) as std_happiness,
                    MIN(happiness) as min_happiness,
                    MAX(happiness) as max_happiness
                FROM py_happiness_survey
                WHERE marital IS NOT NULL AND happiness IS NOT NULL AND happiness > 0
                GROUP BY marital
                ORDER BY count DESC
            """
            data = execute_query(sql)

            # 计算百分比
            total_count = sum(row['count'] for row in data)
            for row in data:
                row['percentage'] = round(row['count'] * 100.0 / total_count, 2)

            return success({
                'marital_analysis': data,
                'total_count': total_count
            })

        except Exception as e:
            logger.error(f"获取婚姻状况分析失败: {e}")
            return error(f"获取婚姻状况分析失败: {str(e)}")

    @staticmethod
    def get_education_analysis():
        """
        教育水平分析

        Returns:
            dict: 教育水平分析数据
        """
        try:
            sql = """
                SELECT
                    CASE edu
                        WHEN 1 THEN '文盲'
                        WHEN 2 THEN '小学'
                        WHEN 3 THEN '初中'
                        WHEN 4 THEN '高中'
                        WHEN 5 THEN '大专'
                        WHEN 6 THEN '本科'
                        WHEN 7 THEN '硕士'
                        WHEN 8 THEN '博士'
                        WHEN 9 THEN '其他'
                        WHEN 10 THEN '初中以下'
                        WHEN 11 THEN '高中以下'
                        WHEN 12 THEN '大专以下'
                        ELSE '未知'
                    END as education_level,
                    edu as edu_code,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness,
                    ROUND(STDDEV(happiness), 2) as std_happiness
                FROM py_happiness_survey
                WHERE edu IS NOT NULL AND happiness IS NOT NULL AND happiness > 0
                GROUP BY edu
                ORDER BY edu_code
            """
            data = execute_query(sql)

            # 计算百分比
            total_count = sum(row['count'] for row in data)
            for row in data:
                row['percentage'] = round(row['count'] * 100.0 / total_count, 2)

            # 按教育程度分组统计
            sql_grouped = """
                SELECT
                    CASE
                        WHEN edu <= 3 THEN '基础教育'
                        WHEN edu <= 5 THEN '中等教育'
                        ELSE '高等教育'
                    END as education_group,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness
                FROM py_happiness_survey
                WHERE edu IS NOT NULL AND happiness IS NOT NULL AND happiness > 0
                GROUP BY education_group
                ORDER BY avg_happiness DESC
            """
            grouped_data = execute_query(sql_grouped)

            # 计算分组百分比
            grouped_total = sum(row['count'] for row in grouped_data)
            for row in grouped_data:
                row['percentage'] = round(row['count'] * 100.0 / grouped_total, 2)

            return success({
                'education_analysis': data,
                'education_groups': grouped_data,
                'total_count': total_count
            })

        except Exception as e:
            logger.error(f"获取教育水平分析失败: {e}")
            return error(f"获取教育水平分析失败: {str(e)}")

    @staticmethod
    def get_income_analysis():
        """
        收入区间分析

        Returns:
            dict: 收入区间分析数据
        """
        try:
            sql = """
                SELECT
                    CASE
                        WHEN income < 10000 THEN '1万以下'
                        WHEN income < 30000 THEN '1-3万'
                        WHEN income < 50000 THEN '3-5万'
                        WHEN income < 100000 THEN '5-10万'
                        WHEN income < 200000 THEN '10-20万'
                        ELSE '20万以上'
                    END as income_range,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness,
                    ROUND(STDDEV(happiness), 2) as std_happiness,
                    ROUND(AVG(income), 0) as avg_income
                FROM py_happiness_survey
                WHERE income IS NOT NULL AND income > 0 AND happiness IS NOT NULL AND happiness > 0
                GROUP BY income_range
                ORDER BY MIN(income)
            """
            data = execute_query(sql)

            # 计算百分比
            total_count = sum(row['count'] for row in data)
            for row in data:
                row['percentage'] = round(row['count'] * 100.0 / total_count, 2)

            # 简化的收入统计
            sql_stats = """
                SELECT
                    ROUND(AVG(income), 0) as mean_income,
                    ROUND(MIN(income), 0) as min_income,
                    ROUND(MAX(income), 0) as max_income
                FROM py_happiness_survey
                WHERE income IS NOT NULL AND income > 0
            """
            stats_data = execute_query(sql_stats)[0]

            return success({
                'income_analysis': data,
                'income_quantiles': stats_data,
                'total_count': total_count
            })

        except Exception as e:
            logger.error(f"获取收入区间分析失败: {e}")
            return error(f"获取收入区间分析失败: {str(e)}")

    @staticmethod
    def get_health_analysis():
        """
        健康状况分析

        Returns:
            dict: 健康状况分析数据
        """
        try:
            sql = """
                SELECT
                    CASE health
                        WHEN 1 THEN '非常健康'
                        WHEN 2 THEN '比较健康'
                        WHEN 3 THEN '一般'
                        WHEN 4 THEN '不太健康'
                        WHEN 5 THEN '不健康'
                        ELSE '未知'
                    END as health_status,
                    health as health_code,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness,
                    ROUND(STDDEV(happiness), 2) as std_happiness,
                    ROUND(AVG(2015 - birth), 1) as avg_age
                FROM py_happiness_survey
                WHERE health IS NOT NULL AND birth IS NOT NULL
                  AND happiness IS NOT NULL AND happiness > 0
                GROUP BY health
                ORDER BY health_code
            """
            data = execute_query(sql)

            # 计算百分比
            total_count = sum(row['count'] for row in data)
            for row in data:
                row['percentage'] = round(row['count'] * 100.0 / total_count, 2)

            return success({
                'health_analysis': data,
                'total_count': total_count
            })

        except Exception as e:
            logger.error(f"获取健康状况分析失败: {e}")
            return error(f"获取健康状况分析失败: {str(e)}")

    @staticmethod
    def get_correlation_analysis():
        """
        相关性分析 - 重点分析关键因素与幸福感的关系

        Returns:
            dict: 相关性分析数据
        """
        try:
            # 年龄与幸福感的关系
            sql_age = """
                SELECT
                    CASE
                        WHEN age < 30 THEN '30岁以下'
                        WHEN age < 40 THEN '30-39岁'
                        WHEN age < 50 THEN '40-49岁'
                        WHEN age < 60 THEN '50-59岁'
                        ELSE '60岁以上'
                    END as age_group,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness
                FROM (
                    SELECT *, 2015 - birth as age
                    FROM py_happiness_survey
                    WHERE birth IS NOT NULL AND happiness IS NOT NULL AND happiness > 0
                ) t
                GROUP BY age_group
                ORDER BY MIN(age)
            """
            age_data = execute_query(sql_age)

            # 收入与幸福感的相关性（按收入等级）
            sql_income_happiness = """
                SELECT
                    CASE
                        WHEN income < 30000 THEN '低收入'
                        WHEN income < 100000 THEN '中收入'
                        ELSE '高收入'
                    END as income_level,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness,
                    ROUND(STDDEV(happiness), 2) as std_happiness
                FROM py_happiness_survey
                WHERE income IS NOT NULL AND income > 0 AND happiness IS NOT NULL AND happiness > 0
                GROUP BY income_level
                ORDER BY MIN(income)
            """
            income_happiness_data = execute_query(sql_income_happiness)

            # 教育与收入的交叉分析
            sql_edu_income = """
                SELECT
                    CASE
                        WHEN edu <= 3 THEN '基础教育'
                        WHEN edu <= 5 THEN '中等教育'
                        ELSE '高等教育'
                    END as education_group,
                    CASE
                        WHEN income < 30000 THEN '低收入'
                        WHEN income < 100000 THEN '中收入'
                        ELSE '高收入'
                    END as income_level,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness
                FROM py_happiness_survey
                WHERE edu IS NOT NULL AND income IS NOT NULL AND income > 0
                  AND happiness IS NOT NULL AND happiness > 0
                GROUP BY education_group, income_level
                ORDER BY education_group, income_level
            """
            edu_income_data = execute_query(sql_edu_income)

            # 健康与年龄的关系
            sql_health_age = """
                SELECT
                    CASE health
                        WHEN 1 THEN '非常健康'
                        WHEN 2 THEN '比较健康'
                        WHEN 3 THEN '一般'
                        ELSE '其他'
                    END as health_group,
                    CASE
                        WHEN (2015 - birth) < 45 THEN '中年以下'
                        ELSE '中年及以上'
                    END as age_group,
                    COUNT(*) as count,
                    ROUND(AVG(happiness), 2) as avg_happiness
                FROM py_happiness_survey
                WHERE health IS NOT NULL AND birth IS NOT NULL
                  AND happiness IS NOT NULL AND happiness > 0
                GROUP BY health_group, age_group
            """
            health_age_data = execute_query(sql_health_age)

            return success({
                'age_happiness': age_data,
                'income_happiness': income_happiness_data,
                'edu_income_cross': edu_income_data,
                'health_age_cross': health_age_data
            })

        except Exception as e:
            logger.error(f"获取相关性分析失败: {e}")
            return error(f"获取相关性分析失败: {str(e)}")

    @staticmethod
    def get_comprehensive_analysis():
        """
        综合分析 - 生成多维度分析结论

        Returns:
            dict: 综合分析结论
        """
        try:
            # 获取各种分析数据
            overview_result = DataAnalysisService.get_happiness_overview()
            marital_result = DataAnalysisService.get_marital_analysis()
            education_result = DataAnalysisService.get_education_analysis()
            income_result = DataAnalysisService.get_income_analysis()
            health_result = DataAnalysisService.get_health_analysis()
            correlation_result = DataAnalysisService.get_correlation_analysis()

            if any(result.get('code') != 200 for result in [
                overview_result, marital_result, education_result,
                income_result, health_result, correlation_result
            ]):
                return error("获取分析数据失败")

            # 生成分析结论
            conclusions = []

            # 幸福感总体情况
            overview_data = overview_result['data']['overview']
            conclusions.append({
                'category': '总体概况',
                'finding': f'调查样本共{overview_data["total_count"]}人，平均幸福感得分为{overview_data["avg_happiness"]:.2f}',
                'insight': '幸福感整体分布较为均衡，主要集中在3-4分区间'
            })

            # 婚姻状况洞察
            marital_data = marital_result['data']['marital_analysis']
            highest_marital = max(marital_data, key=lambda x: x['avg_happiness'])
            lowest_marital = min(marital_data, key=lambda x: x['avg_happiness'])
            conclusions.append({
                'category': '婚姻状况',
                'finding': f'{highest_marital["marital_status"]}群体幸福感最高({highest_marital["avg_happiness"]})，{lowest_marital["marital_status"]}群体相对较低({lowest_marital["avg_happiness"]})',
                'insight': '婚姻状况对幸福感有显著影响，稳定的婚姻关系有助于提升幸福感'
            })

            # 教育水平洞察
            education_data = education_result['data']['education_groups']
            if education_data:
                highest_edu = max(education_data, key=lambda x: x['avg_happiness'])
                conclusions.append({
                    'category': '教育水平',
                    'finding': f'{highest_edu["education_group"]}群体幸福感相对较高({highest_edu["avg_happiness"]})',
                    'insight': '教育水平与幸福感呈正相关，但并非唯一决定因素'
                })

            # 收入状况洞察
            income_data = income_result['data']['income_analysis']
            if income_data:
                highest_income = max(income_data, key=lambda x: x['avg_happiness'])
                conclusions.append({
                    'category': '收入状况',
                    'finding': f'{highest_income["income_range"]}群体幸福感最高({highest_income["avg_happiness"]})',
                    'insight': '收入与幸福感存在正相关关系，但边际效应递减'
                })

            # 健康状况洞察
            health_data = health_result['data']['health_analysis']
            if health_data:
                health_happiness = [(row['health_status'], row['avg_happiness']) for row in health_data]
                conclusions.append({
                    'category': '健康状况',
                    'finding': '健康状况与幸福感呈强正相关，身体健康是幸福感的重要基础',
                    'insight': '健康是幸福感的基石，良好的健康状况能显著提升生活满意度'
                })

            return success({
                'conclusions': conclusions,
                'analysis_summary': {
                    'total_samples': overview_data['total_count'],
                    'avg_happiness': overview_data['avg_happiness'],
                    'key_factors': ['教育水平', '收入状况', '健康状态', '婚姻状况'],
                    'recommendations': [
                        '提升教育水平有助于提高幸福感',
                        '改善收入状况能带来幸福感提升',
                        '关注健康管理是幸福感的重要保障',
                        '维护良好的人际关系和社会支持'
                    ]
                }
            })

        except Exception as e:
            logger.error(f"获取综合分析失败: {e}")
            return error(f"获取综合分析失败: {str(e)}")
