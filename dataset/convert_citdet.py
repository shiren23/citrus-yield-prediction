"""
CitDet 数据集 COCO → YOLO 格式转换脚本
将 Fruit on Ground 和 Fruit on Tree 统一映射为 mature_fruit (class 0)
"""

import os
import json
import shutil
import random
from pathlib import Path

random.seed(42)

BASE_DIR = Path("F:/文档/25-26/A果园产量预测/opensource_dataset")
OUTPUT_DIR = Path("F:/文档/25-26/A果园产量预测/dataset_citdet")

# COCO 类别 → YOLO 类别映射
# CitDet: 1=Fruit on Ground, 2=Fruit on Tree
# 统一映射为 0 = mature_fruit
CATEGORY_MAP = {1: 0, 2: 0}

def coco_to_yolo_bbox(bbox, img_width, img_height):
    """COCO [x, y, width, height] → YOLO [cx, cy, w, h] (normalized)"""
    x, y, w, h = bbox
    cx = (x + w / 2) / img_width
    cy = (y + h / 2) / img_height
    nw = w / img_width
    nh = h / img_height
    return cx, cy, nw, nh

def convert_split(split_name, images_dir, annot_path, output_images_dir, output_labels_dir, img_id_filter=None):
    """转换单个 split"""
    with open(annot_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 构建 image_id → image info 映射
    images = {img['id']: img for img in data['images']}
    
    # 按 image_id 分组 annotations
    anns_by_img = {}
    for ann in data['annotations']:
        img_id = ann['image_id']
        if img_id_filter and img_id not in img_id_filter:
            continue
        cat_id = ann['category_id']
        if cat_id not in CATEGORY_MAP:
            continue
        if img_id not in anns_by_img:
            anns_by_img[img_id] = []
        anns_by_img[img_id].append(ann)
    
    os.makedirs(output_images_dir, exist_ok=True)
    os.makedirs(output_labels_dir, exist_ok=True)
    
    converted = 0
    for img_id, img_info in images.items():
        if img_id_filter and img_id not in img_id_filter:
            continue
        if img_id not in anns_by_img:
            continue  # 跳过无标注的图片
        
        src_img_path = images_dir / img_info['file_name']
        dst_img_path = output_images_dir / img_info['file_name']
        
        if not src_img_path.exists():
            print(f"[Warning] Image not found: {src_img_path}")
            continue
        
        shutil.copy2(src_img_path, dst_img_path)
        
        # 生成 YOLO 标注文件
        label_name = Path(img_info['file_name']).stem + '.txt'
        label_path = output_labels_dir / label_name
        
        lines = []
        for ann in anns_by_img[img_id]:
            yolo_cls = CATEGORY_MAP[ann['category_id']]
            cx, cy, nw, nh = coco_to_yolo_bbox(
                ann['bbox'], img_info['width'], img_info['height']
            )
            lines.append(f"{yolo_cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
        
        with open(label_path, 'w') as f:
            f.write('\n'.join(lines))
        
        converted += 1
    
    print(f"[{split_name}] Converted {converted} images")
    return converted

def main():
    print("=" * 50)
    print("CitDet COCO → YOLO 转换")
    print("=" * 50)
    
    # 清理输出目录
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. 加载训练集标注，划分 train/val
    train_annot_path = BASE_DIR / "CitDet-train/train/train_annotations.json"
    with open(train_annot_path, 'r') as f:
        train_data = json.load(f)
    
    image_ids = [img['id'] for img in train_data['images']]
    random.shuffle(image_ids)
    split_idx = int(len(image_ids) * 0.8)
    train_ids = set(image_ids[:split_idx])
    val_ids = set(image_ids[split_idx:])
    
    print(f"Total train images: {len(image_ids)}")
    print(f"Train split: {len(train_ids)}, Val split: {len(val_ids)}")
    
    # 2. 转换训练集
    convert_split(
        "train",
        BASE_DIR / "CitDet-train/train/images",
        train_annot_path,
        OUTPUT_DIR / "train/images",
        OUTPUT_DIR / "train/labels",
        img_id_filter=train_ids
    )
    
    # 3. 转换验证集
    convert_split(
        "val",
        BASE_DIR / "CitDet-train/train/images",
        train_annot_path,
        OUTPUT_DIR / "val/images",
        OUTPUT_DIR / "val/labels",
        img_id_filter=val_ids
    )
    
    # 4. 转换测试集（单独保留）
    test_annot_path = BASE_DIR / "CitDet-test/test/test_annotations.json"
    convert_split(
        "test",
        BASE_DIR / "CitDet-test/test/images",
        test_annot_path,
        OUTPUT_DIR / "test/images",
        OUTPUT_DIR / "test/labels"
    )
    
    # 5. 生成 data.yaml
    yaml_content = f"""path: {OUTPUT_DIR.absolute()}
train: train/images
val: val/images
test: test/images
nc: 1
names: ['mature_fruit']
"""
    yaml_path = OUTPUT_DIR / "citdet.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    print(f"[Done] Dataset YAML: {yaml_path}")
    
    # 6. 统计信息
    train_imgs = len(list((OUTPUT_DIR / "train/images").glob('*')))
    val_imgs = len(list((OUTPUT_DIR / "val/images").glob('*')))
    test_imgs = len(list((OUTPUT_DIR / "test/images").glob('*')))
    print(f"\nFinal dataset stats:")
    print(f"  Train: {train_imgs} images")
    print(f"  Val:   {val_imgs} images")
    print(f"  Test:  {test_imgs} images")

if __name__ == "__main__":
    main()
