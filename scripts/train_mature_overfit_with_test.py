"""
柑橘成熟果实检测模型 - 合并测试集后的过拟合版本训练脚本

目标：将 CitDet 数据集的 train + test 合并作为训练集，
      在最小化正则化的前提下提升果实检出数量，供成熟期产量校正使用。

用法：
    python scripts/train_mature_overfit_with_test.py --device 0
    python scripts/train_mature_overfit_with_test.py --device cpu --epochs 300
"""

import argparse
import json
import os
import random
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from ultralytics import YOLO
except ImportError as e:
    print("错误: 未安装 ultralytics，请先执行: pip install ultralytics")
    raise e


BASE_DIR = PROJECT_ROOT / "opensource_dataset"
OUTPUT_DIR = PROJECT_ROOT / "tmp" / "mature_overfit_test"
MERGED_YAML = OUTPUT_DIR / "data.yaml"
RUNS_DIR = PROJECT_ROOT / "runs" / "detect" / "mature_overfit_test"

DEFAULT_BASE_MODEL = PROJECT_ROOT / "models" / "citdet_best.pt"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "citdet_overfit.pt"

# COCO 类别 → YOLO 类别映射
# CitDet: 1=Fruit on Ground, 2=Fruit on Tree
CATEGORY_MAP = {1: 0, 2: 0}

random.seed(42)


def coco_to_yolo_bbox(bbox, img_width, img_height):
    """COCO [x, y, width, height] → YOLO [cx, cy, w, h] (normalized)"""
    x, y, w, h = bbox
    cx = (x + w / 2) / img_width
    cy = (y + h / 2) / img_height
    nw = w / img_width
    nh = h / img_height
    return cx, cy, nw, nh


