"""Detector singleton."""
from typing import Optional

from core.config import get_model_config
from core.detector import CitrusDetector, reset_detector

detector: Optional[CitrusDetector] = None


def ensure_detector():
    global detector
    if detector is None:
        try:
            detector = reset_detector(device="cpu")
        except Exception as e:
            print(f"检测器初始化失败: {e}")
            return None
    return detector


def set_detector_model(model_name: str) -> Optional[CitrusDetector]:
    """根据模型名称切换检测器使用的权重。

    Args:
        model_name: AVAILABLE_MODELS 中的键名，例如
                    "通用预训练 (YOLOv8n)"、
                    "花朵检测-增强版（过拟合）" 等。
    Returns:
        切换后的 CitrusDetector 实例，失败返回 None。
    """
    global detector
    config = get_model_config(model_name)
    model_path = config["path"]
    class_names = config.get("class_names")
    class_colors = config.get("class_colors")

    try:
        if detector is None or detector.model_path != model_path:
            detector = reset_detector(
                model_path=model_path,
                device="cpu",
                class_names=class_names,
                class_colors=class_colors,
            )
        return detector
    except Exception as e:
        print(f"切换模型失败 [{model_name}]: {e}")
        return None
