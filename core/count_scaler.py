"""
检测计数 → 整棵树估算
单张照片/短视频通常只能看到部分冠幅，需按可见比例外推整树数量。
"""

from typing import Dict, Optional
from .config import get_variety_config, get_fruit_count

# 默认可见冠幅比例（可见目标数 / 整树估计总数）
DEFAULT_CANOPY_RATIO = {
    "flowering": 0.10,
    "immature": 0.12,
    "mature": 0.15,
    "mixed": 0.12,
    "unknown": 0.12,
}


def scale_counts_to_tree(
    counts: Dict[str, int],
    stage: str,
    canopy_ratio: Optional[float] = None,
    variety_name: str = "通用柑橘",
) -> Dict:
    """
    将局部检测计数外推为整棵树估计数量。
    Returns:
        {
            "raw": 原始计数,
            "scaled": 外推后计数,
            "canopy_ratio": 使用的可见比例,
            "method": 说明,
        }
    """
    ratio = canopy_ratio or DEFAULT_CANOPY_RATIO.get(stage, 0.12)
    ratio = max(ratio, 0.05)

    raw = {
        "flower": int(counts.get("flower", 0)),
        "immature_fruit": int(counts.get("immature_fruit", 0)),
        "mature_fruit": int(get_fruit_count(counts)),
    }

    scaled = {}
    for key in raw:
        n = raw[key]
        if n <= 0:
            scaled[key] = 0
        else:
            scaled[key] = max(1, round(n / ratio))

    # 按品种历史均值做合理上限，避免检测噪声导致离谱外推
    v = get_variety_config(variety_name)
    caps = {
        "flower": int(v.historical_flower_avg * 2.5),
        "immature_fruit": int(v.historical_immature_avg * 2.5),
        "mature_fruit": int(v.historical_mature_avg * 2.5),
    }
    for key, cap in caps.items():
        if scaled[key] > cap:
            scaled[key] = cap

    scaled["fruit"] = scaled["mature_fruit"]
    scaled["total"] = scaled["flower"] + scaled["immature_fruit"] + scaled["mature_fruit"]

    return {
        "raw": raw,
        "scaled": scaled,
        "canopy_ratio": ratio,
        "method": f"局部检测 ÷ 可见比例({ratio:.0%}) → 整树估计",
    }