def convert_coco_split(
    split_name: str,
    images_dir: Path,
    annot_path: Path,
    output_images_dir: Path,
    output_labels_dir: Path,
    img_id_filter=None,
):
    """将 COCO 格式的 CitDet 子集转换为 YOLO 格式。"""
    with open(annot_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    images = {img["id"]: img for img in data["images"]}

    anns_by_img = {}
    for ann in data["annotations"]:
        img_id = ann["image_id"]
        if img_id_filter and img_id not in img_id_filter:
            continue
        cat_id = ann["category_id"]
        if cat_id not in CATEGORY_MAP:
            continue
        anns_by_img.setdefault(img_id, []).append(ann)

    os.makedirs(output_images_dir, exist_ok=True)
    os.makedirs(output_labels_dir, exist_ok=True)

    converted = 0
    for img_id, img_info in images.items():
        if img_id_filter and img_id not in img_id_filter:
            continue
        if img_id not in anns_by_img:
            continue

        src_img_path = images_dir / img_info["file_name"]
        dst_img_path = output_images_dir / img_info["file_name"]

        if not src_img_path.exists():
            print(f"[Warning] Image not found: {src_img_path}")
            continue

        shutil.copy2(src_img_path, dst_img_path)

        label_name = Path(img_info["file_name"]).stem + ".txt"
        label_path = output_labels_dir / label_name

        lines = []
        for ann in anns_by_img[img_id]:
            cx, cy, nw, nh = coco_to_yolo_bbox(
                ann["bbox"], img_info["width"], img_info["height"]
            )
            lines.append(f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        with open(label_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        converted += 1

    print(f"[{split_name}] Converted {converted} images")
    return converted


def prepare_merged_dataset():
    """准备合并 train + test 的数据集，val 从原 train 中 80/20 划分。"""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    train_images_dir = BASE_DIR / "CitDet-train" / "train" / "images"
    train_annot_path = BASE_DIR / "CitDet-train" / "train" / "train_annotations.json"
    test_images_dir = BASE_DIR / "CitDet-test" / "test" / "images"
    test_annot_path = BASE_DIR / "CitDet-test" / "test" / "test_annotations.json"

    # 从 train 中划分 train/val（80/20）
    with open(train_annot_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)
    image_ids = [img["id"] for img in train_data["images"]]
    random.shuffle(image_ids)
    split_idx = int(len(image_ids) * 0.8)
    train_ids = set(image_ids[:split_idx])
    val_ids = set(image_ids[split_idx:])

    print("=" * 60)
    print("准备成熟果实过拟合数据集（train + test 合并）")
    print(f"  原 train: {len(image_ids)} 张，划分 train={len(train_ids)}, val={len(val_ids)}")
    print("=" * 60)

    # 转换 train 部分
    convert_coco_split(
        "train",
        train_images_dir,
        train_annot_path,
        OUTPUT_DIR / "train" / "images",
        OUTPUT_DIR / "train" / "labels",
        img_id_filter=train_ids,
    )

    # 转换 val 部分
    convert_coco_split(
        "val",
        train_images_dir,
        train_annot_path,
        OUTPUT_DIR / "valid" / "images",
        OUTPUT_DIR / "valid" / "labels",
        img_id_filter=val_ids,
    )

    # 转换 test 部分，合并到 train
    convert_coco_split(
        "test",
        test_images_dir,
        test_annot_path,
        OUTPUT_DIR / "train" / "images",
        OUTPUT_DIR / "train" / "labels",
    )

    yaml_content = f"""path: {OUTPUT_DIR.absolute()}
train: train/images
val: valid/images
nc: 1
names: ['mature_fruit']
"""
    MERGED_YAML.write_text(yaml_content, encoding="utf-8")
    print(f"[Done] Dataset YAML: {MERGED_YAML}")

    train_imgs = len(list((OUTPUT_DIR / "train" / "images").glob("*")))
    val_imgs = len(list((OUTPUT_DIR / "valid" / "images").glob("*")))
    print(f"\nFinal dataset stats:")
    print(f"  Train (含 test): {train_imgs} images")
    print(f"  Val:             {val_imgs} images")


def backup_model(model_path: Path):
    if model_path.exists():
        bak_path = model_path.with_suffix(".pt.bak")
        counter = 1
        while bak_path.exists():
            bak_path = model_path.with_suffix(f".pt.bak{counter}")
            counter += 1
        shutil.copy2(model_path, bak_path)
        print(f"[Backup] 旧模型已备份: {bak_path}")


def find_best_weight(runs_dir: Path):
    """查找训练生成的 best.pt，兼容 Ultralytics 自动添加 -2/-3 后缀的情况。"""
    # 优先精确匹配目标目录
    candidates = sorted(runs_dir.rglob("weights/best.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]

    # 若目标目录被重命名（如 mature_overfit_test-2），在同级目录中按名称匹配最新目录
    if runs_dir.parent.exists():
        pattern = runs_dir.name + "*"
        sibling_candidates = sorted(
            runs_dir.parent.rglob(pattern + "/weights/best.pt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if sibling_candidates:
            return sibling_candidates[0]
    return None


def train_mature_overfit(
    data_yaml: Path,
    base_model: Path,
    output_model: Path,
    epochs: int,
    imgsz: int,
    batch: int,
    device: str,
):
    backup_model(output_model)

    if base_model.exists():
        print(f"[Train] 从现有模型继续训练: {base_model}")
        model = YOLO(str(base_model))
    else:
        print("[Train] 未找到基础模型，从 yolov8n.pt 开始训练")
        model = YOLO("yolov8n.pt")

    print("=" * 60)
    print("开始训练成熟果实过拟合模型（train + test）")
    print(f"  数据集: {data_yaml}")
    print(f"  模型: yolov8n")
    print(f"  epochs={epochs}, imgsz={imgsz}, batch={batch}, device={device}")
    print("  增强: 全部关闭（减少正则化，促进拟合）")
    print("  早停: 关闭")
    print("=" * 60)

    model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=str(RUNS_DIR.parent),
        name=RUNS_DIR.name,
        patience=0,                 # 关闭早停
        save=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.0005,
        lrf=0.005,
        momentum=0.937,
        weight_decay=0.0,           # 关闭权重衰减
        warmup_epochs=1.0,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        mosaic=0.0,
        mixup=0.0,
        copy_paste=0.0,
        hsv_h=0.0,
        hsv_s=0.0,
        hsv_v=0.0,
        degrees=0.0,
        translate=0.0,
        scale=0.0,
        fliplr=0.0,
        erasing=0.0,
        auto_augment=None,
        amp=False,
        workers=0,
        val=True,
        plots=True,
    )

    best_pt = find_best_weight(RUNS_DIR)
    if best_pt and best_pt.exists():
        shutil.copy2(best_pt, output_model)
        print(f"[Train] 过拟合模型已保存: {output_model}")
    else:
        print("[Train] 警告: 未找到训练生成的 best.pt")

    print("[Train] 开始验证...")
    metrics = model.val(data=str(data_yaml), imgsz=imgsz, device=device)
    print(f"[Validate] mAP@50-95: {metrics.box.map:.4f}")
    print(f"[Validate] mAP@50:    {metrics.box.map50:.4f}")
    print(f"[Validate] mAP@75:    {metrics.box.map75:.4f}")


def main():
    parser = argparse.ArgumentParser(description="成熟果实过拟合模型训练脚本（含 test 集）")
    parser.add_argument("--base-model", type=str, default=str(DEFAULT_BASE_MODEL),
                        help=f"基础模型路径，默认: {DEFAULT_BASE_MODEL}")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT),
                        help=f"输出模型路径，默认: {DEFAULT_OUTPUT}")
    parser.add_argument("--epochs", type=int, default=300, help="训练轮数，默认 300")
    parser.add_argument("--imgsz", type=int, default=640, help="输入分辨率，默认 640")
    parser.add_argument("--batch", type=int, default=8, help="Batch size，默认 8")
    parser.add_argument("--device", type=str, default="cpu",
                        help="训练设备，例如 cpu、0；默认 cpu")
    args = parser.parse_args()

    prepare_merged_dataset()
    train_mature_overfit(
        data_yaml=MERGED_YAML,
        base_model=Path(args.base_model),
        output_model=Path(args.output),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
    )


if __name__ == "__main__":
    main()
