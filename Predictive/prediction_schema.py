import hashlib
import math
import re
from pathlib import Path
# 数据清洗（Clean Data）：通过 MISSING_SENTINELS 准确识别了问卷中的异常逻辑，避免了错误数据对模型的干扰。
#
# 特征衍生（Feature Engineering）：你通过 engineer_features 将原始特征进行了升维。例如：
#
# age_sq 捕捉了幸福感的 U 型规律。
#
# log_income 处理了收入的 长尾偏态分布。     * interaction 捕捉了 变量间的协同效应。
#
# 工业化部署：使用了 apply_scaler_state。这意味着你的后端系统在预测时不需要加载庞大的 sklearn 对象，仅凭几个参数列表就能完成同样的缩放计算。这体现了你对高性能部署的理解。
import numpy as np
import pandas as pd
#     "age",                       # 年龄：由当前年份减去出生年份得出
#     "age_sq",                    # 年龄平方：用于捕捉幸福感与年龄之间的“U型曲线”关系
#     "log_income",                # 收入对数：平滑高收入人群的数据波动，减少离群点干扰
#     "log_family_income",         # 家庭收入对数：同上，处理家庭总收入
#     "income_gap",                # 家庭收入差：计算个人收入在家庭中的占比权重
#     "class_income_interaction",  # 阶层收入交互项：分析“主观社会地位”与“实际经济收入”的耦合影响
#     "health_depression_gap",     # 健康抑郁差值：综合评估身体健康与心理健康之间的差额

MISSING_SENTINELS = (-8, -3, -2, -1)

BASE_FEATURES = [
    "gender",
    "birth",
    "marital",
    "edu",
    "income",
    "family_income",
    "floor_area",
    "car",
    "house",
    "health",
    "depression",
    "relax",
    "equity",
    "class",
    "status_peer",
    "political",
    "hukou",
    "religion",
    "socialize",
    "learn",
    "work_status",
    "family_status",
    "inc_ability",
    "height_cm",
    "weight_jin",
    "trust",            # 新增：社会信任度
    "media_tv",         # 新增：看电视频率
    "media_internet"    # 新增：上网频率
]

DERIVED_FEATURES = [
    "age",
    "age_sq",
    "log_income",
    "log_family_income",
    "income_gap",
    "class_income_interaction",
    "health_depression_gap",
]

FEATURE_COLUMNS = BASE_FEATURES + DERIVED_FEATURES

FEATURE_LABELS = {
    "gender": "性别",
    "birth": "出生年份",
    "marital": "婚姻状况",
    "edu": "受教育程度",
    "income": "个人收入",
    "family_income": "家庭收入",
    "floor_area": "住房面积",
    "car": "私家车数量",
    "house": "住房产权",
    "health": "健康状况",
    "depression": "心理忧郁感",
    "relax": "休闲放松",
    "equity": "社会公平感",
    "class": "主观社会阶层",
    "status_peer": "同龄人地位感知",
    "political": "政治面貌",
    "hukou": "户口性质",
    "religion": "宗教信仰",
    "socialize": "社交频率",
    "learn": "学习频率",
    "work_status": "工作状态",
    "family_status": "家庭社会地位",
    "inc_ability": "收入相对水平",
    "height_cm": "身高",
    "weight_jin": "体重",
    "age": "年龄",
    "age_sq": "年龄平方项",
    "log_income": "收入对数",
    "log_family_income": "家庭收入对数",
    "income_gap": "家庭收入差",
    "class_income_interaction": "阶层收入交互项",
    "health_depression_gap": "健康抑郁差值",
}


_EXPLICIT_ALIASES = {
    "familyincome": "family_income",
    "familyIncome": "family_income",
    "floorarea": "floor_area",
    "floorArea": "floor_area",
    "statuspeer": "status_peer",
    "statusPeer": "status_peer",
    "workstatus": "work_status",
    "workStatus": "work_status",
    "familystatus": "family_status",
    "familyStatus": "family_status",
    "incability": "inc_ability",
    "incAbility": "inc_ability",
    "heightcm": "height_cm",
    "heightCm": "height_cm",
    "weightjin": "weight_jin",
    "weightJin": "weight_jin",
    "trust1": "trust",        # 假设你用 trust1 代表整体社会信任度
    "media4": "media_tv",     # CGSS中 media4 通常是电视
    "media5": "media_internet",
    "mediatv": "media_tv",
    "mediaTv": "media_tv",
    "mediainternet": "media_internet",
    "mediaInternet": "media_internet"
}

_CANONICAL_LOOKUP = {feature: feature for feature in BASE_FEATURES}
_CANONICAL_LOOKUP.update({feature.replace("_", ""): feature for feature in BASE_FEATURES})
_CANONICAL_LOOKUP.update({feature.lower(): feature for feature in BASE_FEATURES})
_CANONICAL_LOOKUP.update(_EXPLICIT_ALIASES)


