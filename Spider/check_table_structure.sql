-- 检查完整版表结构
DESCRIBE py_happiness_survey_complete;

-- 检查是否有minorChild字段
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'py_happiness_survey_complete'
AND COLUMN_NAME = 'minorChild';

-- 显示所有字段名（按字典序）
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'py_happiness_survey_complete'
ORDER BY COLUMN_NAME;
