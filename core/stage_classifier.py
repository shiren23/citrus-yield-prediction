"""
柑橘产量预测系统 - 生长阶段判断模块
两阶段方案：花期（花量早期预测）/ 果实期（成熟前校正）
"""

from typing import Dict, Optional
from .config import STAGE_THRESHOLDS, get_fruit_count


class StageClassifier:
    """生长阶段分类器"""

    STAGE_NAMES = {
        "flowering": "花期（早期预测）",
        "immature": "幼果期",
        "mature": "果实期（成熟校正）",
        "mixed": "混合期",
        "unknown": "未知阶段",
    }

    @staticmethod
    def _fruit_count(counts: Dict[str, int]) -> int:
        return get_fruit_count(counts)

    @staticmethod
    def classify(counts: Dict[str, int], total: Optional[int] = None) -> Dict:
        """
        根据检测数量判断生长阶段
        Args:
            counts: 归一化后的检测计数
            total: 检测总数（可选，自动计算）
        """
        flower_count = counts.get("flower", 0)
        fruit_count = StageClassifier._fruit_count(counts)
        immature_count = counts.get("immature_fruit", 0)

        if total is None:
            total = counts.get("total")
        if total is None:
            total = flower_count + immature_count + fruit_count

        if total == 0:
            return {
                "stage": "unknown",
                "stage_name": StageClassifier.STAGE_NAMES["unknown"],
                "confidence": 0.0,
                "description": "未检测到花朵或果实，请重新拍摄或更换图片。",
                "ratios": {},
                "prediction_mode": "none",
            }

        flower_ratio = flower_count / total
        fruit_ratio = fruit_count / total
        immature_ratio = immature_count / total

        if flower_ratio > STAGE_THRESHOLDS["flower"]:
            stage = "flowering"
            confidence = flower_ratio
            prediction_mode = "early"
            description = (
                f"当前处于花期，花朵占比 {flower_ratio:.1%}。"
                f"系统将根据花量 × 坐果率 × 单果重预估潜力产量。"
            )
        elif fruit_ratio > STAGE_THRESHOLDS["fruit"]:
            stage = "mature"
            confidence = fruit_ratio
            prediction_mode = "correction"
            description = (
                f"当前处于果实期，果实占比 {fruit_ratio:.1%}。"
                f"系统将根据实际果实数量进行成熟前产量校正。"
            )
        elif immature_ratio > STAGE_THRESHOLDS["immature_fruit"]:
            stage = "immature"
            confidence = immature_ratio
            prediction_mode = "mid"
            description = (
                f"当前处于幼果期，幼果占比 {immature_ratio:.1%}。"
                f"系统将结合幼果数量和成活率修正产量预测。"
            )
        else:
            stage = "mixed"
            max_ratio = max(flower_ratio, fruit_ratio, immature_ratio)
            confidence = max_ratio
            prediction_mode = "mixed"
            description = (
                f"当前处于过渡期，花朵/果实分布较混合。"
                f"系统将优先依据占比更高的类别进行估算。"
            )

        return {
            "stage": stage,
            "stage_name": StageClassifier.STAGE_NAMES[stage],
            "confidence": round(confidence, 3),
            "description": description,
            "prediction_mode": prediction_mode,
            "ratios": {
                "flower": round(flower_ratio, 3),
                "fruit": round(fruit_ratio, 3),
                "immature_fruit": round(immature_ratio, 3),
            },
        }

    @staticmethod
    def get_stage_prediction_method(stage: str) -> str:
        """获取当前阶段的预测方法说明"""
        methods = {
            "flowering": "早期预测：花量 × 坐果率 × 平均单果重",
            "immature": "中期修正：幼果数 × 成活率 × 平均单果重",
            "mature": "成熟校正：果实数 × 平均单果重 × (1-落果率)",
            "mixed": "混合期加权估算",
            "unknown": "无法预测",
        }
        return methods.get(stage, "未知方法")
