"""
柑橘花朵检测模型继续训练脚本

基于当前 models/flowers_best.pt 在花朵数据集上微调，支持在本地 CPU/GPU 继续训练。
用法示例：
    python scripts/train_flower.py --epochs 100 --imgsz 1280 --model-size s --device 0
    python scripts/train_flower.py --epochs 50  --imgsz 640  --model-size n --device cpu
"""

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# 把项目根目录加入 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from ultralytics import YOLO
except ImportError as e:
    print("错误: 未安装 ultralytics，请先执行: pip install ultralytics")
    raise e


DEFAULT_DATA_YAML = PROJECT_ROOT / "opensource_dataset" / "orange flowers.v2i.yolov8" / "data.yaml"
DEFAULT_BASE_MODEL = PROJECT_ROOT / "models" / "flowers_best.pt"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "flowers_best.pt"
RUNS_DIR = PROJECT_ROOT / "runs" / "detect" / "flower_tune"


def backup_model(model_path: Path):
    """训练前备份旧模型，避免覆盖后无法回退。"""
    if model_path.exists():
        bak_path = model_path.with_suffix(".pt.bak")
        # 保留最近一次备份即可；如需多份，可加上时间戳
        counter = 1
        while bak_path.exists():
            bak_path = model_path.with_suffix(f".pt.bak{counter}")
            counter += 1
        shutil.copy2(model_path, bak_path)
        print(f"[Backup] 旧模型已备份: {bak_path}")


def find_best_weight(runs_dir: Path):
    """在 Ultralytics 训练输出目录中查找 best.pt。"""
    candidates = sorted(runs_dir.rglob("weights/best.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def train_flower(
    data_yaml: Path,
    base_model: Path,
    output_model: Path,
    model_size: str,
    epochs: int,
    imgsz: int,
    batch: int,
    device: str,
    patience: int,
    augment: dict,
):
    # 1. 备份旧模型
    backup_model(output_model)

    # 2. 加载基础模型：优先使用已有 flowers_best.pt，不存在则加载对应尺寸的 YOLOv8 预训练权重
    if base_model.exists():
        print(f"[Train] 从现有模型继续训练: {base_model}")
        model = YOLO(str(base_model))
    else:
        pretrained = f"yolov8{model_size}.pt"
        print(f"[Train] 未找到 {base_model}，从 {pretrained} 开始训练")
        model = YOLO(pretrained)

    # 3. 开始训练
    print("=" * 60)
    print(f"开始花朵检测模型微调")
    print(f"  数据集: {data_yaml}")
    print(f"  模型: yolov8{model_size}")
    print(f"  epochs={epochs}, imgsz={imgsz}, batch={batch}, device={device}")
    print("=" * 60)

    model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=str(RUNS_DIR.parent),
        name=RUNS_DIR.name,
        patience=patience,
        save=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        workers=0,
        val=True,
        plots=True,
        **augment,
    )

    # 4. 复制最佳模型到目标位置
    best_pt = find_best_weight(RUNS_DIR)
    if best_pt and best_pt.exists():
        shutil.copy2(best_pt, output_model)
        print(f"[Train] 最佳模型已保存: {output_model}")
    else:
        print("[Train] 警告: 未找到训练生成的 best.pt")

    # 5. 验证
    print("[Train] 开始验证...")
    metrics = model.val(data=str(data_yaml), imgsz=imgsz, device=device)
    print(f"[Validate] mAP@50-95: {metrics.box.map:.4f}")
    print(f"[Validate] mAP@50:    {metrics.box.map50:.4f}")
    print(f"[Validate] mAP@75:    {metrics.box.map75:.4f}")


def parse_augment_args(args):
    """把命令行增强参数整理成 Ultralytics train() 可接收的字典。"""
    return {
        "mosaic": args.mosaic,
        "mixup": args.mixup,
        "copy_paste": args.copy_paste,
        "hsv_h": args.hsv_h,
        "hsv_s": args.hsv_s,
        "hsv_v": args.hsv_v,
        "degrees": args.degrees,
        "translate": args.translate,
        "scale": args.scale,
        "fliplr": args.fliplr,
    }


def main():
    parser = argparse.ArgumentParser(description="柑橘花朵检测模型微调脚本")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_YAML),
                        help=f"花朵数据集 YAML 路径，默认: {DEFAULT_DATA_YAML}")
    parser.add_argument("--base-model", type=str, default=str(DEFAULT_BASE_MODEL),
                        help=f"基础模型路径，默认: {DEFAULT_BASE_MODEL}")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT),
                        help=f"输出模型路径，默认: {DEFAULT_OUTPUT}")
    parser.add_argument("--model-size", type=str, default="n", choices=["n", "s", "m", "l", "x"],
                        help="YOLOv8 模型尺寸，默认 n（CPU 推荐 n/s）")
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数，默认 100")
    parser.add_argument("--imgsz", type=int, default=1280,
                        help="输入分辨率，默认 1280；显存不足可改为 640/960")
    parser.add_argument("--batch", type=int, default=8, help="Batch size，默认 8")
    parser.add_argument("--device", type=str, default="cpu",
                        help="训练设备，例如 cpu、0、0,1；默认 cpu")
    parser.add_argument("--patience", type=int, default=20, help="早停耐心值，默认 20")

    # 数据增强参数
    parser.add_argument("--mosaic", type=float, default=1.0)
    parser.add_argument("--mixup", type=float, default=0.2)
    parser.add_argument("--copy-paste", type=float, default=0.2)
    parser.add_argument("--hsv-h", type=float, default=0.02)
    parser.add_argument("--hsv-s", type=float, default=0.7)
    parser.add_argument("--hsv-v", type=float, default=0.4)
    parser.add_argument("--degrees", type=float, default=10.0)
    parser.add_argument("--translate", type=float, default=0.1)
    parser.add_argument("--scale", type=float, default=0.5)
    parser.add_argument("--fliplr", type=float, default=0.5)

    args = parser.parse_args()

    data_yaml = Path(args.data)
    base_model = Path(args.base_model)
    output_model = Path(args.output)

    if not data_yaml.exists():
        raise FileNotFoundError(f"数据集配置不存在: {data_yaml}")

    augment = parse_augment_args(args)

    train_flower(
        data_yaml=data_yaml,
        base_model=base_model,
        output_model=output_model,
        model_size=args.model_size,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        patience=args.patience,
        augment=augment,
    )


if __name__ == "__main__":
    main()
