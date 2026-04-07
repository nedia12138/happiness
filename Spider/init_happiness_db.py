#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的幸福感数据库初始化入口。
"""

from data_cleaning_import import HappinessDataImporter


def main():
    importer = HappinessDataImporter()
    importer.run_import()


if __name__ == "__main__":
    main()