def camel_to_snake(name):
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def canonicalize_key(key):
    if key is None:
        return None

    if key in _CANONICAL_LOOKUP:
        return _CANONICAL_LOOKUP[key]

    snake_key = camel_to_snake(str(key))
    if snake_key in _CANONICAL_LOOKUP:
        return _CANONICAL_LOOKUP[snake_key]

    compact_key = snake_key.replace("_", "")
    return _CANONICAL_LOOKUP.get(compact_key, snake_key)


def canonicalize_payload(payload):
    """规范化用户上传的 JSON：只保留后端模型需要的字段，过滤掉干扰信息"""
    normalized = {}
    for key, value in (payload or {}).items():
        canonical_key = canonicalize_key(key)
        if canonical_key in BASE_FEATURES:
            normalized[canonical_key] = value
    return normalized


def _coerce_numeric(series):
    """强制数值化：将数据转为浮点数，并将 -8 等无效哨兵值置为 NaN（标准空值）"""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.mask(numeric.isin(MISSING_SENTINELS))


def prepare_base_feature_frame(df, fill_values=None):
    """准备基础特征矩阵：负责字段对齐和空值填充"""
    normalized = df.copy()
    normalized = normalized.rename(columns={column: canonicalize_key(column) for column in normalized.columns})

    prepared = pd.DataFrame(index=normalized.index)
    learned_fill_values = {}

    for feature in BASE_FEATURES:
        # 提取字段数据并清洗
        if feature in normalized.columns:
            series = _coerce_numeric(normalized[feature])
        else:
            series = pd.Series(np.nan, index=normalized.index, dtype=float)

        if fill_values is None:
            # 训练阶段：计算该字段的中位数作为填充标准，并记录下来
            valid_values = series.dropna()
            fill_value = float(valid_values.median()) if not valid_values.empty else 0.0
            learned_fill_values[feature] = fill_value
        else:
            fill_value = float(fill_values.get(feature, 0.0))

        prepared[feature] = series.fillna(fill_value)

    if fill_values is None:
        return prepared, learned_fill_values
    return prepared


def engineer_features(base_df):
    features = base_df.copy()

    features["age"] = 2015.0 - features["birth"]
    # 2. 年龄平方：社会学研究表明幸福感随年龄呈先降后升的 U 型，平方项能捕捉这种非线性关系
    features["age_sq"] = np.square(features["age"])
    # 3. 收入取对数：解决收入分布极度偏态的问题，np.log1p 处理了收入为 0 的情况
    # 因为社会中的收入差距极大，直接使用原始金额会导致数据分布极度偏斜。通过 np.log1p（即 $\ln(x+1)$），你将数据压缩到了一个更平稳的区间，
    # 让模型更容易捕捉收入与幸福感之间的边际效应。
    features["log_income"] = np.log1p(np.clip(features["income"], a_min=0, a_max=None))

    features["log_family_income"] = np.log1p(np.clip(features["family_income"], a_min=0, a_max=None))
    # 4. 收入差距：反映个人在家庭经济结构中的地位
    features["income_gap"] = features["log_family_income"] - features["log_income"]
    # 5. 交互项（高级特征）：反映了“如果你认为自己阶层高，那么增加收入是否会更显著地提升幸福感”
    features["class_income_interaction"] = features["class"] * features["log_income"]
    # 6. 身心差值：如果身体很健康但心理很抑郁，这个差值会提醒模型注意心理健康对总分的拉低作用
    features["health_depression_gap"] = features["health"] - features["depression"]
    # 返回最终合并后的 32 维特征向量
    return features[FEATURE_COLUMNS]


def prepare_model_features(df, fill_values=None):
    """入口函数：一键完成数据规范化、空值填充和特征衍生"""
    if fill_values is None:
        base_df, learned_fill_values = prepare_base_feature_frame(df, fill_values=None)
        return engineer_features(base_df), learned_fill_values
    base_df = prepare_base_feature_frame(df, fill_values=fill_values)
    return engineer_features(base_df)


def build_scaler_state(scaler):
    """导出 Scaler 状态：将 RobustScaler 的中轴和缩放系数转为列表，方便存入 JSON/PKL"""
    return {
        "center": scaler.center_.tolist(),
        "scale": scaler.scale_.tolist(),
    }


def apply_scaler_state(X, scaler_state):
    center = np.asarray(scaler_state["center"], dtype=float)
    scale = np.asarray(scaler_state["scale"], dtype=float)
    safe_scale = np.where(np.abs(scale) < 1e-12, 1.0, scale)
    return (np.asarray(X, dtype=float) - center) / safe_scale


def build_display_importances(feature_names, importances, limit=10):
    """重要性构建器：将算法输出的 Gini 重要性分数映射回中文名，给前端画图用"""
    pairs = []
    for feature_name, importance in zip(feature_names, importances):
        label = FEATURE_LABELS.get(feature_name, feature_name)
        pairs.append(
            {
                "key": feature_name,
                "name": label,
                "value": round(float(importance) * 100.0, 2),
            }
        )

    pairs.sort(key=lambda item: item["value"], reverse=True)
    return pairs[:limit]


def file_signature(path):
    path = Path(path)
    digest = hashlib.md5()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path),
        "md5": digest.hexdigest(),
        "bytes": path.stat().st_size,
    }


def float_or_none(value):
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return float(value)
