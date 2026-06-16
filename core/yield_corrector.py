"""
柑橘产量预测系统 - 两阶段产量校正模块
对比花期早期预测与果实期实际检测，输出校正分析
"""

from typing import Dict, List, Optional
from .yield_estimator import YieldEstimator
from .stage_classifier import StageClassifier


class YieldCorrector:
    """两阶段产量校正器"""

    @staticmethod
    def find_latest_flowering_record(historical_records: List[Dict]) -> Optional[Dict]:
        """查找最近一条花期检测记录"""
        flowering_records = [
            r for r in historical_records
            if r.get("stage") == "flowering"
        ]
        if not flowering_records:
            return None
        return flowering_records[-1]

    @staticmethod
    def analyze(current_counts: Dict[str, int], stage_info: Dict,
                historical_records: Optional[List[Dict]] = None,
                variety_name: str = "通用柑橘",
                tree_count: int = 1) -> Dict:
        """
        分析两阶段预测结果。
        若当前为果实期且存在历史花期记录，则对比早期潜力预测与当前校正产量。
        """
        estimator = YieldEstimator(variety_name)
        current_yield = estimator.estimate(current_counts, stage_info, tree_count=tree_count)
        stage = stage_info.get("stage", "unknown")
        mode = stage_info.get("prediction_mode", "none")

        result = {
            "current_yield_kg": current_yield["predicted_yield_kg"],
            "current_formula": current_yield["formula"],
            "prediction_mode": mode,
            "stage": stage,
            "has_early_record": False,
            "early_yield_kg": None,
            "correction_delta_kg": None,
            "correction_ratio": None,
            "summary": "",
        }

        if stage != "mature" or not historical_records:
            if stage == "flowering":
                result["summary"] = (
                    f"当前为早期预测阶段，预估潜力产量 "
                    f"{current_yield['predicted_yield_kg']} kg。"
                    f"请在临近采摘前再次检测果实数量以进行校正。"
                )
            elif stage == "mature":
                result["summary"] = (
                    f"当前为成熟校正阶段，校正产量 "
                    f"{current_yield['predicted_yield_kg']} kg。"
                    f"（尚无历史花期记录，无法对比早期预测。）"
                )
            else:
                result["summary"] = current_yield["formula"]
            return result

        early_record = YieldCorrector.find_latest_flowering_record(historical_records)
        if not early_record:
            result["summary"] = (
                f"成熟校正产量 {current_yield['predicted_yield_kg']} kg。"
                f"建议先在花期进行一次检测，以便对比早期预测与最终校正结果。"
            )
            return result

        early_counts = early_record.get("counts", {})
        early_stage = {"stage": "flowering", "prediction_mode": "early"}
        early_yield = estimator.estimate(early_counts, early_stage, tree_count=tree_count)

        early_kg = early_yield["predicted_yield_kg"]
        current_kg = current_yield["predicted_yield_kg"]
        delta = round(current_kg - early_kg, 2)
        ratio = round(current_kg / early_kg, 3) if early_kg > 0 else None

        result.update({
            "has_early_record": True,
            "early_yield_kg": early_kg,
            "correction_delta_kg": delta,
            "correction_ratio": ratio,
            "early_date": early_record.get("detected_at", "未知"),
            "summary": (
                f"早期预测（花期）{early_kg} kg → 成熟校正（果实期）{current_kg} kg，"
                f"变化 {delta:+} kg（{ratio:.1%}）" if ratio else
                f"早期预测 {early_kg} kg → 成熟校正 {current_kg} kg"
            ),
        })
        return result
