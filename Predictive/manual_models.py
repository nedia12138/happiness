from dataclasses import dataclass

import numpy as np


@dataclass
class SplitResult:
    feature_index: int
    threshold: float
    gain: float
    left_mask: np.ndarray
    right_mask: np.ndarray


class ManualRidgeRegression:
    def __init__(self, alpha=1.0):
        self.alpha = float(alpha)
        self.weights = None
        self.bias = 0.0

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).reshape(-1)

        X_bias = np.column_stack([np.ones(X.shape[0]), X])
        regularizer = np.eye(X_bias.shape[1], dtype=float)
        regularizer[0, 0] = 0.0
        lhs = X_bias.T @ X_bias + self.alpha * regularizer
        rhs = X_bias.T @ y
        params = np.linalg.pinv(lhs) @ rhs
        self.bias = float(params[0])
        self.weights = params[1:]
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return X @ self.weights + self.bias

    def to_state(self):
        return {
            "alpha": self.alpha,
            "bias": self.bias,
            "weights": self.weights.tolist(),
        }

    @classmethod
    def from_state(cls, state):
        model = cls(alpha=state["alpha"])
        model.bias = float(state["bias"])
        model.weights = np.asarray(state["weights"], dtype=float)
        return model


class ManualRegressionTree:
    def __init__(
        self,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features="sqrt",
        min_gain=1e-6,
        max_thresholds=16,
        random_state=None,
    ):
        self.max_depth = int(max_depth)
        self.min_samples_split = int(min_samples_split)
        self.min_samples_leaf = int(min_samples_leaf)
        self.max_features = max_features
        self.min_gain = float(min_gain)
        self.max_thresholds = int(max_thresholds)
        self.random_state = random_state

        self.root_ = None
        self.n_features_in_ = None
        self.feature_importances_ = None
        self._rng = None

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).reshape(-1)

        self.n_features_in_ = X.shape[1]
        self.feature_importances_ = np.zeros(self.n_features_in_, dtype=float)
        self._rng = np.random.default_rng(self.random_state)
        self.root_ = self._build_tree(X, y, depth=0)

        total_gain = self.feature_importances_.sum()
        if total_gain > 0:
            self.feature_importances_ = self.feature_importances_ / total_gain

        return self

    def _resolve_max_features(self):
        if self.max_features == "sqrt":
            return max(1, int(np.sqrt(self.n_features_in_)))
        if isinstance(self.max_features, float):
            return max(1, int(np.ceil(self.n_features_in_ * self.max_features)))
        if self.max_features is None:
            return self.n_features_in_
        return max(1, min(self.n_features_in_, int(self.max_features)))

    def _make_leaf(self, y):
        return {
            "type": "leaf",
            "value": float(np.mean(y)),
            "n_samples": int(len(y)),
        }

    def _candidate_thresholds(self, values):
        unique_values = np.unique(values)
        if unique_values.size <= 1:
            return np.array([], dtype=float)

        if unique_values.size <= self.max_thresholds + 1:
            return (unique_values[:-1] + unique_values[1:]) / 2.0

        quantiles = np.linspace(0.05, 0.95, self.max_thresholds)
        thresholds = np.unique(np.quantile(unique_values, quantiles))
        thresholds = thresholds[(thresholds > unique_values.min()) & (thresholds < unique_values.max())]
        return thresholds.astype(float)

    def _find_best_split(self, X, y):
        n_samples = X.shape[0]
        if n_samples < max(self.min_samples_split, self.min_samples_leaf * 2):
            return None

        parent_ss = float(np.sum((y - np.mean(y)) ** 2))
        if parent_ss <= 1e-12:
            return None

        feature_count = self._resolve_max_features()
        feature_indices = self._rng.choice(self.n_features_in_, size=feature_count, replace=False)
        total_sum = float(np.sum(y))
        total_sq_sum = float(np.sum(np.square(y)))

        best = None

        for feature_index in feature_indices:
            feature_values = X[:, feature_index]
            thresholds = self._candidate_thresholds(feature_values)
            if thresholds.size == 0:
                continue

            masks = feature_values[:, None] <= thresholds[None, :]
            left_count = masks.sum(axis=0).astype(float)
            right_count = float(n_samples) - left_count

            valid = (left_count >= self.min_samples_leaf) & (right_count >= self.min_samples_leaf)
            if not np.any(valid):
                continue

            y_column = y[:, None]
            left_sum = np.sum(y_column * masks, axis=0)
            left_sq_sum = np.sum(np.square(y_column) * masks, axis=0)
            right_sum = total_sum - left_sum
            right_sq_sum = total_sq_sum - left_sq_sum

            left_ss = left_sq_sum - np.square(left_sum) / np.maximum(left_count, 1.0)
            right_ss = right_sq_sum - np.square(right_sum) / np.maximum(right_count, 1.0)
            gain = parent_ss - left_ss - right_ss
            gain = np.where(valid, gain, -np.inf)

            best_index = int(np.argmax(gain))
            best_gain = float(gain[best_index])
            if best_gain <= self.min_gain:
                continue

            threshold = float(thresholds[best_index])
            left_mask = feature_values <= threshold
            right_mask = ~left_mask

            if best is None or best_gain > best.gain:
                best = SplitResult(
                    feature_index=int(feature_index),
                    threshold=threshold,
                    gain=best_gain,
                    left_mask=left_mask,
                    right_mask=right_mask,
                )

        return best

    def _build_tree(self, X, y, depth):
        if (
            depth >= self.max_depth
            or len(y) < self.min_samples_split
            or len(y) <= self.min_samples_leaf * 2
            or np.var(y) <= 1e-12
        ):
            return self._make_leaf(y)

        split = self._find_best_split(X, y)
        if split is None:
            return self._make_leaf(y)

        self.feature_importances_[split.feature_index] += split.gain

        left_child = self._build_tree(X[split.left_mask], y[split.left_mask], depth + 1)
        right_child = self._build_tree(X[split.right_mask], y[split.right_mask], depth + 1)

        return {
            "type": "node",
            "feature_index": split.feature_index,
            "threshold": split.threshold,
            "value": float(np.mean(y)),
            "n_samples": int(len(y)),
            "left": left_child,
            "right": right_child,
        }

    def _predict_node(self, node, X):
        if node["type"] == "leaf":
            return np.full(X.shape[0], node["value"], dtype=float)

        mask = X[:, node["feature_index"]] <= node["threshold"]
        predictions = np.empty(X.shape[0], dtype=float)
        predictions[mask] = self._predict_node(node["left"], X[mask])
        predictions[~mask] = self._predict_node(node["right"], X[~mask])
        return predictions

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return self._predict_node(self.root_, X)

    def to_state(self):
        return {
            "params": {
                "max_depth": self.max_depth,
                "min_samples_split": self.min_samples_split,
                "min_samples_leaf": self.min_samples_leaf,
                "max_features": self.max_features,
                "min_gain": self.min_gain,
                "max_thresholds": self.max_thresholds,
            },
            "n_features_in": self.n_features_in_,
            "feature_importances": self.feature_importances_.tolist(),
            "root": self.root_,
        }

    @classmethod
    def from_state(cls, state):
        model = cls(**state["params"])
        model.n_features_in_ = int(state["n_features_in"])
        model.feature_importances_ = np.asarray(state["feature_importances"], dtype=float)
        model.root_ = state["root"]
        return model


