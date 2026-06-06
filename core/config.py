"""
柑橘产量预测系统 - 全局配置与品种参数
重庆地区柑橘品种配置
"""

import os
from dataclasses import dataclass
from typing import Dict, List

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_data")

# 数据库路径
DB_PATH = os.path.join(DATA_DIR, "citrus.db")

# 模型权重路径（优先使用微调后的模型，否则回退到YOLOv8n预训练权重）
CUSTOM_MODEL_PATH = os.path.join(MODEL_DIR, "best.pt")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "yolov8n.pt")


@dataclass
class VarietyConfig:
    """柑橘品种参数配置"""
    name: str
    avg_weight_kg: float          # 平均单果重量(kg)
    flower_fruit_rate: float      # 花朵→果实坐果率(花期预测用)
    immature_survival_rate: float # 幼果→成熟果成活率(幼果期预测用)
    mature_drop_rate: float       # 成熟前落果率(成熟期校正用)
    avg_fruit_diameter_cm: float  # 平均果实直径(cm)
    # 历史同期参考值（每棵树的平均数量，用于风险预警）
    historical_flower_avg: int
    historical_immature_avg: int
    historical_mature_avg: int


# 重庆地区主要柑橘品种配置
CITRUS_VARIETIES: Dict[str, VarietyConfig] = {
    "奉节脐橙": VarietyConfig(
        name="奉节脐橙",
        avg_weight_kg=0.25,
        flower_fruit_rate=0.08,
        immature_survival_rate=0.60,
        mature_drop_rate=0.05,
        avg_fruit_diameter_cm=7.5,
        historical_flower_avg=800,
        historical_immature_avg=120,
        historical_mature_avg=100,
    ),
    "忠县柑橘": VarietyConfig(
        name="忠县柑橘",
        avg_weight_kg=0.20,
        flower_fruit_rate=0.10,
        immature_survival_rate=0.65,
        mature_drop_rate=0.04,
        avg_fruit_diameter_cm=6.5,
        historical_flower_avg=750,
        historical_immature_avg=130,
        historical_mature_avg=110,
    ),
    "万州红桔": VarietyConfig(
        name="万州红桔",
        avg_weight_kg=0.15,
        flower_fruit_rate=0.12,
        immature_survival_rate=0.70,
        mature_drop_rate=0.03,
        avg_fruit_diameter_cm=5.5,
        historical_flower_avg=900,
        historical_immature_avg=150,
        historical_mature_avg=130,
    ),
    "通用柑橘": VarietyConfig(
        name="通用柑橘",
        avg_weight_kg=0.20,
        flower_fruit_rate=0.10,
        immature_survival_rate=0.65,
        mature_drop_rate=0.04,
        avg_fruit_diameter_cm=6.5,
        historical_flower_avg=800,
        historical_immature_avg=130,
        historical_mature_avg=110,
    ),
}


# YOLO 模型训练/推理类别（花朵 + 果实，两阶段预测方案）
MODEL_CLASS_NAMES = ["flower", "fruit"]

# 内部统计用类别（fruit 映射为 mature_fruit 用于成熟期校正）
CLASS_NAMES = ["flower", "immature_fruit", "mature_fruit"]
CLASS_COLORS = {
    "flower": (255, 192, 203),
    "fruit": (255, 165, 0),
    "immature_fruit": (144, 238, 144),
    "mature_fruit": (255, 165, 0),
}

# 模型类别名 → 显示名
CLASS_DISPLAY_NAMES = {
    "flower": "花朵",
    "fruit": "果实",
    "immature_fruit": "幼果",
    "mature_fruit": "成熟果",
}

# 检测置信度阈值（分类别）
CONFIDENCE_THRESHOLD = 0.25
CONFIDENCE_THRESHOLDS = {
    "flower": 0.20,
    "fruit": 0.25,
    "immature_fruit": 0.25,
    "mature_fruit": 0.25,
}
# 启发式最低展示/计数置信度
HEURISTIC_MIN_CONFIDENCE = 0.65
FALLBACK_CONFIDENCE = 0.03
FALLBACK_CLASS_THRESHOLDS = {
    "flower": 0.15,
    "fruit": 0.12,
    "immature_fruit": 0.12,
    "mature_fruit": 0.12,
}
IOU_THRESHOLD = 0.50

# 单帧/单图可见冠幅比例（用于整树产量外推）
CANOPY_VISIBLE_RATIO = {
    "flowering": 0.10,
    "immature": 0.12,
    "mature": 0.15,
    "mixed": 0.12,
    "unknown": 0.12,
}

# 风险预警阈值
RISK_THRESHOLDS = {
    "severe": 0.60,   # < 60% 历史均值 → 严重低产
    "warning": 0.80,  # < 80% 历史均值 → 低产风险
    "normal": 1.00,   # >= 80% 历史均值 → 正常
}

# 视频采样配置
VIDEO_SAMPLE_INTERVAL = 10  # 每10帧采样一次

# 生长阶段判断阈值（两阶段：花期早期预测 / 果实期成熟校正）
STAGE_THRESHOLDS = {
    "flower": 0.60,
    "fruit": 0.50,
    "immature_fruit": 0.50,
    "mature_fruit": 0.50,
}


def get_fruit_count(counts: Dict[str, int]) -> int:
    """获取果实数量（避免 fruit 与 mature_fruit 重复计数）"""
    mature = int(counts.get("mature_fruit", 0))
    fruit = int(counts.get("fruit", 0))
    return mature if mature > 0 else fruit


def normalize_counts(raw_counts: Dict[str, int]) -> Dict[str, int]:
    """
    将检测器输出的原始计数归一化为内部格式。
    2 类模型中的 fruit 映射为 mature_fruit，用于成熟期产量校正。
    """
    flower = int(raw_counts.get("flower", 0))
    fruit = int(raw_counts.get("fruit", 0))
    immature = int(raw_counts.get("immature_fruit", 0))
    mature = int(raw_counts.get("mature_fruit", 0))

    if fruit > 0 and mature == 0:
        mature = fruit
    elif mature > 0 and fruit == 0:
        fruit = mature

    total = flower + immature + mature
    return {
        "flower": flower,
        "fruit": fruit,
        "immature_fruit": immature,
        "mature_fruit": mature,
        "total": total,
    }


def get_model_class_names(model_names=None) -> List[str]:
    """获取模型类别名，优先使用模型自身定义"""
    if model_names:
        return list(model_names.values()) if isinstance(model_names, dict) else list(model_names)
    return MODEL_CLASS_NAMES


def get_variety_config(variety_name: str) -> VarietyConfig:
    """获取品种配置，若不存在则返回通用配置"""
    return CITRUS_VARIETIES.get(variety_name, CITRUS_VARIETIES["通用柑橘"])


def get_available_varieties() -> List[str]:
    """获取所有可用品种名称"""
    return list(CITRUS_VARIETIES.keys())
