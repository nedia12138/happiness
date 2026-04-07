import os
import pickle

import numpy as np
import pandas as pd

try:
    from Predictive.manual_models import ManualRandomForestRegressor, ManualRidgeRegression
    from Predictive.prediction_schema import (
        FEATURE_COLUMNS,
        apply_scaler_state,
        build_display_importances,
        canonicalize_payload,
        prepare_model_features,
    )
except ImportError:
    from manual_models import ManualRandomForestRegressor, ManualRidgeRegression
    from prediction_schema import (
        FEATURE_COLUMNS,
        apply_scaler_state,
        build_display_importances,
        canonicalize_payload,
        prepare_model_features,
    )


class HappinessPredictor:
    def __init__(self, model_path=None):
        if model_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_path, "models", "random_forest.pkl")

        with open(model_path, "rb") as file_obj:
            self.state = pickle.load(file_obj)

        self.feature_columns = self.state["feature_columns"]
        self.fill_values = self.state["fill_values"]
        self.scaler_state = self.state["scaler_state"]
        self.hybrid_weight = float(self.state["hybrid_weight"])
        self.lr_model = ManualRidgeRegression.from_state(self.state["ridge_state"])
        self.rf_model = ManualRandomForestRegressor.from_state(self.state["forest_state"])
        self.display_importances = self.state.get("display_importances") or build_display_importances(
            self.feature_columns,
            self.rf_model.feature_importances_,
        )
        self.model_name = self.state.get("model_name", "Manual Ensemble")

        print("✅ 手写幸福感预测模型已就绪")

    def _prepare_input_matrix(self, payload):
        canonical_payload = canonicalize_payload(payload or {})
        feature_frame = prepare_model_features(pd.DataFrame([canonical_payload]), fill_values=self.fill_values)
        feature_frame = feature_frame.reindex(columns=self.feature_columns, fill_value=0.0)
        return apply_scaler_state(feature_frame.values, self.scaler_state)

    def predict(self, payload):
        X = self._prepare_input_matrix(payload)
        lr_score = float(self.lr_model.predict(X)[0])
        rf_score = float(self.rf_model.predict(X)[0])
        hybrid_score = self.hybrid_weight * lr_score + (1.0 - self.hybrid_weight) * rf_score

        return {
            "lr": round(float(np.clip(lr_score, 1, 5)), 2),
            "rf": round(float(np.clip(rf_score, 1, 5)), 2),
            "hybrid": round(float(np.clip(hybrid_score, 1, 5)), 2),
        }

    def get_model_info(self):
        return {
            "model_name": self.model_name,
            "importances": self.display_importances,
            "hybrid_weight": round(self.hybrid_weight, 2),
            "metrics": self.state.get("test_metrics", {}),
        }