class ManualRandomForestRegressor:
    def __init__(
        self,
        n_estimators=100,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features="sqrt",
        min_gain=1e-6,
        max_thresholds=16,
        random_state=42,
    ):
        self.n_estimators = int(n_estimators)
        self.max_depth = int(max_depth)
        self.min_samples_split = int(min_samples_split)
        self.min_samples_leaf = int(min_samples_leaf)
        self.max_features = max_features
        self.min_gain = float(min_gain)
        self.max_thresholds = int(max_thresholds)
        self.random_state = random_state

        self.trees = []
        self.feature_importances_ = None
        self.n_features_in_ = None

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).reshape(-1)

        rng = np.random.default_rng(self.random_state)
        self.trees = []
        self.n_features_in_ = X.shape[1]
        importances = np.zeros(self.n_features_in_, dtype=float)

        for _ in range(self.n_estimators):
            bootstrap_indices = rng.integers(0, X.shape[0], size=X.shape[0])
            tree = ManualRegressionTree(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                max_features=self.max_features,
                min_gain=self.min_gain,
                max_thresholds=self.max_thresholds,
                random_state=int(rng.integers(0, 2**31 - 1)),
            )
            tree.fit(X[bootstrap_indices], y[bootstrap_indices])
            self.trees.append(tree)
            importances += tree.feature_importances_

        total_importance = importances.sum()
        if total_importance > 0:
            importances = importances / total_importance
        self.feature_importances_ = importances
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        tree_predictions = np.asarray([tree.predict(X) for tree in self.trees], dtype=float)
        return np.mean(tree_predictions, axis=0)

    def to_state(self):
        return {
            "params": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "min_samples_split": self.min_samples_split,
                "min_samples_leaf": self.min_samples_leaf,
                "max_features": self.max_features,
                "min_gain": self.min_gain,
                "max_thresholds": self.max_thresholds,
                "random_state": self.random_state,
            },
            "n_features_in": self.n_features_in_,
            "feature_importances": self.feature_importances_.tolist(),
            "trees": [tree.to_state() for tree in self.trees],
        }

    @classmethod
    def from_state(cls, state):
        model = cls(**state["params"])
        model.n_features_in_ = int(state["n_features_in"])
        model.feature_importances_ = np.asarray(state["feature_importances"], dtype=float)
        model.trees = [ManualRegressionTree.from_state(tree_state) for tree_state in state["trees"]]
        return model
