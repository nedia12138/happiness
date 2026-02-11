# 幸福感数据集导入指南

## ✅ 导入结果验证

**最新导入状态：**
- ✅ **简化版数据**：10,968 条记录 (训练集8,000 + 测试集2,968)
- ✅ **完整版数据**：8,000 条记录 (训练集)
- ✅ **字段映射**：140个字段全部正确映射
- ✅ **数据质量**：通过完整的缺失值处理和异常值过滤
- ✅ **执行时间**：5.79秒

## 概述

本目录包含幸福感调查数据集的清洗和导入工具，用于将原始CSV数据导入MySQL数据库。

## 文件说明

- `data/` - 原始数据集目录
  - `happiness_train_abbr.csv` - 训练集简化版 (8,000行 × 42列)
  - `happiness_test_abbr.csv` - 测试集简化版 (2,968行 × 41列)
  - `happiness_train_complete.csv` - 训练集完整版 (8,000行 × 107列)
  - `happiness_test_complete.csv` - 测试集完整版 (2,968行 × 106列)
  - `happiness_index.xlsx` - 幸福指数相关数据

- `data_cleaning_import.py` - 数据清洗和导入主脚本
- `README_data_import.md` - 本说明文件

## 数据库表结构

### 1. py_happiness_survey (简化版)
包含核心42个特征字段，用于基础的幸福感预测分析。

**关键字段：**
- `id` - 原始数据ID
- `happiness` - 幸福感评分 (1-5, -8未知)
- `gender` - 性别 (1男2女)
- `birth` - 出生年份
- `edu` - 教育水平
- `income` - 个人收入
- `marital` - 婚姻状况
- `province/city/county` - 地理位置
- `data_source` - 数据来源 (train/test)

### 2. py_happiness_survey_complete (完整版)
包含所有107个特征字段，用于深度分析和高级建模。

### 3. py_happiness_prediction (预测结果表)
存储机器学习模型的预测结果。

### 4. py_happiness_model_metrics (模型评估表)
存储模型性能评估指标。

## 数据清洗规则

### 数据导入策略
- **先清空后导入**：每次运行脚本前会自动清空目标表，防止数据重复
- **幂等性保证**：脚本可重复运行，结果始终一致

### 数值字段处理
- 空值处理：NaN, null, 空字符串 → NULL
- 负值处理：负数通常表示缺失数据 → NULL
- 类型转换：统一转换为适当的数值类型

### 字符串字段处理
- 去除前后空格
- 超长截断
- 特殊值过滤

### 数据质量保证
- 移除完全为空的记录
- 保持数据类型一致性
- 批量处理避免内存溢出
- 完整的事务控制和错误回滚

## 使用方法

### 1. 环境准备

确保已安装所需依赖：
```bash
pip install pandas numpy pymysql
```

### 2. 数据库准备

首先执行数据库表创建脚本：
```bash
mysql -u root -p < ../sql/happiness_dataset_tables.sql
```

### 3. 运行数据导入

```bash
# 在Spider目录下执行
python data_cleaning_import.py
```

**注意**：脚本会自动清空现有数据再重新导入，可重复运行而不会产生重复数据。

### 4. 验证导入结果

```sql
-- 检查导入的数据量
SELECT data_source, COUNT(*) as count
FROM py_happiness_survey
GROUP BY data_source;

-- 检查数据质量
SELECT
    COUNT(*) as total_records,
    SUM(CASE WHEN happiness IS NULL THEN 1 ELSE 0 END) as missing_happiness,
    AVG(happiness) as avg_happiness,
    MIN(income) as min_income,
    MAX(income) as max_income
FROM py_happiness_survey
WHERE data_source = 'train';
```

## 数据分析示例

### 幸福感分布分析
```sql
SELECT happiness, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM py_happiness_survey
WHERE data_source = 'train' AND happiness > 0
GROUP BY happiness
ORDER BY happiness;
```

### 人口统计分析
```sql
SELECT
    CASE gender WHEN 1 THEN '男' WHEN 2 THEN '女' ELSE '未知' END as gender,
    COUNT(*) as count,
    ROUND(AVG(happiness), 2) as avg_happiness
FROM py_happiness_survey
WHERE data_source = 'train' AND happiness > 0
GROUP BY gender;
```

### 教育水平与幸福感关系
```sql
SELECT
    CASE edu
        WHEN 1 THEN '文盲' WHEN 2 THEN '小学' WHEN 3 THEN '初中'
        WHEN 4 THEN '高中' WHEN 5 THEN '大专' WHEN 6 THEN '本科'
        WHEN 7 THEN '硕士' WHEN 8 THEN '博士' ELSE '其他'
    END as education,
    COUNT(*) as count,
    ROUND(AVG(happiness), 2) as avg_happiness
FROM py_happiness_survey
WHERE data_source = 'train' AND happiness > 0 AND edu IS NOT NULL
GROUP BY edu
ORDER BY edu;
```

## 注意事项

1. **内存管理**: 大文件采用分批处理，避免内存溢出
2. **编码问题**: 完整版数据可能存在编码问题，已在脚本中处理
3. **数据一致性**: 导入过程中会进行数据校验和清洗
4. **索引优化**: 自动创建常用查询的索引以提高性能
5. **日志记录**: 完整的执行日志保存在 `data_import.log` 文件中

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置是否正确
   - 确认MySQL服务正在运行

2. **内存不足**
   - 减小 `batch_size` 参数
   - 分批处理大文件

3. **编码错误**
   - 脚本已处理常见编码问题
   - 如仍有问题，可手动指定文件编码

4. **导入中断**
   - 查看日志文件定位错误
   - 可重新运行，脚本会自动清空并重新导入数据

5. **字段映射错误**
   - **问题**：`Unknown column 'xxx' in 'field list'`
   - **原因**：CSV字段名与数据库字段名不匹配
   - **解决**：检查字段映射字典，确保所有字段都有对应映射
   - **验证**：运行调试脚本检查字段匹配情况

6. **编码问题**
   - **问题**：完整版数据编码读取失败
   - **解决**：脚本自动尝试多种编码(UTF-8, GBK, GB2312等)
   - **状态**：已自动解决，支持多种编码格式

7. **索引创建警告**
   - **现象**：日志显示"创建索引失败"但实际是正常现象
   - **原因**：脚本会检查索引是否已存在，如果存在就跳过创建
   - **状态**：✅ 已解决，现在会正确显示"索引 xxx 已存在，跳过"

8. **重复运行**
   - 脚本支持重复运行，每次都会先清空数据再重新导入
   - 适合数据更新或测试场景

## 技术支持

如遇到问题，请查看：
1. `data_import.log` 日志文件
2. 数据库错误日志
3. 脚本运行时的控制台输出
