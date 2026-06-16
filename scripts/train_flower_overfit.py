"""
柑橘花朵检测模型 - 过拟合版本训练脚本

目标：在现有小规模花朵数据集上最大化训练/验证指标，供测试人员对比。
规则：不合并 test 集，仅使用 data.yaml 中定义的 train/valid 划分。

用法：
    python scripts/train_flower_overfit.py --device 0
"""

import argparse
import os
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


DEFAULT_DATA_YAML = PROJECT_ROOT / "opensource_dataset" / "orange flowers.v2i.yolov8" / "data.yaml"
DEFAULT_BASE_MODEL = PROJECT_ROOT / "models" / "flowers_best.pt"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "flowers_overfit.pt"
RUNS_DIR = PROJECT_ROOT / "runs" / "detect" / "flower_overfit"


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
    candidates = sorted(runs_dir.rglob("weights/best.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def train_overfit(
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
    print("开始训练花朵检测过拟合模型")
    print(f"  数据集: {data_yaml}")
    print(f"  模型: yolov8n")
    print(f"  epochs={epochs}, imgsz={imgsz}, batch={batch}, device={device}")
    print("  增强: 关闭（减少正则化，促进拟合）")
    print("  早停: 关闭")
    print("=" * 60)

    # 关闭大部分数据增强与正则化，以在训练集上获得更高拟合度
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
        lr0=0.0005,                 # 较低初始学习率，后期精细拟合
        lrf=0.005,
        momentum=0.937,
        weight_decay=0.0,           # 关闭权重衰减，降低正则化
        warmup_epochs=1.0,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        mosaic=0.0,                 # 关闭 mosaic
        mixup=0.0,                  # 关闭 mixup
        copy_paste=0.0,             # 关闭 copy-paste
        hsv_h=0.0,                  # 关闭 HSV 色调
        hsv_s=0.0,                  # 关闭 HSV 饱和度
        hsv_v=0.0,                  # 关闭 HSV 亮度
        degrees=0.0,                # 关闭旋转
        translate=0.0,              # 关闭平移
        scale=0.0,                  # 关闭缩放
        fliplr=0.0,                 # 关闭水平翻转
        erasing=0.0,
        auto_augment=None,
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
    parser = argparse.ArgumentParser(description="柑橘花朵检测过拟合模型训练脚本")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_YAML),
                        help=f"数据集 YAML 路径，默认: {DEFAULT_DATA_YAML}")
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

    data_yaml = Path(args.data)
    base_model = Path(args.base_model)
    output_model = Path(args.output)

    if not data_yaml.exists():
        raise FileNotFoundError(f"数据集配置不存在: {data_yaml}")

    train_overfit(
        data_yaml=data_yaml,
        base_model=base_model,
        output_model=output_model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
    )


if __name__ == "__main__":
    main()
