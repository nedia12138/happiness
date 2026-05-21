#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
幸福感数据导入执行脚本
快速执行数据库初始化和数据导入流程
"""

import os

def main():
    """主执行函数"""
    print("=" * 60)
    print("幸福感数据集导入工具")
    print("=" * 60)

    # 检查数据文件是否存在
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    required_files = [

        'happiness_train_complete.csv',
        'happiness_test_complete.csv',
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(data_dir, file)):
            missing_files.append(file)

    if missing_files:
        print(f"[ERROR] 缺少必要的数据文件: {', '.join(missing_files)}")
        print(f"请确保数据文件位于 {data_dir} 目录下")
        sys.exit(1)

    print("[OK] 数据文件检查通过")

    # 检查数据库配置
    try:
        # 添加项目根目录到Python路径
        import sys
        project_root = os.path.dirname(os.path.dirname(__file__))
        sys.path.insert(0, project_root)

        from config.config import DB_CONFIG
        print("[OK] 数据库配置检查通过")
    except ImportError as e:
        print(f"[ERROR] 无法导入数据库配置: {e}")
        print("请确保 config/config.py 文件存在且路径正确")
        sys.exit(1)

    # 导入并运行数据清洗脚本
    try:
        print("\n开始执行数据库初始化与数据导入...")
        from Spider.data.data_cleaning_import import HappinessDataImporter

        importer = HappinessDataImporter()
        importer.run_import()

        print("\n" + "=" * 60)
        print("[SUCCESS] 数据库初始化与数据导入完成！")
        print("=" * 60)
        print("\n接下来您可以：")
        print("1. 查看数据库中的幸福感数据")
        print("2. 运行机器学习训练脚本")
        print("3. 启动系统查看调查列表和分析页面")


    except Exception as e:
        print(f"\n[ERROR] 数据库初始化失败: {e}")
        print("请查看 data_import.log 文件获取详细错误信息")
        sys.exit(1)

if __name__ == '__main__':
    main()
