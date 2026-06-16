"""
柑橘产量预测系统 - 风险预警模块
将当前检测数据与历史同期对比，判断低产风险
"""

from typing import Dict, Optional
from .config import VarietyConfig, get_variety_config, RISK_THRESHOLDS, get_fruit_count
from .stage_classifier import StageClassifier


class RiskAlerter:
    """低产风险预警器"""

    RISK_LEVELS = {
        "severe": {"name": "严重低产", "emoji": "🔴", "color": "#FF4444"},
        "warning": {"name": "低产风险", "emoji": "⚠️", "color": "#FFAA00"},
        "normal": {"name": "产量正常", "emoji": "✅", "color": "#44AA44"},
        "unknown": {"name": "无法判断", "emoji": "❓", "color": "#888888"},
    }

    def __init__(self, variety_name: str = "通用柑橘"):
        self.variety = get_variety_config(variety_name)

    def set_variety(self, variety_name: str):
        self.variety = get_variety_config(variety_name)

    def evaluate(self, counts: Dict[str, int], stage_info: Dict,
                 historical_records: Optional[list] = None) -> Dict:
        """
        评估当前产量风险等级
        Args:
            counts: 检测结果数量
            stage_info: 阶段信息
            historical_records: 历史同期检测记录（可选）
        Returns:
            {
                "risk_level": str,      # severe/warning/normal/unknown
                "risk_name": str,       # 中文风险名称
                "emoji": str,
                "color": str,
                "current_count": int,   # 当前用于对比的数量
                "reference_avg": float, # 参考平均值
                "ratio": float,         # 当前/参考比例
                "message": str,         # 预警信息
                "suggestions": list,    # 建议措施
            }
        """
        stage = stage_info.get("stage", "unknown")
        v = self.variety

        # 根据阶段选择对比指标
        if stage == "flowering":
            current_count = counts.get("flower", 0)
            reference_avg = v.historical_flower_avg
            metric_name = "花量"
        elif stage == "immature":
            current_count = counts.get("immature_fruit", 0)
            reference_avg = v.historical_immature_avg
            metric_name = "幼果数"
        elif stage == "mature":
            fruit_count = get_fruit_count(counts)
            current_count = fruit_count
            reference_avg = v.historical_mature_avg
            metric_name = "果实数"
        else:
            # 混合期或未知：使用总数对比
            current_count = sum(counts.values())
            reference_avg = (v.historical_flower_avg + v.historical_immature_avg + v.historical_mature_avg) / 3
            metric_name = "总检测数"

        # 没有该果园历史检测记录时，不使用品种默认参考值触发低产预警。
        # 只有存在真实历史记录，才计算低产风险。
        if not historical_records:
            reference_avg = 0
        else:
            hist_values = []
            for rec in historical_records:
                c = rec.get("counts", {})
                if stage == "flowering":
                    hist_values.append(c.get("flower", 0))
                elif stage == "immature":
                    hist_values.append(c.get("immature_fruit", 0))
                elif stage == "mature":
                    hist_values.append(get_fruit_count(c))
                else:
                    hist_values.append(sum(c.values()))
            reference_avg = sum(hist_values) / len(hist_values) if hist_values else 0

        if reference_avg <= 0:
            return {
                "risk_level": "unknown",
                "risk_name": self.RISK_LEVELS["unknown"]["name"],
                "emoji": self.RISK_LEVELS["unknown"]["emoji"],
                "color": self.RISK_LEVELS["unknown"]["color"],
                "current_count": current_count,
                "reference_avg": 0,
                "ratio": 0.0,
                "message": "暂无历史参考数据，无法评估风险。",
                "suggestions": ["建议持续监测并录入历史产量数据，以便后续风险预警。"],
            }

        ratio = current_count / reference_avg

        # 判断风险等级
        if ratio < RISK_THRESHOLDS["severe"]:
            level = "severe"
            suggestions = [
                f"当前{metric_name}仅为历史均值的 {ratio:.1%}，存在严重低产风险！",
                "建议立即检查果树健康状况，排查病虫害、营养不良或授粉问题。",
                "考虑人工辅助授粉或补充营养元素（硼、锌等）。",
                "如幼果期发现大量落果，可适当喷施保果剂。",
            ]
        elif ratio < RISK_THRESHOLDS["warning"]:
            level = "warning"
            suggestions = [
                f"当前{metric_name}为历史均值的 {ratio:.1%}，低于正常水平，需关注。",
                "建议加强果园巡查，观察是否存在潜在病虫害或营养不足。",
                "优化水肥管理，确保果树获得充足的养分和水分。",
                "关注天气变化，做好防冻、防旱或排水措施。",
            ]
        else:
            level = "normal"
            suggestions = [
                f"当前{metric_name}为历史均值的 {ratio:.1%}，产量水平正常。",
                "继续保持现有管理措施，定期监测果树生长状况。",
                "做好病虫害预防和果园日常管理工作。",
            ]

        info = self.RISK_LEVELS[level]

        return {
            "risk_level": level,
            "risk_name": info["name"],
            "emoji": info["emoji"],
            "color": info["color"],
            "current_count": current_count,
            "reference_avg": round(reference_avg, 1),
            "ratio": round(ratio, 3),
            "message": f"{info['emoji']} {info['name']}：当前{metric_name}（{current_count}）"
                       f" vs 历史均值（{round(reference_avg, 1)}），比例 {ratio:.1%}",
            "suggestions": suggestions,
            "metric_name": metric_name,
        }
