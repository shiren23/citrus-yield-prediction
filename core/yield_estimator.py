"""
柑橘产量预测系统 - 产量预测算法模块
不同阶段采用不同的预测公式与修正系数
"""

import math
from typing import Dict, Optional
from .config import VarietyConfig, get_variety_config, get_fruit_count
from .stage_classifier import StageClassifier


class YieldEstimator:
    """产量估算器"""

    def __init__(self, variety_name: str = "通用柑橘"):
        self.variety = get_variety_config(variety_name)

    def set_variety(self, variety_name: str):
        """切换品种配置"""
        self.variety = get_variety_config(variety_name)

    def estimate(self, counts: Dict[str, int], stage_info: Dict,
                 tree_count: int = 1) -> Dict:
        """
        根据检测数量和生长阶段估算产量
        Args:
            counts: {"flower": n1, "immature_fruit": n2, "mature_fruit": n3}
            stage_info: 阶段分类结果
            tree_count: 果树数量（默认1棵）
        Returns:
            {
                "predicted_yield_kg": float,    # 预测产量(kg)
                "predicted_yield_jin": float,   # 预测产量(市斤)
                "per_tree_yield_kg": float,     # 单棵产量(kg)
                "formula": str,                 # 使用的公式
                "factors": dict,                # 各因子数值
                "confidence": float,            # 预测置信度(0-1)
            }
        """
        stage = stage_info.get("stage", "unknown")
        v = self.variety

        if stage == "flowering":
            # 花期：花量 × 坐果率 × 平均单果重
            flower_count = counts.get("flower", 0)
            predicted = flower_count * v.flower_fruit_rate * v.avg_weight_kg
            formula = f"{flower_count} × {v.flower_fruit_rate} × {v.avg_weight_kg}kg"
            factors = {
                "flower_count": flower_count,
                "flower_fruit_rate": v.flower_fruit_rate,
                "avg_weight_kg": v.avg_weight_kg,
            }
            # 花期预测不确定性较高
            confidence = 0.6

        elif stage == "immature":
            # 幼果期：幼果数 × 成活率 × 平均单果重
            immature_count = counts.get("immature_fruit", 0)
            predicted = immature_count * v.immature_survival_rate * v.avg_weight_kg
            formula = f"{immature_count} × {v.immature_survival_rate} × {v.avg_weight_kg}kg"
            factors = {
                "immature_count": immature_count,
                "survival_rate": v.immature_survival_rate,
                "avg_weight_kg": v.avg_weight_kg,
            }
            confidence = 0.75

        elif stage == "mature":
            # 果实期：果实数 × 平均单果重 × (1 - 落果率)
            fruit_count = get_fruit_count(counts)
            predicted = fruit_count * v.avg_weight_kg * (1 - v.mature_drop_rate)
            formula = f"{fruit_count} × {v.avg_weight_kg}kg × (1 - {v.mature_drop_rate})"
            factors = {
                "fruit_count": fruit_count,
                "avg_weight_kg": v.avg_weight_kg,
                "mature_drop_rate": v.mature_drop_rate,
            }
            confidence = 0.9

        elif stage == "mixed":
            flower_count = counts.get("flower", 0)
            immature_count = counts.get("immature_fruit", 0)
            fruit_count = get_fruit_count(counts)
            total = flower_count + immature_count + fruit_count

            if total == 0:
                predicted = 0.0
                formula = "无有效检测数据"
                factors = {}
                confidence = 0.0
            else:
                # 加权：花期贡献 + 幼果期贡献 + 成熟期贡献
                w_flower = flower_count / total
                w_immature = immature_count / total
                w_mature = fruit_count / total

                est_flower = flower_count * v.flower_fruit_rate * v.avg_weight_kg
                est_immature = immature_count * v.immature_survival_rate * v.avg_weight_kg
                est_mature = fruit_count * v.avg_weight_kg * (1 - v.mature_drop_rate)

                predicted = w_flower * est_flower + w_immature * est_immature + w_mature * est_mature
                formula = "混合期加权(花期+幼果期+果实期)"
                factors = {
                    "flower_contrib": round(est_flower, 2),
                    "immature_contrib": round(est_immature, 2),
                    "fruit_contrib": round(est_mature, 2),
                    "weights": {
                        "flower": round(w_flower, 2),
                        "immature": round(w_immature, 2),
                        "mature": round(w_mature, 2),
                    }
                }
                confidence = 0.65

        else:
            predicted = 0.0
            formula = "无法计算"
            factors = {}
            confidence = 0.0

        # 扩展到多棵树
        total_yield = predicted * tree_count
        per_tree = predicted

        return {
            "predicted_yield_kg": round(total_yield, 2),
            "predicted_yield_jin": round(total_yield * 2, 2),  # 1kg = 2市斤
            "per_tree_yield_kg": round(per_tree, 2),
            "formula": formula,
            "factors": factors,
            "confidence": confidence,
            "variety": v.name,
        }

    def batch_estimate(self, detection_history: list) -> Dict:
        """
        根据历史检测记录进行趋势分析和综合校正
        Args:
            detection_history: list of dicts, 每次检测的 counts + stage
        Returns:
            趋势分析报告
        """
        if not detection_history:
            return {"error": "无历史数据"}

        yields = []
        stages = []
        for record in detection_history:
            counts = record.get("counts", {})
            stage_info = StageClassifier.classify(counts)
            est = self.estimate(counts, stage_info)
            yields.append(est["predicted_yield_kg"])
            stages.append(stage_info["stage"])

        # 简单趋势分析：后期阶段的预测更可靠，给予更高权重
        weighted_sum = 0.0
        weight_total = 0.0
        stage_weights = {"flowering": 0.3, "immature": 0.6, "mature": 1.0, "mixed": 0.5}

        for y, s in zip(yields, stages):
            w = stage_weights.get(s, 0.5)
            weighted_sum += y * w
            weight_total += w

        corrected_yield = weighted_sum / weight_total if weight_total > 0 else 0

        return {
            "history_count": len(detection_history),
            "yield_records": yields,
            "stage_records": stages,
            "avg_yield": round(sum(yields) / len(yields), 2) if yields else 0,
            "corrected_yield": round(corrected_yield, 2),
            "trend": "上升" if len(yields) > 1 and yields[-1] > yields[0] else "下降/平稳",
        }
