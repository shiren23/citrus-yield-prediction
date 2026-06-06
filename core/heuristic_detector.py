"""
颜色/形态启发式检测（YOLO 弱检出或场景不匹配时的补充/校正）
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple

HEURISTIC_CONFIDENCE = 0.65
FLOWER_NMS_IOU = 0.42
FRUIT_NMS_IOU = 0.40


def _ensure_bgr(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def _fruit_orange_mask(hsv: np.ndarray) -> np.ndarray:
    m1 = cv2.inRange(hsv, (5, 70, 70), (22, 255, 255))
    m2 = cv2.inRange(hsv, (0, 55, 90), (18, 220, 255))
    return cv2.bitwise_or(m1, m2)


def _flower_white_mask(hsv: np.ndarray) -> np.ndarray:
    return cv2.bitwise_or(
        cv2.inRange(hsv, (0, 0, 155), (180, 55, 255)),
        cv2.inRange(hsv, (140, 5, 150), (180, 75, 255)),
    )


def _stamen_mask(hsv: np.ndarray, white_mask: np.ndarray) -> np.ndarray:
    yellow = cv2.inRange(hsv, (12, 35, 100), (38, 255, 255))
    dilated_white = cv2.dilate(
        white_mask,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)),
        iterations=1,
    )
    return cv2.bitwise_and(yellow, dilated_white)


def _stamen_centers(stamen_mask: np.ndarray, img_area: int) -> List[Tuple[int, int, int, int]]:
    """提取单个花蕊候选（过滤合并后的大块）"""
    contours, _ = cv2.findContours(stamen_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    seeds = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        ratio = area / img_area
        if ratio < 0.00004 or ratio > 0.012:
            continue
        if max(bw, bh) < 5:
            continue
        seeds.append((x, y, x + bw, y + bh))
    if len(seeds) > 1:
        scores = [(b[2] - b[0]) * (b[3] - b[1]) for b in seeds]
        seeds = _nms_boxes(seeds, [float(s) for s in scores], iou_threshold=0.45)
    return seeds


def _flower_box_from_stamen(
    stamen_box: Tuple[int, int, int, int],
    white_mask: np.ndarray,
    stamen_mask: np.ndarray,
    h: int,
    w: int,
) -> Tuple[int, int, int, int]:
    """以花蕊为中心，向周围扩展找到整朵花的外接框"""
    x1, y1, x2, y2 = stamen_box
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    sw, sh = x2 - x1, y2 - y1
    pad = max(int(max(sw, sh) * 8.5), 28)
    fx1 = max(0, cx - pad)
    fy1 = max(0, cy - pad)
    fx2 = min(w, cx + pad)
    fy2 = min(h, cy + pad)

    roi_white = white_mask[fy1:fy2, fx1:fx2]
    roi_stamen = stamen_mask[fy1:fy2, fx1:fx2]
    combined = cv2.bitwise_or(roi_white, roi_stamen)
    pts = cv2.findNonZero(combined)
    if pts is None:
        return (fx1, fy1, fx2, fy2)
    bx, by, bw, bh = cv2.boundingRect(pts)
    return (fx1 + bx, fy1 + by, fx1 + bx + bw, fy1 + by + bh)


def _white_bud_boxes(
    white_mask: np.ndarray,
    stamen_mask: np.ndarray,
    h: int,
    w: int,
    img_area: int,
) -> List[Tuple[int, int, int, int]]:
    """未开放花苞：白色区域且附近无花蕊"""
    stamen_dilated = cv2.dilate(
        stamen_mask,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)),
        iterations=1,
    )
    buds_only = cv2.bitwise_and(white_mask, cv2.bitwise_not(stamen_dilated))
    buds_only = cv2.morphologyEx(
        buds_only, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        iterations=1,
    )
    boxes = []
    contours, _ = cv2.findContours(buds_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        ratio = area / img_area
        if ratio < 0.0004 or ratio > 0.035:
            continue
        ar = bw / max(bh, 1)
        if not (0.35 <= ar <= 3.5):
            continue
        boxes.append((x, y, x + bw, y + bh))
    return boxes


def _nms_by_distance(
    boxes: List[Tuple[int, int, int, int]],
    scores: List[float],
    min_center_dist_ratio: float = 0.55,
) -> List[Tuple[int, int, int, int]]:
    """合并中心过近的重叠框（同一朵花的多个花蕊）"""
    if not boxes:
        return []
    order = np.argsort(scores)[::-1]
    kept = []
    for idx in order:
        box = boxes[int(idx)]
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2
        bw, bh = box[2] - box[0], box[3] - box[1]
        min_dist = max(bw, bh) * min_center_dist_ratio
        too_close = False
        for kb in kept:
            kcx = (kb[0] + kb[2]) / 2
            kcy = (kb[1] + kb[3]) / 2
            if ((cx - kcx) ** 2 + (cy - kcy) ** 2) ** 0.5 < min_dist:
                too_close = True
                break
        if not too_close:
            kept.append(box)
    return kept


def _cap_flower_boxes(
    boxes: List[Tuple[int, int, int, int]],
    scores: List[float],
    bloom_ratio: float,
    yolo_supported: bool = False,
) -> List[Tuple[int, int, int, int]]:
    if not boxes:
        return []
    if yolo_supported:
        max_flowers = max(3, min(12, int(bloom_ratio * 18 + 1)))
    else:
        max_flowers = max(3, min(8, int(bloom_ratio * 12 + 1)))
    if len(boxes) <= max_flowers:
        return boxes
    order = np.argsort(scores)[::-1][:max_flowers]
    return [boxes[int(i)] for i in order]


def _nms_boxes(
    boxes: List[Tuple[int, int, int, int]],
    scores: List[float],
    iou_threshold: float = 0.45,
) -> List[Tuple[int, int, int, int]]:
    if not boxes:
        return []
    boxes_arr = np.array(boxes, dtype=np.float32)
    scores_arr = np.array(scores, dtype=np.float32)
    order = scores_arr.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = int(order[0])
        keep.append(tuple(map(int, boxes_arr[i])))
        if order.size == 1:
            break
        rest = order[1:]
        xx1 = np.maximum(boxes_arr[i, 0], boxes_arr[rest, 0])
        yy1 = np.maximum(boxes_arr[i, 1], boxes_arr[rest, 1])
        xx2 = np.minimum(boxes_arr[i, 2], boxes_arr[rest, 2])
        yy2 = np.minimum(boxes_arr[i, 3], boxes_arr[rest, 3])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        area_i = (boxes_arr[i, 2] - boxes_arr[i, 0]) * (boxes_arr[i, 3] - boxes_arr[i, 1])
        area_r = (boxes_arr[rest, 2] - boxes_arr[rest, 0]) * (boxes_arr[rest, 3] - boxes_arr[rest, 1])
        iou = inter / (area_i + area_r - inter + 1e-6)
        order = rest[iou <= iou_threshold]
    return keep


def _box_color_ratio(mask: np.ndarray, box: Tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = box
    roi = mask[y1:y2, x1:x2]
    return float(cv2.countNonZero(roi)) / roi.size if roi.size else 0.0


def _box_green_ratio(green_mask: np.ndarray, box: Tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = box
    roi = green_mask[y1:y2, x1:x2]
    return float(cv2.countNonZero(roi)) / roi.size if roi.size else 0.0


def _is_sky_box(box: Tuple[int, int, int, int], h: int, green_mask: np.ndarray) -> bool:
    x1, y1, x2, y2 = box
    cy = (y1 + y2) / 2
    if cy > h * 0.18:
        return False
    return _box_green_ratio(green_mask, box) < 0.15


def _fruit_boxes_from_mask(
    fruit_mask: np.ndarray,
    bloom: np.ndarray,
    stamen: np.ndarray,
    green_mask: np.ndarray,
    h: int,
    w: int,
    y_start: int,
    y_end: int,
    area_min_ratio: float,
    area_max_ratio: float,
    min_orange_ratio: float = 0.22,
    require_near_green: bool = False,
) -> List[Tuple[int, int, int, int, float]]:
    img_area = h * w
    sub = fruit_mask[y_start:y_end, :]
    green_d = cv2.dilate(
        green_mask[y_start:y_end, :],
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)),
    ) if require_near_green else None
    boxes = []
    contours, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        if not (img_area * area_min_ratio <= area <= img_area * area_max_ratio):
            continue
        if not (0.55 <= bw / max(bh, 1) <= 1.85):
            continue
        peri = cv2.arcLength(cnt, True)
        if peri < 1:
            continue
        circularity = 4 * np.pi * cv2.contourArea(cnt) / (peri * peri)
        if circularity < 0.35:
            continue
        box = (x, y + y_start, x + bw, y + y_start + bh)
        if _is_sky_box(box, h, green_mask):
            continue
        if _box_color_ratio(bloom, box) > 0.10:
            continue
        if _box_color_ratio(stamen, box) > 0.06:
            continue
        orange_r = _box_color_ratio(fruit_mask, box)
        if orange_r < min_orange_ratio:
            continue
        if require_near_green and green_d is not None:
            if _box_color_ratio(green_d, box) < 0.08:
                continue
        score = min(0.95, 0.50 + orange_r * 0.35 + circularity * 0.12)
        boxes.append((*box, score))
    return boxes


def _expand_fruit_box(
    orange_mask: np.ndarray,
    box: Tuple[int, int, int, int],
    h: int,
    w: int,
) -> Tuple[int, int, int, int]:
    """从小色块向外扩展，尽量框住整颗果"""
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    base = max(x2 - x1, y2 - y1, 12)
    best = box
    best_fill = _box_color_ratio(orange_mask, box)
    for step in range(1, 10):
        half = base // 2 + step * max(4, base // 6)
        nx1, ny1 = max(0, cx - half), max(0, cy - half)
        nx2, ny2 = min(w, cx + half), min(h, cy + half)
        nbox = (nx1, ny1, nx2, ny2)
        fill = _box_color_ratio(orange_mask, nbox)
        if fill >= best_fill * 0.72 and fill >= 0.18:
            best, best_fill = nbox, fill
        else:
            break
    return best


def _cluster_fruit_boxes(
    boxes: List[Tuple[int, int, int, int]],
    scores: List[float],
    merge_dist: float,
) -> Tuple[List[Tuple[int, int, int, int]], List[float]]:
    """合并中心过近的小框，每簇只保留一个外接框"""
    if not boxes:
        return [], []
    order = np.argsort(scores)[::-1]
    used = [False] * len(boxes)
    merged_boxes, merged_scores = [], []
    for idx in order:
        if used[int(idx)]:
            continue
        bx1, by1, bx2, by2 = boxes[int(idx)]
        cluster = [int(idx)]
        used[int(idx)] = True
        bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
        for j, box in enumerate(boxes):
            if used[j]:
                continue
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            if ((cx - bcx) ** 2 + (cy - bcy) ** 2) ** 0.5 < merge_dist:
                cluster.append(j)
                used[j] = True
                bx1, by1 = min(bx1, box[0]), min(by1, box[1])
                bx2, by2 = max(bx2, box[2]), max(by2, box[3])
        merged_boxes.append((int(bx1), int(by1), int(bx2), int(by2)))
        merged_scores.append(max(scores[i] for i in cluster))
    return merged_boxes, merged_scores


def _cap_fruit_boxes(
    boxes: List[Tuple[int, int, int, int]],
    scores: List[float],
    orange_ratio: float,
) -> List[Tuple[int, int, int, int]]:
    if not boxes:
        return []
    max_fruits = max(5, min(22, int(orange_ratio * 100 + 4)))
    if len(boxes) <= max_fruits:
        return boxes
    order = np.argsort(scores)[::-1][:max_fruits]
    return [boxes[int(i)] for i in order]


def _fruit_boxes_from_components(
    orange_mask: np.ndarray,
    bloom: np.ndarray,
    stamen: np.ndarray,
    green_mask: np.ndarray,
    h: int,
    w: int,
    y_start: int,
    y_end: int,
    area_min_ratio: float,
    area_max_ratio: float,
    min_orange_ratio: float = 0.30,
    require_near_green: bool = False,
) -> List[Tuple[int, int, int, int, float]]:
    img_area = h * w
    sub = orange_mask[y_start:y_end, :].copy()
    sub = cv2.morphologyEx(
        sub, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1,
    )
    green_d = None
    if require_near_green:
        green_d = cv2.dilate(
            green_mask[y_start:y_end, :],
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)),
        )

    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(sub, connectivity=8)
    raw_boxes, raw_scores = [], []
    sizes = []
    for i in range(1, num_labels):
        x, y, bw, bh, pix_area = stats[i]
        if pix_area < img_area * area_min_ratio or pix_area > img_area * area_max_ratio:
            continue
        if max(bw, bh) < 10:
            continue
        side_ratio = min(bw, bh) / max(bw, bh)
        if side_ratio < 0.55:
            continue
        box = (x, y + y_start, x + bw, y + y_start + bh)
        if _is_sky_box(box, h, green_mask):
            continue
        if _box_color_ratio(bloom, box) > 0.12:
            continue
        if _box_color_ratio(stamen, box) > 0.05:
            continue
        orange_r = _box_color_ratio(orange_mask, box)
        if orange_r < min_orange_ratio:
            continue
        if green_d is not None and _box_color_ratio(green_d, (x, y, x + bw, y + bh)) < 0.06:
            continue
        score = min(0.95, 0.45 + orange_r * 0.40)
        raw_boxes.append(box)
        raw_scores.append(score)
        sizes.append(max(bw, bh))

    if not raw_boxes:
        return []

    merge_dist = max(28, int(min(h, w) * 0.038))
    if sizes:
        merge_dist = max(merge_dist, int(np.median(sizes) * 0.85))
    merged, merged_scores = _cluster_fruit_boxes(raw_boxes, raw_scores, merge_dist)

    # 略微扩展框以覆盖整颗果
    min_dim = min(h, w)
    padded = []
    for (x1, y1, x2, y2), score in zip(merged, merged_scores):
        bw, bh = x2 - x1, y2 - y1
        pbox = (x1, y1, x2, y2)
        if max(bw, bh) < min_dim * 0.07:
            pbox = _expand_fruit_box(orange_mask, pbox, h, w)
        else:
            pad = max(3, int(max(bw, bh) * 0.10))
            pbox = (max(0, x1 - pad), max(0, y1 - pad), min(w, x2 + pad), min(h, y2 + pad))
        if _box_color_ratio(orange_mask, pbox) < min_orange_ratio * 0.70:
            pbox = (x1, y1, x2, y2)
        padded.append((*pbox, score))
    return padded


def color_ratios(image: np.ndarray) -> Dict[str, float]:
    bgr = _ensure_bgr(image)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    total = hsv.shape[0] * hsv.shape[1]
    white = _flower_white_mask(hsv)
    stamen = _stamen_mask(hsv, white)
    fruit_raw = _fruit_orange_mask(hsv)
    # 场景判断用：排除花蕊后的“真果实橙”
    fruit_only = cv2.bitwise_and(fruit_raw, cv2.bitwise_not(stamen))
    green = cv2.inRange(hsv, (35, 35, 35), (85, 255, 255))
    bloom = cv2.bitwise_or(white, stamen)
    return {
        "orange": float(cv2.countNonZero(fruit_only)) / total,
        "white": float(cv2.countNonZero(white)) / total,
        "green": float(cv2.countNonZero(green)) / total,
        "bloom": float(cv2.countNonZero(bloom)) / total,
    }


def classify_scene(
    ratios: Dict[str, float],
    flower_n: int,
    fruit_n: int,
    yolo_fruit: int = 0,
    yolo_flower: int = 0,
) -> str:
    orange = ratios["orange"]
    white = ratios["white"]
    green = ratios["green"]
    bloom = ratios.get("bloom", white)

    # YOLO / 启发式挂果信号优先（沙地/天空的高 white 不能覆盖）
    if yolo_fruit >= 5:
        return "fruit"
    if yolo_fruit >= 2 and (orange >= 0.012 or fruit_n >= 2):
        return "fruit"
    if fruit_n >= 6 and orange >= 0.015:
        return "fruit"
    if yolo_fruit >= 1 and fruit_n >= 4 and orange >= 0.018:
        return "fruit"

    # 花期：必须几乎没有果实信号
    if yolo_fruit == 0 and fruit_n <= 1 and orange < 0.025:
        if bloom >= 0.12 or (white >= 0.12 and green >= 0.18):
            if flower_n >= 2 or yolo_flower >= 2:
                return "flower"
        if yolo_flower >= 3 and white >= 0.08:
            return "flower"
        if flower_n >= 3 and flower_n > fruit_n and white >= 0.06:
            return "flower"

    if fruit_n > flower_n and fruit_n >= 4:
        return "fruit"
    if yolo_fruit > 0 and fruit_n >= yolo_fruit:
        return "fruit"
    if flower_n >= 2 and yolo_fruit == 0 and fruit_n == 0 and orange < 0.02:
        return "flower"
    return "mixed"


def detect_flowers_heuristic(image: np.ndarray) -> Dict:
    """花蕊中心扩展 + 白色花苞，每朵花一个框"""
    bgr = _ensure_bgr(image)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    white_mask = _flower_white_mask(hsv)
    stamen_mask = _stamen_mask(hsv, white_mask)
    h, w = bgr.shape[:2]
    img_area = h * w

    boxes, scores = [], []
    seen = set()
    for stamen_box in _stamen_centers(stamen_mask, img_area):
        box = _flower_box_from_stamen(stamen_box, white_mask, stamen_mask, h, w)
        area = (box[2] - box[0]) * (box[3] - box[1])
        if area < img_area * 0.0025 or area > img_area * 0.10:
            continue
        bw, bh = box[2] - box[0], box[3] - box[1]
        if not (0.35 <= bw / max(bh, 1) <= 3.2):
            continue
        white_r = _box_color_ratio(white_mask, box)
        stamen_r = _box_color_ratio(stamen_mask, box)
        if white_r < 0.06 and stamen_r < 0.02:
            continue
        key = (box[0] // 8, box[1] // 8, box[2] // 8, box[3] // 8)
        if key in seen:
            continue
        seen.add(key)
        score = min(0.95, 0.58 + white_r * 0.28 + stamen_r * 0.12)
        boxes.append(box)
        scores.append(score)

    for box in _white_bud_boxes(white_mask, stamen_mask, h, w, img_area):
        white_r = _box_color_ratio(white_mask, box)
        if white_r < 0.18:
            continue
        stamen_r = _box_color_ratio(stamen_mask, box)
        if stamen_r > 0.03:
            continue
        key = (box[0] // 8, box[1] // 8, box[2] // 8, box[3] // 8)
        if key in seen:
            continue
        seen.add(key)
        boxes.append(box)
        scores.append(min(0.90, 0.55 + white_r * 0.30))

    kept = _nms_boxes(boxes, scores, iou_threshold=FLOWER_NMS_IOU)
    score_map = {b: s for b, s in zip(boxes, scores)}
    kept_scores = [score_map[b] for b in kept]
    kept = _nms_by_distance(kept, kept_scores, min_center_dist_ratio=0.62)
    kept_scores = [score_map.get(b, 0.65) for b in kept]
    ratios = color_ratios(image)
    kept = _cap_flower_boxes(kept, kept_scores, ratios.get("bloom", ratios["white"]), yolo_supported=False)
    return {"flower": len(kept), "fruit": 0, "boxes": kept}


def detect_fruits_heuristic(image: np.ndarray) -> Dict:
    bgr = _ensure_bgr(image)
    h, w = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    white = _flower_white_mask(hsv)
    stamen = _stamen_mask(hsv, white)
    green = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
    fruit_raw = _fruit_orange_mask(hsv)
    bloom = cv2.bitwise_or(white, stamen)
    fruit_mask = cv2.bitwise_and(fruit_raw, cv2.bitwise_not(stamen))

    canopy_end = int(h * 0.78)
    ground_start = int(h * 0.55)
    boxes_scores: List[Tuple[int, int, int, int, float]] = []

    boxes_scores.extend(_fruit_boxes_from_components(
        fruit_mask, bloom, stamen, green, h, w,
        0, canopy_end, 0.00012, 0.10, min_orange_ratio=0.28, require_near_green=False,
    ))
    boxes_scores.extend(_fruit_boxes_from_components(
        fruit_mask, bloom, stamen, green, h, w,
        ground_start, h, 0.00020, 0.08, min_orange_ratio=0.32, require_near_green=False,
    ))

    seen = set()
    boxes, scores = [], []
    for x1, y1, x2, y2, score in boxes_scores:
        key = (x1 // 10, y1 // 10, x2 // 10, y2 // 10)
        if key in seen:
            continue
        seen.add(key)
        boxes.append((x1, y1, x2, y2))
        scores.append(score)

    merge_dist = max(32, int(min(h, w) * 0.04))
    boxes, scores = _cluster_fruit_boxes(boxes, scores, merge_dist)
    kept = _nms_boxes(boxes, scores, iou_threshold=0.30)
    score_map = {b: s for b, s in zip(boxes, scores)}
    kept_scores = [score_map.get(b, HEURISTIC_CONFIDENCE) for b in kept]
    ratios = color_ratios(image)
    orange_r = ratios.get("orange", 0.05)
    if orange_r > 0.07:
        big_dist = max(45, int(min(h, w) * 0.055))
        kept, kept_scores = _cluster_fruit_boxes(kept, kept_scores, big_dist)
    kept = _cap_fruit_boxes(kept, kept_scores, orange_r)
    return {"flower": 0, "fruit": len(kept), "boxes": kept}


def detect_heuristic(image: np.ndarray, yolo_fruit: int = 0, yolo_flower: int = 0) -> Dict:
    ratios = color_ratios(image)
    flower_res = detect_flowers_heuristic(image)
    fruit_res = detect_fruits_heuristic(image)
    scene = classify_scene(
        ratios, flower_res["flower"], fruit_res["fruit"], yolo_fruit, yolo_flower
    )

    if scene == "fruit":
        boxes = [(b, "fruit") for b in fruit_res["boxes"]]
        return {
            "flower": 0, "fruit": fruit_res["fruit"],
            "primary": "fruit", "scene": scene, "boxes": boxes, "color_ratios": ratios,
        }

    boxes = [(b, "flower") for b in flower_res["boxes"]]
    return {
        "flower": flower_res["flower"], "fruit": 0,
        "primary": "flower", "scene": "flower", "boxes": boxes, "color_ratios": ratios,
    }


def merge_flower_detections(
    yolo_detections: List[Dict],
    heuristic_boxes: List,
    bloom_ratio: float = 0.2,
) -> List[Dict]:
    flower_yolo = [d for d in yolo_detections if d.get("class") == "flower"]
    h_boxes = [tuple(b) for b, cls in heuristic_boxes if cls == "flower"]
    y_boxes = [tuple(d["bbox"]) for d in flower_yolo]
    y_scores = [float(d.get("confidence", 0.7)) for d in flower_yolo]
    h_scores = [HEURISTIC_CONFIDENCE * 0.85] * len(h_boxes)

    # YOLO 可靠时以 YOLO 为主，启发式只补漏
    if len(flower_yolo) >= 3 and max(y_scores, default=0) >= 0.35:
        merged = _nms_boxes(y_boxes, y_scores, iou_threshold=FLOWER_NMS_IOU)
        merged_scores = {b: s for b, s in zip(y_boxes, y_scores)}
        for hb in h_boxes:
            overlap = False
            for mb in merged:
                cx = (hb[0] + hb[2]) / 2
                cy = (hb[1] + hb[3]) / 2
                if mb[0] <= cx <= mb[2] and mb[1] <= cy <= mb[3]:
                    overlap = True
                    break
            if not overlap:
                hb_area = (hb[2] - hb[0]) * (hb[3] - hb[1])
                if hb_area >= 1200:
                    merged.append(hb)
                    merged_scores[hb] = HEURISTIC_CONFIDENCE * 0.8
        score_list = [merged_scores.get(b, 0.65) for b in merged]
        merged = _cap_flower_boxes(merged, score_list, bloom_ratio, yolo_supported=True)
        return [
            {"class": "flower", "confidence": round(merged_scores.get(b, HEURISTIC_CONFIDENCE), 3), "bbox": list(b)}
            for b in merged
        ]

    all_boxes = y_boxes + h_boxes
    all_scores = y_scores + h_scores
    merged = _nms_boxes(all_boxes, all_scores, iou_threshold=FLOWER_NMS_IOU)
    score_map = {b: s for b, s in zip(all_boxes, all_scores)}
    merged_scores = [score_map.get(b, 0.65) for b in merged]
    merged = _nms_by_distance(merged, merged_scores, min_center_dist_ratio=0.58)
    merged_scores = [score_map.get(b, 0.65) for b in merged]
    merged = _cap_flower_boxes(merged, merged_scores, bloom_ratio, yolo_supported=len(flower_yolo) >= 2)
    return [
        {"class": "flower", "confidence": round(score_map.get(b, HEURISTIC_CONFIDENCE), 3), "bbox": list(b)}
        for b in merged
    ]


def merge_fruit_detections(yolo_detections: List[Dict], heuristic_boxes: List) -> List[Dict]:
    fruit_yolo = [d for d in yolo_detections if d.get("class") == "fruit"]
    y_boxes = [tuple(d["bbox"]) for d in fruit_yolo]
    y_scores = [float(d.get("confidence", 0.7)) for d in fruit_yolo]
    h_boxes = [tuple(b) for b, cls in heuristic_boxes if cls == "fruit"]
    h_scores = [HEURISTIC_CONFIDENCE * 0.9] * len(h_boxes)

    all_boxes = y_boxes + h_boxes
    all_scores = y_scores + h_scores
    if not all_boxes:
        return []

    # YOLO 有可靠检出时以 YOLO 为主，启发式只补漏
    if len(fruit_yolo) >= 2 and max(y_scores, default=0) >= 0.20:
        merged = _nms_boxes(y_boxes, y_scores, iou_threshold=0.35)
        score_map = {b: s for b, s in zip(y_boxes, y_scores)}
        for hb, hs in zip(h_boxes, h_scores):
            cx, cy = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
            covered = any(
                mb[0] <= cx <= mb[2] and mb[1] <= cy <= mb[3] for mb in merged
            )
            if not covered:
                merged.append(hb)
                score_map[hb] = hs
    else:
        merge_dist = 36
        if all_boxes:
            sizes = [max(b[2] - b[0], b[3] - b[1]) for b in all_boxes]
            merge_dist = max(32, int(np.median(sizes) * 0.75))
        merged, merged_scores = _cluster_fruit_boxes(all_boxes, all_scores, merge_dist)
        score_map = {b: s for b, s in zip(merged, merged_scores)}
        merged = _nms_boxes(merged, [score_map[b] for b in merged], iou_threshold=0.30)

    return [
        {"class": "fruit", "confidence": round(score_map.get(b, HEURISTIC_CONFIDENCE), 3), "bbox": list(b)}
        for b in merged
    ]


def detections_from_heuristic_boxes(boxes: List, cls_name: str) -> List[Dict]:
    return [
        {"class": cls_name, "confidence": HEURISTIC_CONFIDENCE, "bbox": list(bbox)}
        for bbox, c in boxes if c == cls_name
    ]
