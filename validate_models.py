"""
验证训练好的两个模型：成熟果实 + 花朵
在测试集上跑推理，生成带标注框的可视化结果
"""

import os
import random
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

random.seed(42)

BASE_DIR = Path("F:/文档/25-26/A果园产量预测")
OUTPUT_DIR = BASE_DIR / "validation_results"
OUTPUT_DIR.mkdir(exist_ok=True)

def draw_detections(image_path, results, class_names, class_colors, save_path):
    """在图片上绘制检测框和标签"""
    img = cv2.imread(str(image_path))
    if img is None:
        return False
    
    boxes = results[0].boxes
    for box in boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        cls_name = class_names[cls_id] if cls_id < len(class_names) else f"class_{cls_id}"
        color = class_colors.get(cls_name, (0, 255, 0))
        
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{cls_name} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    cv2.imwrite(str(save_path), img)
    return True

def validate_model(model_path, test_images_dir, class_names, class_colors, output_subdir, num_samples=6):
    """验证单个模型"""
    print(f"\n{'='*50}")
    print(f"验证模型: {model_path}")
    print(f"{'='*50}")
    
    model = YOLO(str(model_path))
    
    image_files = list(Path(test_images_dir).glob("*.jpg")) + list(Path(test_images_dir).glob("*.jpeg")) + list(Path(test_images_dir).glob("*.png"))
    image_files = sorted(image_files)
    
    if len(image_files) > num_samples:
        image_files = random.sample(image_files, num_samples)
    
    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(exist_ok=True)
    
    total_boxes = 0
    for img_path in image_files:
        results = model.predict(str(img_path), imgsz=640, conf=0.25, verbose=False)
        num_boxes = len(results[0].boxes)
        total_boxes += num_boxes
        
        save_path = out_dir / img_path.name
        success = draw_detections(img_path, results, class_names, class_colors, save_path)
        
        if success:
            print(f"  ✓ {img_path.name} → {num_boxes} 个目标检测")
        else:
            print(f"  ✗ {img_path.name} → 读取失败")
    
    print(f"\n  共检测 {total_boxes} 个目标，结果保存在: {out_dir}")
    return out_dir

def main():
    print("="*50)
    print("模型验证脚本")
    print("="*50)
    
    # 1. 验证成熟果实模型 (CitDet)
    citdet_dir = validate_model(
        BASE_DIR / "models/citdet_best.pt",
        BASE_DIR / "dataset_citdet/test/images",
        class_names=["mature_fruit"],
        class_colors={"mature_fruit": (255, 165, 0)},  # 橙色
        output_subdir="citdet_results",
        num_samples=6
    )
    
    # 2. 验证花朵模型 (orange flowers)
    flowers_dir = validate_model(
        BASE_DIR / "models/flowers_best.pt",
        BASE_DIR / "opensource_dataset/orange flowers.v2i.yolov8/test/images",
        class_names=["flower"],
        class_colors={"flower": (255, 192, 203)},  # 粉色
        output_subdir="flowers_results",
        num_samples=6
    )
    
    print(f"\n{'='*50}")
    print("验证完成！")
    print(f"{'='*50}")
    print(f"成熟果实检测结果: {citdet_dir}")
    print(f"花朵检测结果: {flowers_dir}")

if __name__ == "__main__":
    main()
