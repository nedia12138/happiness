import itertools
import json
import os
import pickle
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

try:
    from Predictive.manual_models import ManualRandomForestRegressor, ManualRidgeRegression
    from Predictive.prediction_schema import (
        FEATURE_COLUMNS,
        build_display_importances,
        build_scaler_state,
        file_signature,
        prepare_model_features,
    )
except ImportError:
    from manual_models import ManualRandomForestRegressor, ManualRidgeRegression
    from prediction_schema import (
        FEATURE_COLUMNS,
        build_display_importances,
        build_scaler_state,
        file_signature,
        prepare_model_features,
    )

SEED = 424
MODEL_NAME = "Manual Ensemble (Ridge + CART Forest)"

np.random.seed(SEED)


def compute_metrics(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "rmse": float(np.sqrt(mse)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mse": float(mse),
    }


def is_better(candidate_metrics, current_metrics, tol=1e-4):
    if current_metrics is None:
        return True
    if candidate_metrics["r2"] > current_metrics["r2"] + tol:
        return True
    if candidate_metrics["r2"] < current_metrics["r2"] - tol:
        return False
    if candidate_metrics["rmse"] < current_metrics["rmse"] - tol:
        return True
    if candidate_metrics["rmse"] > current_metrics["rmse"] + tol:
        return False
    return candidate_metrics["mae"] < current_metrics["mae"] - tol


def as_serializable_metrics(metrics):
    return {key: round(float(value), 6) for key, value in metrics.items()}


class SimpleImprovedModel:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.base_path, "..", "Spider", "data", "happiness_train_abbr.csv")
        self.model_dir = os.path.join(self.base_path, "models")
        self.model_path = os.path.join(self.model_dir, "random_forest.pkl")
        self.training_report_path = os.path.join(self.model_dir, "training_report.json")
        self.model_info_path = os.path.join(self.model_dir, "model_info.json")
        self.max_thresholds = 12

        self.ridge_alphas = [0.1, 1, 5, 10, 20]
        self.forest_param_grid = {
            "n_estimators": [80, 120, 160],
            "max_depth": [8, 12, 16],
            "min_samples_split": [10, 20],
            "min_samples_leaf": [5, 10],
            "max_features": ["sqrt", 0.35],
            "min_gain": [1e-6, 1e-4],
        }
        self.search_proxy_trees = 40
        self.search_top_k = 3

        os.makedirs(self.model_dir, exist_ok=True)

    def load_data(self):
        df = pd.read_csv(self.data_path, low_memory=False, encoding="utf-8")
        df["happiness"] = pd.to_numeric(df["happiness"], errors="coerce")
        df = df[df["happiness"].between(1, 5)].copy()
        df["happiness"] = df["happiness"].astype(float)
        df.reset_index(drop=True, inplace=True)
        return df

    def split_data(self, df):
        train_valid_df, test_df = train_test_split(
            df,
            test_size=0.15,
            random_state=SEED,
            stratify=df["happiness"],
        )
        train_df, valid_df = train_test_split(
            train_valid_df,
            test_size=0.17647058823529413,
            random_state=SEED,
            stratify=train_valid_df["happiness"],
        )
        return train_df.reset_index(drop=True), valid_df.reset_index(drop=True), test_df.reset_index(drop=True)

    def build_datasets(self, train_df, valid_df, test_df):
        X_train_raw, fill_values = prepare_model_features(train_df)
        X_valid_raw = prepare_model_features(valid_df, fill_values=fill_values)
        X_test_raw = prepare_model_features(test_df, fill_values=fill_values)

        scaler = RobustScaler()
        X_train = scaler.fit_transform(X_train_raw.values)
        X_valid = scaler.transform(X_valid_raw.values)
        X_test = scaler.transform(X_test_raw.values)

        return {
            "fill_values": fill_values,
            "scaler": scaler,
            "X_train": X_train,
            "X_valid": X_valid,
            "X_test": X_test,
            "y_train": train_df["happiness"].to_numpy(dtype=float),
            "y_valid": valid_df["happiness"].to_numpy(dtype=float),
            "y_test": test_df["happiness"].to_numpy(dtype=float),
        }

    # ... (中间的网格搜索函数 fit_ridge_grid, fit_forest_grid 等保持不变) ...

    def fit_ridge_grid(self, X_train, y_train, X_valid, y_valid):
        best = None
        print("-> 搜索手写 Ridge 线性回归最优 alpha...")
        for alpha in self.ridge_alphas:
            model = ManualRidgeRegression(alpha=alpha)
            model.fit(X_train, y_train)
            valid_pred = np.clip(model.predict(X_valid), 1, 5)
            valid_metrics = compute_metrics(y_valid, valid_pred)
            if best is None or is_better(valid_metrics, best["metrics"]):
                best = {"alpha": alpha, "model": model, "metrics": valid_metrics}
        return best

    def forest_structure_combinations(self):
        structure_keys = ["max_depth", "min_samples_split", "min_samples_leaf", "max_features", "min_gain"]
        structure_values = [self.forest_param_grid[key] for key in structure_keys]
        for values in itertools.product(*structure_values):
            yield dict(zip(structure_keys, values))

    def fit_forest_grid(self, X_train, y_train, X_valid, y_valid):
        best = None
        structure_combinations = list(self.structure_combinations_proxy())
        shortlisted = []
        for params in structure_combinations:
            model = ManualRandomForestRegressor(n_estimators=self.search_proxy_trees, **params,
                                                max_thresholds=self.max_thresholds, random_state=SEED)
            model.fit(X_train, y_train)
            metrics = compute_metrics(y_valid, np.clip(model.predict(X_valid), 1, 5))
            shortlisted.append({"params": params, "metrics": metrics})
        shortlisted.sort(key=lambda x: x["metrics"]["r2"], reverse=True)
        shortlisted = shortlisted[:self.search_top_k]

        n_est_list = self.forest_param_grid["n_estimators"]
        for item in shortlisted:
            for n in n_est_list:
                p = dict(item["params"]);
                p["n_estimators"] = n
                m = ManualRandomForestRegressor(**p, max_thresholds=self.max_thresholds, random_state=SEED)
                m.fit(X_train, y_train)
                met = compute_metrics(y_valid, np.clip(m.predict(X_valid), 1, 5))
                if best is None or is_better(met, best["metrics"]):
                    best = {"params": p, "model": m, "metrics": met}
        return best

    def structure_combinations_proxy(self):
        # 兼容原代码结构
        return self.forest_structure_combinations()

    def search_hybrid_weight(self, y_valid, lr_pred, rf_pred):
        best = None
        for weight in np.arange(0.0, 1.0001, 0.05):
            hybrid_pred = np.clip(weight * lr_pred + (1.0 - weight) * rf_pred, 1, 5)
            metrics = compute_metrics(y_valid, hybrid_pred)
            if best is None or is_better(metrics, best["metrics"]):
                best = {"weight": round(float(weight), 2), "metrics": metrics}
        return best

    def refit_final_models(self, train_df, valid_df, test_df, ridge_alpha, forest_params):
        final_train_df = pd.concat([train_df, valid_df], ignore_index=True)
        X_final_raw, fill_values = prepare_model_features(final_train_df)
        X_test_raw = prepare_model_features(test_df, fill_values=fill_values)

        scaler = RobustScaler()
        X_final = scaler.fit_transform(X_final_raw.values)
        X_test = scaler.transform(X_test_raw.values)

        y_final = final_train_df["happiness"].to_numpy(dtype=float)
        y_test = test_df["happiness"].to_numpy(dtype=float)

        ridge = ManualRidgeRegression(alpha=ridge_alpha)
        ridge.fit(X_final, y_final)

        forest = ManualRandomForestRegressor(**forest_params, max_thresholds=self.max_thresholds, random_state=SEED)
        forest.fit(X_final, y_final)

        # 这里不仅返回测试集预测，还返回训练集预测用于对比
        ridge_pred_train = np.clip(ridge.predict(X_final), 1, 5)
        forest_pred_train = np.clip(forest.predict(X_final), 1, 5)

        ridge_pred_test = np.clip(ridge.predict(X_test), 1, 5)
        forest_pred_test = np.clip(forest.predict(X_test), 1, 5)

        return {
            "fill_values": fill_values,
            "scaler": scaler,
            "ridge": ridge,
            "forest": forest,
            "y_train": y_final,
            "y_test": y_test,
            "ridge_pred_train": ridge_pred_train,
            "forest_pred_train": forest_pred_train,
            "ridge_pred_test": ridge_pred_test,
            "forest_pred_test": forest_pred_test,
            "train_rows": len(final_train_df),
            "test_rows": len(test_df),
        }

    def save_artifacts(self, artifact, report):
        with open(self.model_path, "wb") as file_obj:
            pickle.dump(artifact, file_obj)
        with open(self.training_report_path, "w", encoding="utf-8") as file_obj:
            json.dump(report, file_obj, ensure_ascii=False, indent=2)
        model_info = {
            "model_name": artifact["model_name"],
            "description": "手写 Ridge + 手写 CART 随机森林融合模型",
            "feature_importances": artifact["display_importances"],
            "hybrid_weight": artifact["hybrid_weight"],
            "metrics": report["test_metrics"],
        }
        with open(self.model_info_path, "w", encoding="utf-8") as file_obj:
            json.dump(model_info, file_obj, ensure_ascii=False, indent=2)

    def run(self):
        print("-> 启动手写幸福感预测训练流程")
        df = self.load_data()
        train_df, valid_df, test_df = self.split_data(df)
        datasets = self.build_datasets(train_df, valid_df, test_df)

        # 1. 参数搜索
        ridge_search = self.fit_ridge_grid(datasets["X_train"], datasets["y_train"], datasets["X_valid"],
                                           datasets["y_valid"])
        forest_search = self.fit_forest_grid(datasets["X_train"], datasets["y_train"], datasets["X_valid"],
                                             datasets["y_valid"])
        valid_lr_pred = np.clip(ridge_search["model"].predict(datasets["X_valid"]), 1, 5)
        valid_rf_pred = np.clip(forest_search["model"].predict(datasets["X_valid"]), 1, 5)
        hybrid_search = self.search_hybrid_weight(datasets["y_valid"], valid_lr_pred, valid_rf_pred)

        # 2. 使用最优参数在全量训练集（Train+Valid）上重训练
        final = self.refit_final_models(train_df, valid_df, test_df, ridge_search["alpha"], forest_search["params"])
        w = hybrid_search["weight"]

        # 3. 计算训练集和测试集的混合预测
        hybrid_pred_train = np.clip(w * final["ridge_pred_train"] + (1.0 - w) * final["forest_pred_train"], 1, 5)
        hybrid_pred_test = np.clip(w * final["ridge_pred_test"] + (1.0 - w) * final["forest_pred_test"], 1, 5)

        # 4. 指标统计
        train_metrics = {
            "ridge": compute_metrics(final["y_train"], final["ridge_pred_train"]),
            "forest": compute_metrics(final["y_train"], final["forest_pred_train"]),
            "hybrid": compute_metrics(final["y_train"], hybrid_pred_train),
        }
        test_metrics = {
            "ridge": compute_metrics(final["y_test"], final["ridge_pred_test"]),
            "forest": compute_metrics(final["y_test"], final["forest_pred_test"]),
            "hybrid": compute_metrics(final["y_test"], hybrid_pred_test),
        }

        # 5. 专业对比打印
        print("\n" + "=" * 90)
        print(f"| {'算法模型':<18} | {'数据集':<10} | {'R2 (↑)':<12} | {'RMSE (↓)':<12} | {'MAE (↓)':<12} |")
        print("-" * 90)
        for name in ["ridge", "forest", "hybrid"]:
            tr, te = train_metrics[name], test_metrics[name]
            print(
                f"| {name.capitalize():<18} | {'训练集':<10} | {tr['r2']:<12.4f} | {tr['rmse']:<12.4f} | {tr['mae']:<12.4f} |")
            print(f"| {'':<18} | {'测试集':<10} | {te['r2']:<12.4f} | {te['rmse']:<12.4f} | {te['mae']:<12.4f} |")
            print("-" * 90)
        print("=" * 90)

        # 6. 保存逻辑保持不变
        display_importances = build_display_importances(FEATURE_COLUMNS, final["forest"].feature_importances_)
        artifact = {
            "version": 2, "model_name": MODEL_NAME, "created_at": datetime.now().isoformat(timespec="seconds"),
            "feature_columns": FEATURE_COLUMNS, "fill_values": {k: float(v) for k, v in final["fill_values"].items()},
            "scaler_state": build_scaler_state(final["scaler"]), "ridge_state": final["ridge"].to_state(),
            "forest_state": final["forest"].to_state(), "hybrid_weight": w,
            "test_metrics": {n: as_serializable_metrics(m) for n, m in test_metrics.items()},
            "best_params": {"ridge_alpha": ridge_search["alpha"], "forest": forest_search["params"]},
            "display_importances": display_importances, "data_signature": file_signature(self.data_path),
        }
        report = {
            "model_name": MODEL_NAME, "created_at": artifact["created_at"], "test_metrics": artifact["test_metrics"],
            "train_metrics": {n: as_serializable_metrics(m) for n, m in train_metrics.items()}
        }
        self.save_artifacts(artifact, report)
        print(f"\n✅ 训练完成。最优参数: Alpha={ridge_search['alpha']}, Weight={w}")


if __name__ == "__main__":
    SimpleImprovedModel().run()