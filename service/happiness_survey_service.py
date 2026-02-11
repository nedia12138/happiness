"""
幸福感调查表服务层
"""
import pymysql
from datetime import datetime
from utils.db_utils import get_db_connection
from utils.response import success, error, page_response


class HappinessSurveyService:
    """幸福感调查表服务类"""

    @staticmethod
    def get_happiness_survey_list(page_num=1, page_size=10, filters=None):
        """
        获取幸福感调查表列表（分页）

        Args:
            page_num: 页码
            page_size: 每页数量
            filters: 筛选条件字典，包含：
                - happiness: 幸福感评分
                - province: 省份代码
                - city: 城市代码
                - gender: 性别
                - edu: 教育水平
                - dataSource: 数据来源
                - keyword: 关键词搜索（目前无实际作用，保留接口）

        Returns:
            dict: 分页响应数据
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 构建查询条件
                    where_conditions = []
                    params = []

                    if filters:
                        # 幸福感评分筛选
                        if filters.get('happiness') is not None:
                            where_conditions.append("happiness = %s")
                            params.append(filters['happiness'])

                        # 省份筛选
                        if filters.get('province') is not None:
                            where_conditions.append("province = %s")
                            params.append(filters['province'])

                        # 城市筛选
                        if filters.get('city') is not None:
                            where_conditions.append("city = %s")
                            params.append(filters['city'])

                        # 性别筛选
                        if filters.get('gender') is not None:
                            where_conditions.append("gender = %s")
                            params.append(filters['gender'])

                        # 教育水平筛选
                        if filters.get('edu') is not None:
                            where_conditions.append("edu = %s")
                            params.append(filters['edu'])

                        # 数据来源筛选
                        if filters.get('dataSource'):
                            where_conditions.append("dataSource = %s")
                            params.append(filters['dataSource'])

                    # 如果没有指定 happiness 筛选条件，则默认只显示有 happiness 值的记录
                    if not filters.get('happiness') and not filters.get('show_all'):
                        where_conditions.append("happiness IS NOT NULL")

                    where_clause = ""
                    if where_conditions:
                        where_clause = "WHERE " + " AND ".join(where_conditions)

                    # 查询总数
                    count_sql = f"SELECT COUNT(*) as total FROM py_happiness_survey {where_clause}"
                    print(f"执行SQL: {count_sql}, 参数: {params}")
                    cursor.execute(count_sql, params)
                    total_result = cursor.fetchone()
                    total = total_result['total'] if total_result else 0

                    # 查询数据
                    offset = (page_num - 1) * page_size

                    data_sql = f"""
                        SELECT id, happiness, surveyType, province, city, county, surveyTime, gender, birth,
                               nationality, religion, religionFreq, edu, income, political, floorArea,
                               heightCm, weightJin, health, healthProblem, depression, hukou, socialize,
                               relax, learn, equity, class, workExper, workStatus, workYr, workType,
                               workManage, familyIncome, familyM, familyStatus, house, car, marital,
                               statusPeer, status3Before, view, incAbility, dataSource, createTime, updateTime
                        FROM py_happiness_survey
                        {where_clause}
                        ORDER BY id DESC
                        LIMIT %s OFFSET %s
                    """
                    params.extend([page_size, offset])
                    print(f"执行SQL: {data_sql}, 参数: {params}")
                    cursor.execute(data_sql, params)
                    rows = cursor.fetchall()

                    return page_response(rows, total, page_num, page_size)

        except Exception as e:
            print(f"获取幸福感调查表列表失败: {str(e)}")
            return error(f"获取幸福感调查表列表失败: {str(e)}")

    @staticmethod
    def get_happiness_survey_by_id(survey_id):
        """
        根据ID获取幸福感调查表详情

        Args:
            survey_id: 调查表ID

        Returns:
            dict: 响应数据
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT id, happiness, surveyType, province, city, county, surveyTime, gender, birth,
                               nationality, religion, religionFreq, edu, income, political, floorArea,
                               heightCm, weightJin, health, healthProblem, depression, hukou, socialize,
                               relax, learn, equity, class, workExper, workStatus, workYr, workType,
                               workManage, familyIncome, familyM, familyStatus, house, car, marital,
                               statusPeer, status3Before, view, incAbility, dataSource, createTime, updateTime
                        FROM py_happiness_survey
                        WHERE id = %s
                    """
                    print(f"执行SQL: {sql}, 参数: [{survey_id}]")
                    cursor.execute(sql, [survey_id])
                    row = cursor.fetchone()

                    if not row:
                        return error("调查记录不存在")

                    return success(row)

        except Exception as e:
            print(f"获取幸福感调查表详情失败: {str(e)}")
            return error(f"获取幸福感调查表详情失败: {str(e)}")

    @staticmethod
    def get_happiness_statistics():
        """
        获取幸福感统计数据

        Returns:
            dict: 统计数据
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 幸福感评分分布统计
                    happiness_stats_sql = """
                        SELECT happiness, COUNT(*) as count
                        FROM py_happiness_survey
                        GROUP BY happiness
                        ORDER BY happiness
                    """
                    print(f"执行SQL: {happiness_stats_sql}")
                    cursor.execute(happiness_stats_sql)
                    happiness_stats = cursor.fetchall()

                    # 性别分布统计
                    gender_stats_sql = """
                        SELECT gender, COUNT(*) as count
                        FROM py_happiness_survey
                        WHERE gender IS NOT NULL
                        GROUP BY gender
                        ORDER BY gender
                    """
                    print(f"执行SQL: {gender_stats_sql}")
                    cursor.execute(gender_stats_sql)
                    gender_stats = cursor.fetchall()

                    # 教育水平分布统计
                    edu_stats_sql = """
                        SELECT edu, COUNT(*) as count
                        FROM py_happiness_survey
                        WHERE edu IS NOT NULL
                        GROUP BY edu
                        ORDER BY edu
                    """
                    print(f"执行SQL: {edu_stats_sql}")
                    cursor.execute(edu_stats_sql)
                    edu_stats = cursor.fetchall()

                    # 数据来源统计
                    source_stats_sql = """
                        SELECT dataSource, COUNT(*) as count
                        FROM py_happiness_survey
                        GROUP BY dataSource
                    """
                    print(f"执行SQL: {source_stats_sql}")
                    cursor.execute(source_stats_sql)
                    source_stats = cursor.fetchall()

                    # 总记录数
                    total_sql = "SELECT COUNT(*) as total FROM py_happiness_survey"
                    print(f"执行SQL: {total_sql}")
                    cursor.execute(total_sql)
                    total = cursor.fetchone()['total']

                    return success({
                        "total": total,
                        "happinessStats": happiness_stats,
                        "genderStats": gender_stats,
                        "eduStats": edu_stats,
                        "sourceStats": source_stats
                    })

        except Exception as e:
            print(f"获取幸福感统计数据失败: {str(e)}")
            return error(f"获取幸福感统计数据失败: {str(e)}")
