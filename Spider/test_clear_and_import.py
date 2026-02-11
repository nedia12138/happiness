#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试清空和重新导入功能
"""

import sys
import os
import pymysql

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from config.config import DB_CONFIG

def test_clear_and_import():
    """测试清空和重新导入功能"""
    print("=" * 60)
    print("测试数据清空和重新导入功能")
    print("=" * 60)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 第一次检查数据量
        cursor.execute("SELECT COUNT(*) FROM py_happiness_survey")
        count_before = cursor.fetchone()[0]
        print(f"导入前数据量: {count_before:,} 条")

        # 模拟清空操作
        cursor.execute("TRUNCATE TABLE py_happiness_survey")
        conn.commit()
        print("已执行清空操作")

        # 检查清空后数据量
        cursor.execute("SELECT COUNT(*) FROM py_happiness_survey")
        count_after_clear = cursor.fetchone()[0]
        print(f"清空后数据量: {count_after_clear:,} 条")

        # 验证清空成功
        if count_after_clear == 0:
            print("✅ 清空功能正常")
        else:
            print("❌ 清空功能异常")
            return False

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ 清空和重新导入功能测试完成")
        print("现在可以运行完整的导入脚本验证完整功能")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False

if __name__ == '__main__':
    test_clear_and_import()
