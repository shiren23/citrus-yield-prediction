"""
合并 Roboflow 花朵数据集与 Kaggle CitDet 果实数据集
输出符合本项目 YOLOv8 训练格式的 2 类数据集：flower + fruit
"""

import argparse
import os
import random
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "dataset"

# CitDet 类别：0=树上果(orange_T), 1=地上落果(orange_G，默认跳过)
CITDET_TREE_CLASS = 0
CITDET_GROUND_CLASS = 1

TARGET_CLASSES = {
    "flower": 0,
    "fruit": 1,
}


def find_split_dirs(source: Path) -> dict:
    """在解压目录中查找 train/valid(val) 的 images 与 labels 路径"""
    candidates = {
        "train": {"images": None, "labels": None},
        "val": {"images": None, "labels": None},
    }

    for split, aliases in {
        "train": ["train"],
        "val": ["valid", "val"],
    }.items():
        for alias in aliases:
            img_dir = source / alias / "images"
            lbl_dir = source / alias / "labels"
            if img_dir.is_dir() and lbl_dir.is_dir():
                candidates[split]["images"] = img_dir
                candidates[split]["labels"] = lbl_dir
                break

    return candidates


def remap_label_file(src_label: Path, dst_label: Path, class_map: dict,
                     skip_classes: set = None):
    """复制并重映射标注类别 ID"""
    skip_classes = skip_classes or set()
    lines_out = []

    with open(src_label, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            cls_id = int(float(parts[0]))
            if cls_id in skip_classes:
                continue
            if cls_id not in class_map:
                continue
            parts[0] = str(class_map[cls_id])
            lines_out.append(" ".join(parts))

    if lines_out:
        dst_label.parent.mkdir(parents=True, exist_ok=True)
        with open(dst_label, "w", encoding="utf-8") as f:
            f.write("\n".join(lines_out) + "\n")
        return True
    return False


def copy_pair(img_path: Path, label_path: Path, dst_img: Path, dst_lbl: Path,
              class_map: dict, skip_classes: set = None, prefix: str = ""):
    """复制图片并重映射标注"""
    stem = f"{prefix}{img_path.stem}"
    dst_img = dst_img.with_name(stem + img_path.suffix.lower())
    dst_lbl = dst_lbl.with_name(stem + ".txt")

    if not label_path.exists():
        return False

    ok = remap_label_file(label_path, dst_lbl, class_map, skip_classes)
    if not ok:
        if dst_lbl.exists():
            dst_lbl.unlink()
        return False

    dst_img.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(img_path, dst_img)
    return True


def import_flower_balanced(
    flower_root: Path,
    output: Path,
    val_ratio: float = 0.2,
    oversample: int = 4,
    seed: int = 42,
) -> dict:
    """
    导入花朵数据：train 划分验证集、test 并入 val、训练集过采样以缓解类别失衡。
    """
    stats = {"train": 0, "val": 0, "skipped": 0}
    rng = random.Random(seed)
    class_map = {0: TARGET_CLASSES["flower"]}

    train_img = flower_root / "train" / "images"
    train_lbl = flower_root / "train" / "labels"
    test_img = flower_root / "test" / "images"
    test_lbl = flower_root / "test" / "labels"

    pairs = []
    if train_img.is_dir() and train_lbl.is_dir():
        for img_path in sorted(train_img.iterdir()):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
                continue
            lbl = train_lbl / f"{img_path.stem}.txt"
            if lbl.exists():
                pairs.append(("train", img_path, lbl))

    val_pairs = []
    if test_img.is_dir() and test_lbl.is_dir():
        for img_path in sorted(test_img.iterdir()):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
                continue
            lbl = test_lbl / f"{img_path.stem}.txt"
            if lbl.exists():
                val_pairs.append((img_path, lbl))

    train_only = [p for p in pairs if p[0] == "train"]
    rng.shuffle(train_only)
    val_count = max(1, int(len(train_only) * val_ratio))
    holdout = train_only[:val_count]
    train_keep = train_only[val_count:]

    for _, img_path, lbl in holdout:
        dst_img = output / "images" / "val" / img_path.name
        dst_lbl = output / "labels" / "val" / f"{img_path.stem}.txt"
        if copy_pair(img_path, lbl, dst_img, dst_lbl, class_map, prefix="flower_"):
            stats["val"] += 1

    for img_path, lbl in val_pairs:
        dst_img = output / "images" / "val" / img_path.name
        dst_lbl = output / "labels" / "val" / f"{img_path.stem}.txt"
        if copy_pair(img_path, lbl, dst_img, dst_lbl, class_map, prefix="flower_test_"):
            stats["val"] += 1

    oversample = max(1, oversample)
    for rep in range(oversample):
        prefix = "flower_" if rep == 0 else f"flower_{rep}_"
        for _, img_path, lbl in train_keep:
            dst_img = output / "images" / "train" / img_path.name
            dst_lbl = output / "labels" / "train" / f"{img_path.stem}.txt"
            if copy_pair(img_path, lbl, dst_img, dst_lbl, class_map, prefix=prefix):
                stats["train"] += 1

    return stats


def import_source(source: Path, output: Path, split_dirs: dict,
                  class_map: dict, prefix: str,
                  skip_classes: set = None) -> dict:
    """导入一个数据源到 output 目录"""
    stats = {"train": 0, "val": 0, "skipped": 0}

    for split in ("train", "val"):
        img_dir = split_dirs[split]["images"]
        lbl_dir = split_dirs[split]["labels"]
        if not img_dir or not lbl_dir:
            continue

        for img_path in sorted(img_dir.iterdir()):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
                continue
            label_path = lbl_dir / f"{img_path.stem}.txt"
            dst_img = output / "images" / split / img_path.name
            dst_lbl = output / "labels" / split / f"{img_path.stem}.txt"
            if copy_pair(img_path, label_path, dst_img, dst_lbl,
                         class_map, skip_classes, prefix=prefix):
                stats[split] += 1
            else:
                stats["skipped"] += 1

    return stats


def write_citrus_yaml(output: Path):
    """生成训练用 citrus.yaml"""
    yaml_path = output / "citrus.yaml"
    content = f"""path: {output.as_posix()}
train: images/train
val: images/val
nc: 2
names: ['flower', 'fruit']
"""
    yaml_path.write_text(content, encoding="utf-8")
    print(f"[Merge] 已生成配置: {yaml_path}")


def clear_output_data(output: Path):
    """清空输出目录中的旧图片和标注"""
    for sub in ("images/train", "images/val", "labels/train", "labels/val"):
        folder = output / sub
        if folder.is_dir():
            for f in folder.iterdir():
                if f.is_file():
                    f.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="合并 Roboflow 花朵 + CitDet 果实数据集（2 类：flower/fruit）"
    )
    parser.add_argument(
        "--flower-dir", required=True,
        help="Roboflow 花朵数据集解压目录（含 train/valid 子目录）"
    )
    parser.add_argument(
        "--fruit-dir", required=True,
        help="CitDet 果实数据集解压目录（含 train/val 子目录）"
    )
    parser.add_argument(
        "--output", default=str(DEFAULT_OUTPUT),
        help="输出目录，默认 dataset/"
    )
    parser.add_argument(
        "--keep-ground-fruit", action="store_true",
        help="保留 CitDet 地上落果（默认跳过）"
    )
    parser.add_argument(
        "--no-clear", action="store_true",
        help="不清空输出目录中的旧数据"
    )
    parser.add_argument(
        "--flower-oversample", type=int, default=4,
        help="花朵训练图过采样倍数（缓解类别失衡，默认 4）"
    )
    parser.add_argument(
        "--flower-val-ratio", type=float, default=0.2,
        help="从花朵 train 中划分验证集比例（默认 0.2）"
    )
    args = parser.parse_args()

    flower_root = Path(args.flower_dir).resolve()
    fruit_root = Path(args.fruit_dir).resolve()
    output = Path(args.output).resolve()

    if not flower_root.is_dir():
        raise FileNotFoundError(f"花朵数据集目录不存在: {flower_root}")
    if not fruit_root.is_dir():
        raise FileNotFoundError(f"果实数据集目录不存在: {fruit_root}")

    flower_splits = find_split_dirs(flower_root)
    fruit_splits = find_split_dirs(fruit_root)

    for name, splits in [("花朵", flower_splits), ("果实", fruit_splits)]:
        if not splits["train"]["images"]:
            raise FileNotFoundError(f"{name}数据集未找到 train/images 与 train/labels")

    for sub in ("images/train", "images/val", "labels/train", "labels/val"):
        (output / sub).mkdir(parents=True, exist_ok=True)

    if not args.no_clear:
        clear_output_data(output)
        print(f"[Merge] 已清空旧数据: {output}")

    # Roboflow flower: 划分 val + 过采样 train
    flower_stats = import_flower_balanced(
        flower_root, output,
        val_ratio=args.flower_val_ratio,
        oversample=args.flower_oversample,
    )
    print(f"[Merge] 花朵数据: train={flower_stats['train']}, val={flower_stats['val']}, "
          f"skipped={flower_stats['skipped']}")

    # CitDet: class 0(树上果) → fruit(1), class 1(落果) 默认跳过
    skip = set()
    if not args.keep_ground_fruit:
        skip.add(CITDET_GROUND_CLASS)
    fruit_map = {CITDET_TREE_CLASS: TARGET_CLASSES["fruit"]}
    if args.keep_ground_fruit:
        fruit_map[CITDET_GROUND_CLASS] = TARGET_CLASSES["fruit"]

    fruit_stats = import_source(
        fruit_root, output, fruit_splits, fruit_map,
        prefix="fruit_", skip_classes=skip
    )
    print(f"[Merge] 果实数据: train={fruit_stats['train']}, val={fruit_stats['val']}, "
          f"skipped={fruit_stats['skipped']}")

    write_citrus_yaml(output)

    total_train = flower_stats["train"] + fruit_stats["train"]
    total_val = flower_stats["val"] + fruit_stats["val"]
    print("\n" + "=" * 50)
    print("数据集合并完成！")
    print(f"  训练集: {total_train} 张")
    print(f"  验证集: {total_val} 张")
    print(f"  类别: flower(0), fruit(1)")
    print("\n下一步训练命令:")
    print(f"  python models/train.py --data {output / 'citrus.yaml'} --epochs 100 --device cpu")
    print("=" * 50)


if __name__ == "__main__":
    main()
