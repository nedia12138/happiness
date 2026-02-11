#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单比较数据字段和数据库表字段
"""

import pandas as pd
import os

def simple_compare():
    """简单比较字段"""

    # 从SQL文件提取的完整版表字段名（手动整理）
    db_fields = {
        'id', 'happiness', 'surveyType', 'province', 'city', 'county', 'surveyTime', 'gender', 'birth',
        'nationality', 'religion', 'religionFreq', 'edu', 'eduOther', 'eduStatus', 'eduYr', 'income',
        'political', 'joinParty', 'floorArea', 'property0', 'property1', 'property2', 'property3',
        'property4', 'property5', 'property6', 'property7', 'property8', 'propertyOther', 'heightCm',
        'weightJin', 'health', 'healthProblem', 'depression', 'hukou', 'hukouLoc', 'media1', 'media2',
        'media3', 'media4', 'media5', 'media6', 'leisure1', 'leisure2', 'leisure3', 'leisure4', 'leisure5',
        'leisure6', 'leisure7', 'leisure8', 'leisure9', 'leisure10', 'leisure11', 'leisure12', 'socialize',
        'relax', 'learn', 'socialNeighbor', 'socialFriend', 'socialOuting', 'equity', 'class', 'class10Before',
        'class10After', 'class14', 'workExper', 'workStatus', 'workYr', 'workType', 'workManage', 'insur1',
        'insur2', 'insur3', 'insur4', 'familyIncome', 'familyM', 'familyStatus', 'house', 'car', 'invest0',
        'invest1', 'invest2', 'invest3', 'invest4', 'invest5', 'invest6', 'invest7', 'invest8', 'investOther',
        'son', 'daughter', 'minorChild', 'marital', 'marital1st', 'sBirth', 'maritalNow', 'sEdu', 'sPolitical',
        'sHukou', 'sIncome', 'sWorkExper', 'sWorkStatus', 'sWorkType', 'fBirth', 'fEdu', 'fPolitical', 'fWork14',
        'mBirth', 'mEdu', 'mPolitical', 'mWork14', 'statusPeer', 'status3Before', 'view', 'incAbility', 'incExp',
        'trust1', 'trust2', 'trust3', 'trust4', 'trust5', 'trust6', 'trust7', 'trust8', 'trust9', 'trust10',
        'trust11', 'trust12', 'trust13', 'neighborFamiliarity', 'publicService1', 'publicService2', 'publicService3',
        'publicService4', 'publicService5', 'publicService6', 'publicService7', 'publicService8', 'publicService9',
        'dataSource', 'createTime', 'updateTime'
    }

    print(f"数据库表字段数: {len(db_fields)}")

    # 读取数据字段
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    train_file = os.path.join(data_dir, 'happiness_train_complete.csv')

    encodings_to_try = ['utf-8', 'gbk', 'gb2312']
    df = None

    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(train_file, nrows=1, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取数据")
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        print("无法读取数据文件")
        return

    data_fields = set(df.columns)
    print(f"数据文件字段数: {len(data_fields)}")

    # 创建字段映射
    field_mapping = {
        'survey_type': 'surveyType',
        'survey_time': 'surveyTime',
        'religion_freq': 'religionFreq',
        'edu_other': 'eduOther',
        'edu_status': 'eduStatus',
        'edu_yr': 'eduYr',
        'join_party': 'joinParty',
        'floor_area': 'floorArea',
        'property_0': 'property0',
        'property_1': 'property1',
        'property_2': 'property2',
        'property_3': 'property3',
        'property_4': 'property4',
        'property_5': 'property5',
        'property_6': 'property6',
        'property_7': 'property7',
        'property_8': 'property8',
        'property_other': 'propertyOther',
        'height_cm': 'heightCm',
        'weight_jin': 'weightJin',
        'health_problem': 'healthProblem',
        'hukou_loc': 'hukouLoc',
        'media_1': 'media1',
        'media_2': 'media2',
        'media_3': 'media3',
        'media_4': 'media4',
        'media_5': 'media5',
        'media_6': 'media6',
        'leisure_1': 'leisure1',
        'leisure_2': 'leisure2',
        'leisure_3': 'leisure3',
        'leisure_4': 'leisure4',
        'leisure_5': 'leisure5',
        'leisure_6': 'leisure6',
        'leisure_7': 'leisure7',
        'leisure_8': 'leisure8',
        'leisure_9': 'leisure9',
        'leisure_10': 'leisure10',
        'leisure_11': 'leisure11',
        'leisure_12': 'leisure12',
        'social_neighbor': 'socialNeighbor',
        'social_friend': 'socialFriend',
        'socia_outing': 'socialOuting',
        'class_10_before': 'class10Before',
        'class_10_after': 'class10After',
        'class_14': 'class14',
        'work_exper': 'workExper',
        'work_status': 'workStatus',
        'work_yr': 'workYr',
        'work_type': 'workType',
        'work_manage': 'workManage',
        'insur_1': 'insur1',
        'insur_2': 'insur2',
        'insur_3': 'insur3',
        'insur_4': 'insur4',
        'family_income': 'familyIncome',
        'family_m': 'familyM',
        'family_status': 'familyStatus',
        'invest_0': 'invest0',
        'invest_1': 'invest1',
        'invest_2': 'invest2',
        'invest_3': 'invest3',
        'invest_4': 'invest4',
        'invest_5': 'invest5',
        'invest_6': 'invest6',
        'invest_7': 'invest7',
        'invest_8': 'invest8',
        'invest_other': 'investOther',
        'minor_child': 'minorChild',
        'marital_1st': 'marital1st',
        's_birth': 'sBirth',
        'marital_now': 'maritalNow',
        's_edu': 'sEdu',
        's_political': 'sPolitical',
        's_hukou': 'sHukou',
        's_income': 'sIncome',
        's_work_exper': 'sWorkExper',
        's_work_status': 'sWorkStatus',
        's_work_type': 'sWorkType',
        'f_birth': 'fBirth',
        'f_edu': 'fEdu',
        'f_political': 'fPolitical',
        'f_work_14': 'fWork14',
        'm_birth': 'mBirth',
        'm_edu': 'mEdu',
        'm_political': 'mPolitical',
        'm_work_14': 'mWork14',
        'status_peer': 'statusPeer',
        'status_3_before': 'status3Before',
        'inc_ability': 'incAbility',
        'inc_exp': 'incExp',
        'trust_1': 'trust1',
        'trust_2': 'trust2',
        'trust_3': 'trust3',
        'trust_4': 'trust4',
        'trust_5': 'trust5',
        'trust_6': 'trust6',
        'trust_7': 'trust7',
        'trust_8': 'trust8',
        'trust_9': 'trust9',
        'trust_10': 'trust10',
        'trust_11': 'trust11',
        'trust_12': 'trust12',
        'trust_13': 'trust13',
        'neighbor_familiarity': 'neighborFamiliarity',
        'public_service_1': 'publicService1',
        'public_service_2': 'publicService2',
        'public_service_3': 'publicService3',
        'public_service_4': 'publicService4',
        'public_service_5': 'publicService5',
        'public_service_6': 'publicService6',
        'public_service_7': 'publicService7',
        'public_service_8': 'publicService8',
        'public_service_9': 'publicService9',
        'data_source': 'dataSource'
    }

    # 应用映射后的字段名
    mapped_data_fields = set()
    for col in data_fields:
        if col in field_mapping:
            mapped_data_fields.add(field_mapping[col])
        else:
            mapped_data_fields.add(col)  # 没有映射的保持原名

    # 找出不匹配的字段
    missing_in_db = mapped_data_fields - db_fields
    missing_in_data = db_fields - mapped_data_fields

    print(f"\n映射后的数据字段数: {len(mapped_data_fields)}")

    if missing_in_db:
        print(f"\n[ERROR] 数据中有但数据库表中没有的字段 ({len(missing_in_db)} 个):")
        for col in sorted(missing_in_db):
            print(f"  - {col}")
    else:
        print("\n[OK] 所有数据字段都有对应的数据库字段")

    if missing_in_data:
        print(f"\n[INFO] 数据库表中有但数据中没有的字段 ({len(missing_in_data)} 个):")
        for col in sorted(list(missing_in_data)[:10]):  # 只显示前10个
            print(f"  - {col}")
        if len(missing_in_data) > 10:
            print(f"  ... 还有 {len(missing_in_data) - 10} 个")

if __name__ == '__main__':
    simple_compare()
