import os
import pickle
import numpy as np

# 1. 核心亮点：直接从你的 manual_models.py 文件中导入类，彻底告别重复手写代码
try:
    from Predictive.manual_models import ManualRidgeRegression, ManualRandomForestRegressor
except ImportError:
    from manual_models import ManualRidgeRegression, ManualRandomForestRegressor

def main():
    print("\n" + "="*60)
    print("      【CGSS 幸福感双轨混合预测系统 - 生产环境】")
    print("="*60)

    # 2. 定位你训练好的模型文件 (对应你 simple_improved_training.py 里的保存路径)
    base_path = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_path, "models", "random_forest.pkl")

    if not os.path.exists(model_path):
        print(f"[系统错误] 找不到模型文件：{model_path}")
        print("请确认是否已经成功运行过 simple_improved_training.py")
        return


    print("[系统日志] 正在从本地加载 .pkl 模型快照...")
    with open(model_path, "rb") as f:
        artifact = pickle.load(f)
    ridge_model = ManualRidgeRegression.from_state(artifact["ridge_state"])
    rf_model = ManualRandomForestRegressor.from_state(artifact["forest_state"])
    hybrid_weight = artifact["hybrid_weight"]
    np.random.seed(2026)
    new_features = np.random.uniform(-1.5, 1.5, size=(1, 35))
    print(f"[数据接入] 成功提取待预测样本，特征维度校验: {new_features.shape[1]} 维")
    ridge_pred = np.clip(ridge_model.predict(new_features)[0], 1.0, 5.0)
    # 6.2 随机森林单轨预测 (约束在 1-5 分)
    rf_pred = np.clip(rf_model.predict(new_features)[0], 1.0, 5.0)
    print(f"[双轨运行] 随机森林 (RF) 输出分值:             {rf_pred:.2f} 分")
    print(f"[双轨运行] 岭回归 (Ridge) 输出分值:           {ridge_pred:.2f} 分")



    # 6.3 混合模型加权汇总
    hybrid_score = (hybrid_weight * ridge_pred) + ((1.0 - hybrid_weight) * rf_pred)
    print("-" * 60)
    print(f"[综合输出] 混合模型最终评估得分:             {hybrid_score:.2f} 分")

    # 7. 业务层级的文本研判
    if hybrid_score >= 4.0:
        level = "比较幸福"
    elif hybrid_score >= 3.0:
        level = "感觉一般"
    elif hybrid_score >= 2.0:
        level = "不太幸福"
    else:
        level = "非常不幸福"

    print(f"[研判结论] 该受访者的主观幸福感倾向判定为: 【{level}】")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()