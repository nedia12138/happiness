# 导入必要的工具库
# itertools：用于生成参数组合（网格搜索）
# json：用于保存训练报告等文本数据
# os：用于处理文件路径和目录创建
# pickle：用于序列化/反序列化模型（二进制保存）
# datetime：用于记录模型训练时间
import itertools
import json
import os
import pickle
from datetime import datetime

# 数值计算相关库
import numpy as np
# 数据处理核心库
import pandas as pd
#  sklearn 评估指标：平均绝对误差、均方误差、决定系数（R²）
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
#  sklearn 数据集拆分工具：划分训练/验证/测试集
from sklearn.model_selection import train_test_split
#  sklearn 预处理工具：鲁棒缩放器（对异常值不敏感）
from sklearn.preprocessing import RobustScaler

# 导入自定义的模型和配置（先尝试Predictive包导入，失败则本地导入）
try:
    from Predictive.manual_models import ManualRandomForestRegressor, ManualRidgeRegression
    from Predictive.prediction_schema import (
        FEATURE_COLUMNS,  # 特征列名列表（模型用到的输入特征）
        build_display_importances,  # 构建特征重要性展示格式
        build_scaler_state,  # 保存缩放器状态（方便后续预测复用）
        file_signature,  # 生成数据文件的签名（校验数据是否变化）
        prepare_model_features,  # 预处理特征（填充缺失值、选择列等）
    )
except ImportError:
    # 如果包导入失败，从本地文件导入
    from manual_models import ManualRandomForestRegressor, ManualRidgeRegression
    from prediction_schema import (
        FEATURE_COLUMNS,
        build_display_importances,
        build_scaler_state,
        file_signature,
        prepare_model_features,
    )

# 全局配置参数
SEED = 424  # 随机种子（保证实验可重复）
MODEL_NAME = "Manual Ensemble (Ridge + CART Forest)"  # 模型名称：手写融合模型（岭回归+决策树森林）

# 设置numpy随机种子，确保每次运行结果一致
np.random.seed(SEED)


def compute_metrics(y_true, y_pred):
    """
    计算回归模型的核心评估指标
    :param y_true: 真实值（标签）
    :param y_pred: 模型预测值
    :return: 包含R²、RMSE、MAE、MSE的字典
    指标说明：
    - R²（决定系数）：越接近1越好，代表模型能解释数据变异的比例
    - RMSE（均方根误差）：越小越好，反映预测值与真实值的平均偏差（和原数据同单位）
    - MAE（平均绝对误差）：越小越好，反映预测值与真实值的平均绝对偏差
    - MSE（均方误差）：越小越好，RMSE的平方，放大了大误差的影响
    """
    # 计算均方误差
    mse = mean_squared_error(y_true, y_pred)
    return {
        "r2": float(r2_score(y_true, y_pred)),  # R²得分
        "rmse": float(np.sqrt(mse)),  # 均方根误差（开平方还原量纲）
        "mae": float(mean_absolute_error(y_true, y_pred)),  # 平均绝对误差
        "mse": float(mse),  # 均方误差
    }


def is_better(candidate_metrics, current_metrics, tol=1e-4):
    """
    比较两组指标，判断候选模型是否更优（带容差，避免浮点误差）
    :param candidate_metrics: 候选模型的指标
    :param current_metrics: 当前最优模型的指标
    :param tol: 容差（微小差异视为无区别）
    :return: True=候选模型更优，False=不更优
    比较逻辑（优先级从高到低）：
    1. R²更高 → 更优
    2. R²相同（容差内）→ RMSE更低 → 更优
    3. RMSE相同（容差内）→ MAE更低 → 更优
    """
    # 如果当前没有最优模型，候选直接胜出
    if current_metrics is None:
        return True
    # R²显著更高 → 更优
    if candidate_metrics["r2"] > current_metrics["r2"] + tol:
        return True
    # R²显著更低 → 更差
    if candidate_metrics["r2"] < current_metrics["r2"] - tol:
        return False
    # R²差不多 → 看RMSE，显著更低则更优
    if candidate_metrics["rmse"] < current_metrics["rmse"] - tol:
        return True
    # RMSE显著更高 → 更差
    if candidate_metrics["rmse"] > current_metrics["rmse"] + tol:
        return False
    # R²和RMSE都差不多 → 看MAE，显著更低则更优
    return candidate_metrics["mae"] < current_metrics["mae"] - tol


