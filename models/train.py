"""
柑橘产量预测系统 - YOLOv8 模型训练脚本
支持花朵、幼果、成熟果实的目标检测微调
"""

import os
import yaml
import argparse
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    print("警告: ultralytics 未安装，训练功能不可用")


# 默认数据集配置（用于自动生成数据集YAML）
DEFAULT_DATASET_CONFIG = {
    "path": "../dataset",
    "train": "images/train",
    "val": "images/val",
    "names": {
        0: "flower",
        1: "fruit",
    },
}


def create_dataset_yaml(output_path: str = "dataset/citrus.yaml",
                        dataset_root: str = "dataset") -> str:
    """
    自动生成数据集配置文件
    Args:
        output_path: 输出的YAML文件路径
        dataset_root: 数据集根目录绝对路径
    Returns:
        yaml文件路径
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    config = {
        "path": os.path.abspath(dataset_root),
        "train": "images/train",
        "val": "images/val",
        "nc": 2,
        "names": ["flower", "fruit"],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    print(f"[Train] 数据集配置已生成: {output_path}")
    return output_path


def train_model(data_yaml: str,
                model_size: str = "n",
                epochs: int = 100,
                imgsz: int = 640,
                batch: int = 16,
                device: str = "cpu",
                project: str = "models/runs",
                name: str = "citrus_detect",
                patience: int = 20) -> str:
    """
    训练YOLOv8柑橘检测模型
    Args:
        data_yaml: 数据集YAML配置文件路径
        model_size: 模型大小 n/s/m/l/x
        epochs: 训练轮数
        imgsz: 输入图片尺寸
        batch: batch size
        device: 训练设备 cpu/cuda/0/1...
        project: 训练结果保存目录
        name: 训练任务名称
        patience: 早停耐心值
    Returns:
        最佳模型权重路径
    """
    if YOLO is None:
        raise RuntimeError("ultralytics 未安装")

    # 加载预训练模型
    pretrained = f"yolov8{model_size}.pt"
    print(f"[Train] 加载预训练模型: {pretrained}")
    model = YOLO(pretrained)

    # 开始训练
    print(f"[Train] 开始训练: epochs={epochs}, imgsz={imgsz}, batch={batch}, device={device}")
    model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
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
        cls=1.0,
        dfl=1.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        nbs=64,
        workers=0,
        val=True,
        plots=True,
    )

    # 训练完成后，查找 best.pt（Ultralytics 常保存到 runs/detect/{project}/{name}/）
    candidates = [
        os.path.join(project, name, "weights", "best.pt"),
        os.path.join("runs", "detect", project, name, "weights", "best.pt"),
    ]
    for search_root in (Path("runs/detect"), Path("runs"), Path(project)):
        if search_root.exists():
            for p in sorted(search_root.rglob("best.pt"), key=lambda x: x.stat().st_mtime, reverse=True):
                candidates.append(str(p))

    best_path = ""
    seen = set()
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)
        if os.path.exists(path):
            best_path = path
            break
    if os.path.exists(best_path):
        print(f"[Train] 训练完成，最佳模型: {best_path}")
        # 复制到 models/best.pt
        import shutil
        target = os.path.join(os.path.dirname(__file__), "best.pt")
        shutil.copy2(best_path, target)
        print(f"[Train] 模型已复制到: {target}")
        return target
    else:
        print(f"[Train] 警告: 未找到最佳模型文件")
        return ""


def validate_model(weights_path: str,
                   data_yaml: str,
                   imgsz: int = 640,
                   device: str = "cpu"):
    """
    验证模型性能
    """
    if YOLO is None:
        raise RuntimeError("ultralytics 未安装")

    model = YOLO(weights_path)
    metrics = model.val(data=data_yaml, imgsz=imgsz, device=device)
    result = {
        "map50_95": float(metrics.box.map),
        "map50": float(metrics.box.map50),
        "map75": float(metrics.box.map75),
    }
    print(f"[Validate] mAP@50-95: {result['map50_95']:.4f}")
    print(f"[Validate] mAP@50: {result['map50']:.4f}")
    return result


def export_model(weights_path: str, format: str = "onnx") -> str:
    """
    导出模型为其他格式（ONNX/TensorRT等）
    """
    if YOLO is None:
        raise RuntimeError("ultralytics 未安装")

    model = YOLO(weights_path)
    path = model.export(format=format)
    print(f"[Export] 模型已导出: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="柑橘检测模型训练")
    parser.add_argument("--data", type=str, default="dataset/citrus.yaml", help="数据集YAML路径")
    parser.add_argument("--model-size", type=str, default="n", choices=["n", "s", "m", "l", "x"])
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--project", type=str, default="models/runs")
    parser.add_argument("--name", type=str, default="citrus_detect")
    parser.add_argument("--patience", type=int, default=20, help="早停耐心值")
    parser.add_argument("--validate", action="store_true", help="训练后验证")
    parser.add_argument("--export", type=str, default="", help="导出格式(onnx/engine等)")
    args = parser.parse_args()

    # 若YAML不存在，自动生成一个模板
    if not os.path.exists(args.data):
        print(f"[Train] 数据集配置不存在，生成模板: {args.data}")
        create_dataset_yaml(args.data)
        print("[Train] 请准备数据集后重新运行训练")
        return

    # 训练
    best_path = train_model(
        data_yaml=args.data,
        model_size=args.model_size,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        patience=args.patience,
    )

    # 验证
    if args.validate and best_path:
        validate_model(best_path, args.data, imgsz=args.imgsz, device=args.device)

    # 导出
    if args.export and best_path:
        export_model(best_path, format=args.export)


if __name__ == "__main__":
    main()
