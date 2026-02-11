#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试字段映射问题
"""

import pandas as pd
import os

def check_field_mapping():
    """检查字段映射是否完整"""

    data_dir = os.path.join(os.path.dirname(__file__), 'data')

    # 读取完整版数据
    train_file = os.path.join(data_dir, 'happiness_train_complete.csv')
    if not os.path.exists(train_file):
        print("完整版训练数据文件不存在")
        return

    # 尝试多种编码
    encodings_to_try = ['utf-8', 'gbk', 'gb2312']
    df = None

    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(train_file, nrows=5, encoding=encoding)  # 只读取前5行来检查列名
            print(f"成功使用 {encoding} 编码读取数据")
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        print("无法读取完整版数据文件")
        return

    print(f"\n完整版数据列数: {len(df.columns)}")
    print("完整版数据列名:")
    for i, col in enumerate(df.columns, 1):
        print("2d")

    # 定义的映射字典
    field_mapping_complete = {
        'survey_type': 'surveyType',
        'survey_time': 'surveyTime',
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
        'social_outing': 'socialOuting',
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
        'house': 'house',
        'car': 'car',
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
        'son': 'son',
        'daughter': 'daughter',
        'minor_child': 'minorChild',
        'marital': 'marital',
        'marital_1st': 'marital1st',
        's_birth': 'sBirth',
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
        'view': 'view',
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

    # 检查哪些字段没有映射
    mapped_columns = set()
    for csv_field in df.columns:
        if csv_field in field_mapping_complete:
            mapped_columns.add(field_mapping_complete[csv_field])
        else:
            mapped_columns.add(csv_field)  # 如果没有映射，保持原名

    print(f"\n映射后的列数: {len(mapped_columns)}")
    print("\n前20个映射后的列名:")
    for i, col in enumerate(sorted(mapped_columns), 1):
        if i <= 20:
            print("2d")
        elif i == 21:
            print("    ...")

    # 特别检查religion_freq
    if 'religion_freq' in df.columns:
        print(f"\n[INFO] religion_freq 字段存在于数据中")
        if 'religion_freq' in field_mapping_complete:
            print(f"[INFO] religion_freq 映射到: {field_mapping_complete['religion_freq']}")
        else:
            print("[ERROR] religion_freq 没有映射!")
    else:
        print("[INFO] religion_freq 字段不存在于数据中")

    # 检查可能缺失的映射
    missing_mappings = []
    for col in df.columns:
        if col not in field_mapping_complete and col not in ['id', 'happiness', 'nationality', 'religion', 'political', 'income', 'data_source', 'province', 'city', 'county', 'gender', 'birth', 'edu', 'floor_area', 'height_cm', 'weight_jin', 'health', 'health_problem', 'depression', 'hukou', 'socialize', 'relax', 'learn', 'equity', 'class', 'work_exper', 'work_status', 'work_yr', 'work_type', 'work_manage', 'family_m', 'family_status', 'house', 'car', 'marital', 'status_peer', 'status_3_before', 'view', 'inc_ability', 'survey_time']:
            missing_mappings.append(col)

    if missing_mappings:
        print(f"\n[WARNING] 可能缺失的字段映射: {len(missing_mappings)} 个")
        for col in missing_mappings[:10]:  # 只显示前10个
            print(f"    - {col}")
        if len(missing_mappings) > 10:
            print(f"    ... 还有 {len(missing_mappings) - 10} 个")
    else:
        print("\n[OK] 所有字段都有映射")

if __name__ == '__main__':
    check_field_mapping()