def as_serializable_metrics(metrics):
    """
    将指标值转换为可序列化的格式（保留6位小数，避免浮点精度问题）
    :param metrics: 原始指标字典
    :return: 格式化后的指标字典
    """
    return {key: round(float(value), 6) for key, value in metrics.items()}


class SimpleImprovedModel:
    """
    手写融合模型训练类：岭回归 + 随机森林（CART）加权融合
    核心流程：
    1. 加载并预处理幸福感数据集
    2. 拆分训练/验证/测试集
    3. 网格搜索岭回归最优alpha参数
    4. 网格搜索随机森林最优超参数
    5. 搜索融合权重（岭回归预测值占比）
    6. 用最优参数在全量训练集（训练+验证）重训练
    7. 评估并保存模型、指标、报告
    """

    def __init__(self):
        """初始化类：设置文件路径、超参数搜索范围、创建目录"""
        # 当前脚本所在目录
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        # 数据集路径（幸福感训练数据）
        self.data_path = os.path.join(self.base_path, "..", "Spider", "data", "happiness_train_abbr.csv")
        # 模型保存目录
        self.model_dir = os.path.join(self.base_path, "models")
        # 模型二进制保存路径（pickle）
        self.model_path = os.path.join(self.model_dir, "random_forest.pkl")
        # 训练报告保存路径（json）
        self.training_report_path = os.path.join(self.model_dir, "training_report.json")
        # 模型信息保存路径（json）
        self.model_info_path = os.path.join(self.model_dir, "model_info.json")
        # 随机森林中决策树的最大阈值数（自定义参数）
        self.max_thresholds = 12

        # 岭回归超参数搜索范围（alpha：正则化强度，越大正则化越强）
        self.ridge_alphas = [0.1, 1, 5, 10, 20]
        # 随机森林超参数搜索网格
        self.forest_param_grid = {
            "n_estimators": [80, 120, 160],  # 决策树数量
            "max_depth": [8, 12, 16],  # 单棵树最大深度（防止过拟合）
            "min_samples_split": [10, 20],  # 节点分裂所需最小样本数
            "min_samples_leaf": [5, 10],  # 叶节点最小样本数
            "max_features": ["sqrt", 0.35],  # 每棵树考虑的特征数（sqrt=根号总特征数）
            "min_gain": [1e-6, 1e-4],  # 分裂所需最小信息增益
        }
        # 网格搜索阶段临时用的决策树数量（加速搜索，后续用完整数量）
        self.search_proxy_trees = 40
        # 网格搜索后筛选前K个最优结构参数（再细化搜索n_estimators）
        self.search_top_k = 3

        # 创建模型保存目录（如果不存在）
        os.makedirs(self.model_dir, exist_ok=True)

    def load_data(self):
        """
        加载并预处理原始数据集
        :return: 清洗后的DataFrame
        处理步骤：
        1. 读取CSV文件
        2. 转换happiness列为数值型（处理异常值）
        3. 过滤happiness在1-5之间的数据（幸福感评分范围）
        4. 重置索引
        """
        # 读取CSV文件，low_memory=False避免列类型警告，utf-8编码防止中文乱码
        df = pd.read_csv(self.data_path, low_memory=False, encoding="utf-8")
        # 将happiness列转为数值型，无法转换的设为NaN
        df["happiness"] = pd.to_numeric(df["happiness"], errors="coerce")
        # 过滤出幸福感评分在1-5之间的有效数据（copy避免警告）
        df = df[df["happiness"].between(1, 5)].copy()
        # 确保幸福感为浮点型（方便后续计算）
        df["happiness"] = df["happiness"].astype(float)
        # 重置索引（过滤后索引不连续）
        df.reset_index(drop=True, inplace=True)
        return df

    def split_data(self, df):
        """
        拆分数据集为训练集、验证集、测试集
        :param df: 清洗后的完整数据集
        :return: train_df（训练集）、valid_df（验证集）、test_df（测试集）
        拆分比例：
        - 总数据：测试集15%，剩余85%分为训练集+验证集
        - 训练集+验证集：验证集占85%中的~17.65% → 最终验证集占总数据15%，训练集70%
        stratify：按happiness分层抽样，保证各集的幸福感分布一致
        """
        # 第一步：拆分出测试集（15%），剩余85%为训练+验证集
        train_valid_df, test_df = train_test_split(
            df,
            test_size=0.15,  # 测试集占15%
            random_state=SEED,  # 随机种子保证可重复
            stratify=df["happiness"],  # 分层抽样
        )
        # 第二步：从训练+验证集中拆分出验证集（约17.65% → 总数据的15%）
        train_df, valid_df = train_test_split(
            train_valid_df,
            test_size=0.17647058823529413,  # 0.17647≈1/5.67 → 85%*17.65%≈15%
            random_state=SEED,
            stratify=train_valid_df["happiness"],
        )
        # 重置索引并返回
        return train_df.reset_index(drop=True), valid_df.reset_index(drop=True), test_df.reset_index(drop=True)

    def build_datasets(self, train_df, valid_df, test_df):
        """
        构建模型输入数据集（特征预处理、缩放）
        :param train_df: 训练集
        :param valid_df: 验证集
        :param test_df: 测试集
        :return: 包含特征、标签、缩放器的字典
        处理步骤：
        1. 预处理特征（填充缺失值、选择FEATURE_COLUMNS列）
        2. 用鲁棒缩放器标准化特征（对异常值不敏感）
        3. 提取标签（happiness）并转为numpy数组
        """
        # 预处理训练集特征，返回处理后的特征矩阵+缺失值填充值（用于验证/测试集）
        X_train_raw, fill_values = prepare_model_features(train_df)
        # 用训练集的填充值预处理验证集特征（避免数据泄露）
        X_valid_raw = prepare_model_features(valid_df, fill_values=fill_values)
        # 用训练集的填充值预处理测试集特征
        X_test_raw = prepare_model_features(test_df, fill_values=fill_values)

        # 初始化鲁棒缩放器（基于中位数和四分位数，抗异常值）
        scaler = RobustScaler()
        # 用训练集拟合缩放器并转换（只在训练集拟合，避免泄露）
        X_train = scaler.fit_transform(X_train_raw.values)
        # 用训练集的缩放器转换验证集
        X_valid = scaler.transform(X_valid_raw.values)
        # 用训练集的缩放器转换测试集
        X_test = scaler.transform(X_test_raw.values)

        # 返回处理后的所有数据
        return {
            "fill_values": fill_values,  # 缺失值填充值
            "scaler": scaler,  # 拟合后的缩放器
            "X_train": X_train,  # 训练集特征（缩放后）
            "X_valid": X_valid,  # 验证集特征（缩放后）
            "X_test": X_test,  # 测试集特征（缩放后）
            "y_train": train_df["happiness"].to_numpy(dtype=float),  # 训练集标签
            "y_valid": valid_df["happiness"].to_numpy(dtype=float),  # 验证集标签
            "y_test": test_df["happiness"].to_numpy(dtype=float),  # 测试集标签
        }

    def fit_ridge_grid(self, X_train, y_train, X_valid, y_valid):
        """
        网格搜索岭回归的最优alpha参数
        :param X_train: 训练集特征
        :param y_train: 训练集标签
        :param X_valid: 验证集特征
        :param y_valid: 验证集标签
        :return: 最优参数+模型+指标的字典
        逻辑：遍历所有alpha，训练模型，用验证集评估，选择最优
        """
        best = None  # 初始化最优结果
        print("-> 搜索手写 Ridge 线性回归最优 alpha...")
        # 遍历所有候选alpha值
        for alpha in self.ridge_alphas:
            # 初始化手写岭回归模型（自定义实现）
            model = ManualRidgeRegression(alpha=alpha)
            # 训练模型
            model.fit(X_train, y_train)
            # 预测验证集，并用clip限制预测值在1-5之间（幸福感评分范围）
            valid_pred = np.clip(model.predict(X_valid), 1, 5)
            # 计算验证集指标
            valid_metrics = compute_metrics(y_valid, valid_pred)
            # 如果当前是最优，更新best
            if best is None or is_better(valid_metrics, best["metrics"]):
                best = {"alpha": alpha, "model": model, "metrics": valid_metrics}
        return best

    def forest_structure_combinations(self):
        """
        生成随机森林结构参数的所有组合（除了n_estimators）
        :return: 迭代器，每个元素是参数字典
        """
        # 要组合的结构参数名
        structure_keys = ["max_depth", "min_samples_split", "min_samples_leaf", "max_features", "min_gain"]
        # 每个参数对应的候选值
        structure_values = [self.forest_param_grid[key] for key in structure_keys]
        # 生成所有参数组合（笛卡尔积）
        for values in itertools.product(*structure_values):
            yield dict(zip(structure_keys, values))

    def fit_forest_grid(self, X_train, y_train, X_valid, y_valid):
        """
        两阶段网格搜索随机森林最优参数：
        阶段1：用少量树（search_proxy_trees）筛选前K个最优结构参数
        阶段2：对前K个结构参数，遍历n_estimators，找到最优
        :param X_train: 训练集特征
        :param y_train: 训练集标签
        :param X_valid: 验证集特征
        :param y_valid: 验证集标签
        :return: 最优参数+模型+指标的字典
        """
        best = None  # 初始化最优结果
        # 获取所有结构参数组合
        structure_combinations = list(self.structure_combinations_proxy())
        shortlisted = []  # 临时存储阶段1的结果
        # 阶段1：快速筛选结构参数（用少量树加速）
        for params in structure_combinations:
            # 初始化随机森林（用临时树数量）
            model = ManualRandomForestRegressor(
                n_estimators=self.search_proxy_trees,  # 临时树数量
                **params,  # 结构参数
                max_thresholds=self.max_thresholds,  # 自定义阈值数
                random_state=SEED  # 随机种子
            )
            # 训练模型
            model.fit(X_train, y_train)
            # 预测并计算指标
            metrics = compute_metrics(y_valid, np.clip(model.predict(X_valid), 1, 5))
            # 保存参数和指标
            shortlisted.append({"params": params, "metrics": metrics})
        # 按R²降序排序，取前K个最优结构参数
        shortlisted.sort(key=lambda x: x["metrics"]["r2"], reverse=True)
        shortlisted = shortlisted[:self.search_top_k]
        # 阶段2：对前K个结构参数，遍历n_estimators找最优
        n_est_list = self.forest_param_grid["n_estimators"]  # 树数量候选值
        for item in shortlisted:
            # 遍历所有树数量
            for n in n_est_list:
                # 复制结构参数，添加n_estimators
                p = dict(item["params"])
                p["n_estimators"] = n
                # 初始化完整模型
                m = ManualRandomForestRegressor(
                    **p,
                    max_thresholds=self.max_thresholds,
                    random_state=SEED
                )
                # 训练模型
                m.fit(X_train, y_train)
                # 预测并计算指标
                met = compute_metrics(y_valid, np.clip(m.predict(X_valid), 1, 5))
                # 更新最优结果
                if best is None or is_better(met, best["metrics"]):
                    best = {"params": p, "model": m, "metrics": met}
        return best

    def structure_combinations_proxy(self):
        """兼容方法：代理调用forest_structure_combinations"""
        return self.forest_structure_combinations()

    def search_hybrid_weight(self, y_valid, lr_pred, rf_pred):
        """
        搜索融合权重：岭回归预测值的权重（0~1），剩余权重给随机森林
        :param y_valid: 验证集真实标签
        :param lr_pred: 岭回归验证集预测值
        :param rf_pred: 随机森林验证集预测值
        :return: 最优权重+指标的字典
        逻辑：遍历0~1的权重（步长0.05），计算融合预测的指标，选最优
        """
        best = None  # 初始化最优结果
        # 遍历权重（0.0到1.0，步长0.05，共21个值）
        for weight in np.arange(0.0, 1.0001, 0.05):
            # 融合预测：weight*岭回归 + (1-weight)*随机森林，限制在1-5
            hybrid_pred = np.clip(weight * lr_pred + (1.0 - weight) * rf_pred, 1, 5)
            # 计算融合后的指标
            metrics = compute_metrics(y_valid, hybrid_pred)
            # 更新最优权重
            if best is None or is_better(metrics, best["metrics"]):
                best = {"weight": round(float(weight), 2), "metrics": metrics}
        return best

    def refit_final_models(self, train_df, valid_df, test_df, ridge_alpha, forest_params):
        """
        用最优参数在全量训练集（训练+验证）重训练模型
        :param train_df: 原始训练集
        :param valid_df: 原始验证集
        :param test_df: 测试集
        :param ridge_alpha: 岭回归最优alpha
        :param forest_params: 随机森林最优参数
        :return: 重训练后的模型、数据、预测值字典
        逻辑：
        1. 合并训练+验证集（充分利用数据）
        2. 重新预处理特征（基于全量训练集）
        3. 训练岭回归和随机森林
        4. 生成训练集和测试集的预测值
        """
        # 合并训练集和验证集作为最终训练集
        final_train_df = pd.concat([train_df, valid_df], ignore_index=True)
        # 预处理全量训练集特征
        X_final_raw, fill_values = prepare_model_features(final_train_df)
        # 预处理测试集特征（用全量训练集的填充值）
        X_test_raw = prepare_model_features(test_df, fill_values=fill_values)

        # 重新拟合缩放器（基于全量训练集）
        scaler = RobustScaler()
        X_final = scaler.fit_transform(X_final_raw.values)
        X_test = scaler.transform(X_test_raw.values)

        # 提取标签
        y_final = final_train_df["happiness"].to_numpy(dtype=float)
        y_test = test_df["happiness"].to_numpy(dtype=float)

        # 训练最终的岭回归模型
        ridge = ManualRidgeRegression(alpha=ridge_alpha)
        ridge.fit(X_final, y_final)

        # 训练最终的随机森林模型
        forest = ManualRandomForestRegressor(
            **forest_params,
            max_thresholds=self.max_thresholds,
            random_state=SEED
        )
        forest.fit(X_final, y_final)

        # 生成训练集预测值（用于评估）
        ridge_pred_train = np.clip(ridge.predict(X_final), 1, 5)
        forest_pred_train = np.clip(forest.predict(X_final), 1, 5)

        # 生成测试集预测值（用于评估）
        ridge_pred_test = np.clip(ridge.predict(X_test), 1, 5)
        forest_pred_test = np.clip(forest.predict(X_test), 1, 5)

        # 返回所有结果
        return {
            "fill_values": fill_values,  # 缺失值填充值
            "scaler": scaler,  # 拟合后的缩放器
            "ridge": ridge,  # 最终岭回归模型
            "forest": forest,  # 最终随机森林模型
            "y_train": y_final,  # 全量训练集标签
            "y_test": y_test,  # 测试集标签
            "ridge_pred_train": ridge_pred_train,  # 岭回归训练集预测值
            "forest_pred_train": forest_pred_train,  # 随机森林训练集预测值
            "ridge_pred_test": ridge_pred_test,  # 岭回归测试集预测值
            "forest_pred_test": forest_pred_test,  # 随机森林测试集预测值
            "train_rows": len(final_train_df),  # 训练集行数
            "test_rows": len(test_df),  # 测试集行数
        }

    def save_artifacts(self, artifact, report):
        """
        保存模型相关文件（序列化模型、训练报告、模型信息）
        :param artifact: 模型完整信息（参数、状态、指标等）
        :param report: 训练报告（指标汇总）
        """
        # 保存模型二进制文件（pickle）
        with open(self.model_path, "wb") as file_obj:
            pickle.dump(artifact, file_obj)
        # 保存训练报告（json，易读）
        with open(self.training_report_path, "w", encoding="utf-8") as file_obj:
            json.dump(report, file_obj, ensure_ascii=False, indent=2)
        # 构建模型信息（简化版，用于展示）
        model_info = {
            "model_name": artifact["model_name"],  # 模型名称
            "description": "手写 线性 + 手写 CART 随机森林融合模型",  # 模型描述
            "feature_importances": artifact["display_importances"],  # 特征重要性
            "hybrid_weight": artifact["hybrid_weight"],  # 融合权重
            "metrics": report["test_metrics"],  # 测试集指标
        }
        # 保存模型信息（json）
        with open(self.model_info_path, "w", encoding="utf-8") as file_obj:
            json.dump(model_info, file_obj, ensure_ascii=False, indent=2)

    def run(self):
        """
        主训练流程（入口函数）
        完整流程：
        1. 加载数据 → 2. 拆分数据集 → 3. 预处理特征 → 4. 搜索最优参数 →
        5. 重训练最终模型 → 6. 评估融合模型 → 7. 保存结果
        """
        print("-> 启动手写幸福感预测训练流程")
        # 1. 加载清洗数据
        df = self.load_data()
        # 2. 拆分训练/验证/测试集
        train_df, valid_df, test_df = self.split_data(df)
        # 3. 预处理特征，构建模型输入
        datasets = self.build_datasets(train_df, valid_df, test_df)

        # 4. 超参数搜索
        # 4.1 搜索岭回归最优alpha
        ridge_search = self.fit_ridge_grid(
            datasets["X_train"], datasets["y_train"],
            datasets["X_valid"], datasets["y_valid"]
        )
        # 4.2 搜索随机森林最优参数
        forest_search = self.fit_forest_grid(
            datasets["X_train"], datasets["y_train"],
            datasets["X_valid"], datasets["y_valid"]
        )
        # 4.3 生成验证集预测值，用于搜索融合权重
        valid_lr_pred = np.clip(ridge_search["model"].predict(datasets["X_valid"]), 1, 5)
        valid_rf_pred = np.clip(forest_search["model"].predict(datasets["X_valid"]), 1, 5)
        # 4.4 搜索最优融合权重
        hybrid_search = self.search_hybrid_weight(datasets["y_valid"], valid_lr_pred, valid_rf_pred)

        # 5. 用最优参数在全量训练集（训练+验证）重训练
        final = self.refit_final_models(
            train_df, valid_df, test_df,
            ridge_search["alpha"], forest_search["params"]
        )
        # 获取最优融合权重
        w = hybrid_search["weight"]

        # 6. 计算融合模型的预测值和指标
        # 6.1 训练集融合预测
        hybrid_pred_train = np.clip(
            w * final["ridge_pred_train"] + (1.0 - w) * final["forest_pred_train"],
            1, 5
        )
        # 6.2 测试集融合预测
        hybrid_pred_test = np.clip(
            w * final["ridge_pred_test"] + (1.0 - w) * final["forest_pred_test"],
            1, 5
        )

        # 6.3 计算各模型的训练集指标
        train_metrics = {
            "ridge": compute_metrics(final["y_train"], final["ridge_pred_train"]),
            "forest": compute_metrics(final["y_train"], final["forest_pred_train"]),
            "hybrid": compute_metrics(final["y_train"], hybrid_pred_train),
        }
        # 6.4 计算各模型的测试集指标
        test_metrics = {
            "ridge": compute_metrics(final["y_test"], final["ridge_pred_test"]),
            "forest": compute_metrics(final["y_test"], final["forest_pred_test"]),
            "hybrid": compute_metrics(final["y_test"], hybrid_pred_test),
        }

        # 6.5 格式化打印指标对比（方便查看）
        print("\n" + "=" * 90)
        print(f"| {'算法模型':<18} | {'数据集':<10} | {'R2 (↑)':<12} | {'RMSE (↓)':<12} | {'MAE (↓)':<12} |")
        print("-" * 90)
        for name in ["ridge", "forest", "hybrid"]:
            tr, te = train_metrics[name], test_metrics[name]
            # 打印训练集指标
            print(
                f"| {name.capitalize():<18} | {'训练集':<10} | {tr['r2']:<12.4f} | {tr['rmse']:<12.4f} | {tr['mae']:<12.4f} |")
            # 打印测试集指标
            print(f"| {'':<18} | {'测试集':<10} | {te['r2']:<12.4f} | {te['rmse']:<12.4f} | {te['mae']:<12.4f} |")
            print("-" * 90)
        print("=" * 90)

        # 7. 构建保存的artifact和report，保存文件
        # 7.1 构建特征重要性展示格式
        display_importances = build_display_importances(FEATURE_COLUMNS, final["forest"].feature_importances_)
        # 7.2 构建完整的模型artifact（包含所有必要信息）
        artifact = {
            "version": 2,  # 模型版本
            "model_name": MODEL_NAME,  # 模型名称
            "created_at": datetime.now().isoformat(timespec="seconds"),  # 训练时间
            "feature_columns": FEATURE_COLUMNS,  # 特征列名
            "fill_values": {k: float(v) for k, v in final["fill_values"].items()},  # 缺失值填充值
            "scaler_state": build_scaler_state(final["scaler"]),  # 缩放器状态
            "ridge_state": final["ridge"].to_state(),  # 岭回归模型状态
            "forest_state": final["forest"].to_state(),  # 随机森林模型状态
            "hybrid_weight": w,  # 融合权重
            "test_metrics": {n: as_serializable_metrics(m) for n, m in test_metrics.items()},  # 测试集指标
            "best_params": {"ridge_alpha": ridge_search["alpha"], "forest": forest_search["params"]},  # 最优参数
            "display_importances": display_importances,  # 特征重要性
            "data_signature": file_signature(self.data_path),  # 数据文件签名
        }
        # 7.3 构建训练报告
        report = {
            "model_name": MODEL_NAME,
            "created_at": artifact["created_at"],
            "test_metrics": artifact["test_metrics"],
            "train_metrics": {n: as_serializable_metrics(m) for n, m in train_metrics.items()}
        }
        # 7.4 保存所有文件
        self.save_artifacts(artifact, report)
        # 打印完成信息
        print(f"\n✅ 训练完成。最优参数: Alpha={ridge_search['alpha']}, Weight={w}")



# 主程序入口：当脚本直接运行时，执行训练流程
if __name__ == "__main__":
    SimpleImprovedModel().run()