"""Detector singleton."""
from typing import Optional
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
