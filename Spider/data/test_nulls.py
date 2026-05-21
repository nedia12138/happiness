import pandas as pd
import numpy as np

# # 1. 读取你的真实训练集 (路径换成你实际的csv名字，比
# df = pd.read_csv("/Users/nan/Desktop/paper/happiness/Spider/data/happiness_train_complete.csv")
df = pd.read_csv("/Users/nan/Desktop/paper/happiness/Spider/data/happiness_train_complete.csv", encoding="gbk")
# 2. 模拟你 prediction_schema.py 里的拦截机制
MISSING_SENTINELS = [-8, -3, -2, -1]
df.replace(MISSING_SENTINELS, np.nan, inplace=True)

print(f"\n✅ 全表真实缺失值总数: {df.isnull().sum().sum()} 个")
print("\n✅ 具体是哪些列缺失了 (以及缺失数量):")
missing_stats = df.isnull().sum()
print(missing_stats[missing_stats > 0])