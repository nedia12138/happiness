import pymysql

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12121212',
    'database': '0_80123xingfuganwajue',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def check_data():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()

        # 检查happiness字段
        cursor.execute('SELECT happiness, COUNT(*) as count FROM py_happiness_survey WHERE dataSource="train" GROUP BY happiness ORDER BY happiness LIMIT 10')
        results = cursor.fetchall()
        print("Happiness values distribution (simplified table):")
        for row in results:
            print(f"  {row['happiness']}: {row['count']} records")

        # 检查完整版表
        cursor.execute('SELECT happiness, COUNT(*) as count FROM py_happiness_survey_complete WHERE dataSource="train" GROUP BY happiness ORDER BY happiness LIMIT 10')
        results = cursor.fetchall()
        print("\nHappiness values distribution (complete table):")
        for row in results:
            print(f"  {row['happiness']}: {row['count']} records")

        # 检查数据类型
        cursor.execute('DESCRIBE py_happiness_survey')
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            print(f"  {col['Field']}: {col['Type']} ({col['Null']})")

        # 检查一些样本数据
        cursor.execute('SELECT id, happiness, edu, income, health, birth, gender FROM py_happiness_survey WHERE dataSource="train" LIMIT 10')
        samples = cursor.fetchall()
        print("\nSample data:")
        for sample in samples:
            print(f"  ID: {sample['id']}, happiness: {sample['happiness']}, edu: {sample['edu']}, income: {sample['income']}, health: {sample['health']}, birth: {sample['birth']}, gender: {sample['gender']}")

        # 检查NULL值统计
        cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN birth IS NULL THEN 1 ELSE 0 END) as birth_null, SUM(CASE WHEN income IS NULL THEN 1 ELSE 0 END) as income_null FROM py_happiness_survey WHERE dataSource="train"')
        null_stats = cursor.fetchone()
        print(f"\nNULL值统计: 总记录数={null_stats['total']}, birth NULL={null_stats['birth_null']}, income NULL={null_stats['income_null']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_data()
