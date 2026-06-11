"""
柑橘产量预测系统 - 目标检测引擎
基于 YOLOv8 的花朵/幼果/成熟果实检测
支持图片和视频输入
"""

import os
import random
import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Tuple, Optional, Union
import tempfile

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from .config import (
    CUSTOM_MODEL_PATH, DEFAULT_MODEL_PATH,
    MODEL_CLASS_NAMES, CLASS_COLORS,
    CONFIDENCE_THRESHOLD, CONFIDENCE_THRESHOLDS, IOU_THRESHOLD,
    FALLBACK_CONFIDENCE, FALLBACK_CLASS_THRESHOLDS,
    VIDEO_SAMPLE_INTERVAL, normalize_counts, get_model_class_names,
)
from .heuristic_detector import (
    detect_heuristic, merge_fruit_detections, merge_flower_detections,
    color_ratios, classify_scene,
    detections_from_heuristic_boxes, detect_flowers_heuristic, HEURISTIC_CONFIDENCE,
)


def _prepare_image_array(image: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
    """统一图像格式：RGB uint8"""
    if isinstance(image, str):
        img_array = cv2.imread(image)
        if img_array is None:
            raise ValueError(f"无法读取图片: {image}")
        img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    elif isinstance(image, Image.Image):
        img_array = np.array(image.convert("RGB"))
    else:
        img_array = np.asarray(image)
        if img_array.dtype in (np.float32, np.float64):
            if img_array.max() <= 1.0:
                img_array = (img_array * 255).astype(np.uint8)
            else:
                img_array = img_array.astype(np.uint8)
        if img_array.ndim == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[-1] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
    return img_array


def _class_conf_threshold(class_name: str, thresholds: dict, default: float) -> float:
    return thresholds.get(class_name, default)


def _filter_detections(boxes, confs, classes, class_names, thresholds: dict, default_conf: float):
    """按类别置信度阈值过滤检测结果"""
    if boxes is None or len(boxes) == 0:
        return [], [], []

    kept_boxes, kept_confs, kept_classes = [], [], []
    for bbox, conf_val, cls_idx in zip(boxes, confs, classes):
        cls_name = class_names[int(cls_idx)] if int(cls_idx) < len(class_names) else "unknown"
        threshold = _class_conf_threshold(cls_name, thresholds, default_conf)
        if float(conf_val) >= threshold:
            kept_boxes.append(bbox)
            kept_confs.append(conf_val)
            kept_classes.append(cls_idx)
    return kept_boxes, kept_confs, kept_classes


def _bbox_area_ratio(bbox, img_shape) -> float:
    h, w = img_shape[:2]
    x1, y1, x2, y2 = bbox
    return max(0, x2 - x1) * max(0, y2 - y1) / max(h * w, 1)


def _bbox_orange_ratio(img_array: np.ndarray, bbox) -> float:
    bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    from .heuristic_detector import _fruit_orange_mask
    mask = _fruit_orange_mask(hsv)
    x1, y1, x2, y2 = bbox
    roi = mask[y1:y2, x1:x2]
    return float(cv2.countNonZero(roi)) / roi.size if roi.size else 0.0


def _is_plausible_box(bbox, img_shape, cls_name: str, img_array=None) -> bool:
    """过滤天空噪点、过小框、非橙色区域等明显误检"""
    h, w = img_shape[:2]
    x1, y1, x2, y2 = bbox
    bw, bh = max(1, x2 - x1), max(1, y2 - y1)
    area_ratio = _bbox_area_ratio(bbox, img_shape)
    cy = (y1 + y2) / 2
    if area_ratio < 0.00012:
        return False
    if cls_name == "fruit" and area_ratio > 0.20:
        return False
    if cls_name == "fruit" and cy < h * 0.10 and area_ratio < 0.002:
        return False
    if cls_name == "fruit" and bw / bh > 3.2:
        return False
    if cls_name == "fruit" and img_array is not None:
        if _bbox_orange_ratio(img_array, bbox) < 0.22:
            return False
    if cls_name == "fruit":
        side_ratio = min(bw, bh) / max(bw, bh)
        if side_ratio < 0.55:
            return False
        if max(bw, bh) < max(18, int(min(h, w) * 0.022)):
            return False
    if y2 < h * 0.08 and area_ratio < 0.001:
        return False
    return True


def _filter_detection_list(detections: List[Dict], img_shape, img_array=None) -> List[Dict]:
    return [
        d for d in detections
        if _is_plausible_box(d["bbox"], img_shape, d.get("class", "unknown"), img_array)
    ]


def _count_from_detections(detections: List[Dict], class_names: List[str]) -> Dict[str, int]:
    raw = {name: 0 for name in class_names}
    for d in detections:
        cls_name = d.get("class", "unknown")
        if cls_name in raw:
            raw[cls_name] += 1
    return raw


def _apply_scene_detection(
    img_array,
    class_names: List[str],
    yolo_detections: List[Dict],
    yolo_counts: Dict[str, int],
    yolo_mode: str,
) -> Tuple[List[Dict], Dict[str, int], str]:
    """按场景（花期/果实期）合并 YOLO 与启发式结果"""
    y_fruit = int(yolo_counts.get("fruit", 0))
    y_flower = int(yolo_counts.get("flower", 0))
    h = detect_heuristic(img_array, yolo_fruit=y_fruit, yolo_flower=y_flower)
    ratios = h.get("color_ratios", color_ratios(img_array))
    scene = h.get("scene") or classify_scene(ratios, h["flower"], h["fruit"], y_fruit, y_flower)
    orange = float(ratios.get("orange", 0))

    if scene == "flower" or h.get("primary") == "flower":
        yolo_flowers = [d for d in yolo_detections if d["class"] == "flower"]
        merged = merge_flower_detections(yolo_flowers, h["boxes"], ratios.get("bloom", ratios.get("white", 0.2)))
        if not merged:
            fr = detect_flowers_heuristic(img_array)
            merged = [
                {"class": "flower", "confidence": HEURISTIC_CONFIDENCE, "bbox": list(b)}
                for b in fr["boxes"]
            ]
        raw = {name: 0 for name in class_names}
        raw["flower"] = len(merged)
        return merged, raw, "hybrid" if yolo_flowers else "heuristic"

    if scene == "fruit":
        yolo_fruits = [d for d in yolo_detections if d["class"] == "fruit"]
        merged = merge_fruit_detections(yolo_fruits, h["boxes"])
        if len(merged) < max(y_fruit, h["fruit"], 3):
            merged = merge_fruit_detections([], h["boxes"])
        merged = _filter_detection_list(merged, img_array.shape, img_array)
        if not merged and h["fruit"] > 0:
            merged = _filter_detection_list(
                detections_from_heuristic_boxes(h["boxes"], "fruit"),
                img_array.shape, img_array,
            )
        raw = {name: 0 for name in class_names}
        raw["fruit"] = len(merged)
        mode = "hybrid" if y_fruit > 0 and h["fruit"] > 0 else ("heuristic" if h["fruit"] >= y_fruit else yolo_mode)
        return merged, raw, mode

    # mixed：保留 YOLO，但去掉明显不合理的类别
    detections = list(yolo_detections)
    if orange >= 0.02:
        detections = [d for d in detections if d["class"] != "flower"]
    detections = _filter_detection_list(detections, img_array.shape, img_array)
    raw = _count_from_detections(detections, class_names)
    return detections, raw, yolo_mode


def _parse_yolo_result(result, class_names, thresholds, default_conf, img_shape=None):
    detections = []
    raw_counts = {name: 0 for name in class_names}
    if result.boxes is None:
        return detections, raw_counts, [], [], []

    boxes = result.boxes.xyxy.cpu().numpy().astype(int)
    confs = result.boxes.conf.cpu().numpy()
    classes = result.boxes.cls.cpu().numpy().astype(int)
    boxes, confs, classes = _filter_detections(
        boxes, confs, classes, class_names, thresholds, default_conf
    )
    for bbox, conf_val, cls_idx in zip(boxes, confs, classes):
        cls_name = class_names[int(cls_idx)] if int(cls_idx) < len(class_names) else "unknown"
        bbox_list = bbox.tolist()
        if img_shape is not None and not _is_plausible_box(bbox_list, img_shape, cls_name, None):
            continue
        raw_counts[cls_name] = raw_counts.get(cls_name, 0) + 1
        detections.append({
            "class": cls_name,
            "confidence": float(conf_val),
            "bbox": bbox_list,
        })
    return detections, raw_counts, boxes, confs, classes


class CitrusDetector:
    """柑橘花朵与果实检测器"""

    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        初始化检测器
        Args:
            model_path: 自定义模型路径，None则自动选择
            device: 运行设备 cpu/cuda
        """
        self.device = device
        self.model = None
        self.class_names = list(MODEL_CLASS_NAMES)
        self._load_model(model_path)

    def _load_model(self, model_path: Optional[str] = None):
        """加载YOLO模型"""
        if YOLO is None:
            raise RuntimeError("Ultralytics 未安装，请先安装: pip install ultralytics")

        # 模型路径优先级: 指定路径 > 自定义微调模型 > 默认预训练模型
        if model_path and os.path.exists(model_path):
            path = model_path
        elif os.path.exists(CUSTOM_MODEL_PATH):
            path = CUSTOM_MODEL_PATH
        elif os.path.exists(DEFAULT_MODEL_PATH):
            path = DEFAULT_MODEL_PATH
        else:
            # 自动下载YOLOv8n预训练权重
            path = "yolov8n.pt"
            print(f"[Detector] 本地模型未找到，将自动下载: {path}")

        print(f"[Detector] 加载模型: {path}")
        self.model = YOLO(path)
        if hasattr(self.model, "names") and self.model.names:
            self.class_names = get_model_class_names(self.model.names)
            print(f"[Detector] 模型类别: {self.class_names}")
        # 将模型移动到指定设备
        if self.device != "cpu":
            self.model.to(self.device)

    def detect_image(self, image: Union[str, np.ndarray, Image.Image],
                     conf: float = CONFIDENCE_THRESHOLD,
                     iou: float = IOU_THRESHOLD) -> Dict:
        """
        对单张图片进行检测
        Args:
            image: 图片路径 / numpy数组 / PIL Image
            conf: 置信度阈值
            iou: NMS IoU阈值
        Returns:
            {
                "success": bool,
                "image": 标注后的图片(numpy数组),
                "detections": [
                    {"class": str, "confidence": float, "bbox": [x1,y1,x2,y2]}, ...
                ],
                "counts": dict,           # 归一化计数（含 flower/fruit/mature_fruit）
                "raw_counts": dict,       # 模型原始计数
                "total": int
            }
        """
        # 统一转换为numpy数组
        img_array = _prepare_image_array(image)

        detection_mode = "yolo"
        avg_confidence = 0.0

        # 第一遍：常规模型推理
        predict_conf = min(CONFIDENCE_THRESHOLD, min(CONFIDENCE_THRESHOLDS.values(), default=0.25))
        results = self.model.predict(img_array, conf=predict_conf, iou=iou, verbose=False)
        detections, raw_counts, boxes, confs, classes = _parse_yolo_result(
            results[0], self.class_names, CONFIDENCE_THRESHOLDS, conf, img_array.shape
        )

        # 第二遍：低置信度回退（域外图片/AI 图常见）
        yolo_counts = dict(raw_counts)
        yolo_detections = list(detections)
        yolo_mode = detection_mode
        if sum(raw_counts.values()) == 0:
            results = self.model.predict(
                img_array, conf=FALLBACK_CONFIDENCE, iou=iou, verbose=False
            )
            detections, raw_counts, boxes, confs, classes = _parse_yolo_result(
                results[0], self.class_names, FALLBACK_CLASS_THRESHOLDS,
                FALLBACK_CONFIDENCE, img_array.shape,
            )
            if sum(raw_counts.values()) > 0:
                yolo_counts = dict(raw_counts)
                yolo_detections = list(detections)
                yolo_mode = "yolo_low_conf"

        # 第三遍：按场景合并 YOLO + 启发式
        detections, raw_counts, detection_mode = _apply_scene_detection(
            img_array, self.class_names, yolo_detections, yolo_counts, yolo_mode,
        )

        # 挂果场景：用更低阈值再扫一遍 YOLO，弥补树上果实漏检
        ratios = color_ratios(img_array)
        likely_fruit_scene = (
            int(yolo_counts.get("fruit", 0)) >= 2
            or raw_counts.get("fruit", 0) >= 3
            or (
                ratios.get("orange", 0) >= 0.018
                and ratios.get("white", 0) < 0.30
                and int(yolo_counts.get("flower", 0)) <= 1
            )
        )
        if likely_fruit_scene:
            low_results = self.model.predict(
                img_array, conf=0.08, iou=iou, verbose=False
            )
            low_dets, low_raw, _, _, _ = _parse_yolo_result(
                low_results[0], self.class_names,
                {"flower": 0.99, "fruit": 0.08},
                0.08, img_array.shape,
            )
            low_fruits = _filter_detection_list(
                [d for d in low_dets if d["class"] == "fruit"],
                img_array.shape, img_array,
            )
            if low_fruits:
                h = detect_heuristic(img_array, yolo_fruit=len(low_fruits), yolo_flower=int(yolo_counts.get("flower", 0)))
                if h.get("scene") == "fruit" or h.get("primary") == "fruit":
                    merged = merge_fruit_detections(low_fruits, h["boxes"])
                    merged = _filter_detection_list(merged, img_array.shape, img_array)
                    if merged:
                        detections = merged
                        raw_counts = {name: 0 for name in self.class_names}
                        raw_counts["fruit"] = len(merged)
                        detection_mode = "hybrid"

        if sum(raw_counts.values()) == 0:
            h = detect_heuristic(img_array)
            if h["flower"] + h["fruit"] > 0:
                detections = [
                    {"class": cls, "confidence": 0.5, "bbox": list(bbox)}
                    for bbox, cls in h["boxes"]
                ]
                raw_counts = {name: 0 for name in self.class_names}
                raw_counts["flower"] = h["flower"]
                raw_counts["fruit"] = h["fruit"]
                detection_mode = "heuristic"

        annotated_img = img_array.copy()

        if detections:
            avg_confidence = sum(d["confidence"] for d in detections) / len(detections)

        for det in detections:
            bbox = det["bbox"]
            cls_name = det["class"]
            conf_val = det["confidence"]
            x1, y1, x2, y2 = bbox
            color = CLASS_COLORS.get(cls_name, (128, 128, 128))
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
            label = f"{cls_name} {conf_val:.2f}"
            cv2.putText(annotated_img, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        counts = normalize_counts(raw_counts)

        return {
            "success": True,
            "image": annotated_img,
            "detections": detections,
            "counts": counts,
            "raw_counts": raw_counts,
            "total": counts["total"],
            "detection_mode": detection_mode,
            "avg_confidence": round(avg_confidence, 3),
        }

    def detect_video(self, video_path: str,
                     conf: float = CONFIDENCE_THRESHOLD,
                     iou: float = IOU_THRESHOLD,
                     sample_interval: int = VIDEO_SAMPLE_INTERVAL) -> Dict:
        """
        对视频进行检测，每隔N帧采样一次，汇总统计
        Args:
            video_path: 视频文件路径
            conf: 置信度阈值
            iou: NMS IoU阈值
            sample_interval: 采样间隔帧数
        Returns:
            {
                "success": bool,
                "frame_results": [每帧的counts],
                "avg_counts": 平均数量,
                "max_counts": 最大数量,
                "total_frames": 处理帧数,
                "sampled_frames": 实际采样帧数,
                "preview_image": 随机采样帧的标注图(RGB),
                "preview_frame_index": 预览帧在视频中的序号(从0起),
            }
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"success": False, "error": "无法打开视频文件"}

        frame_results = []
        frame_idx = 0
        sampled = 0
        preview_image = None
        preview_frame_index = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 按间隔采样
            if frame_idx % sample_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.detect_image(frame_rgb, conf=conf, iou=iou)
                frame_results.append(result["counts"])
                sampled += 1
                # 随机保留一帧标注图，供界面预览
                if random.randint(1, sampled) == 1:
                    preview_image = result["image"]
                    preview_frame_index = frame_idx

            frame_idx += 1

        cap.release()

        if not frame_results:
            return {"success": False, "error": "视频中未检测到有效帧"}

        # 计算平均和最大数量
        avg_counts = normalize_counts({name: 0 for name in self.class_names})
        max_counts = normalize_counts({name: 0 for name in self.class_names})

        for counts in frame_results:
            normalized = normalize_counts(counts)
            for key in ("flower", "fruit", "immature_fruit", "mature_fruit"):
                avg_counts[key] += normalized.get(key, 0)
                max_counts[key] = max(max_counts.get(key, 0), normalized.get(key, 0))

        sampled = len(frame_results)
        if sampled > 0:
            for key in ("flower", "fruit", "immature_fruit", "mature_fruit"):
                avg_counts[key] = round(avg_counts[key] / sampled, 1)
        avg_counts["total"] = sum(avg_counts[k] for k in ("flower", "immature_fruit", "mature_fruit"))
        max_counts["total"] = sum(max_counts[k] for k in ("flower", "immature_fruit", "mature_fruit"))

        return {
            "success": True,
            "frame_results": frame_results,
            "avg_counts": avg_counts,
            "max_counts": max_counts,
            "total_frames": frame_idx,
            "sampled_frames": sampled,
            "preview_image": preview_image,
            "preview_frame_index": preview_frame_index,
        }

    def detect(self, input_path: str,
               conf: float = CONFIDENCE_THRESHOLD,
               iou: float = IOU_THRESHOLD) -> Dict:
        """
        自动判断输入类型（图片/视频）并进行检测
        """
        ext = os.path.splitext(input_path)[1].lower()
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"}

        if ext in video_exts:
            return self.detect_video(input_path, conf=conf, iou=iou)
        else:
            return self.detect_image(input_path, conf=conf, iou=iou)


# 单例模式，避免重复加载模型
_detector_instance: Optional[CitrusDetector] = None


def get_detector(model_path: Optional[str] = None, device: str = "cpu") -> CitrusDetector:
    """获取检测器单例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CitrusDetector(model_path=model_path, device=device)
    return _detector_instance


def reset_detector(model_path: Optional[str] = None, device: str = "cpu") -> CitrusDetector:
    """重置并重新加载检测器（模型更新后调用）"""
    global _detector_instance
    _detector_instance = CitrusDetector(model_path=model_path, device=device)
    return _detector_instance
