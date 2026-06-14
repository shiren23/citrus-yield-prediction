"""
柑橘产量预测系统 - 命令行工具
支持对单张图片或视频进行快速产量预测

用法示例:
    python cli.py --image sample_data/sample_00.jpg --variety 奉节脐橙 --trees 5
    python cli.py --video sample.mp4 --variety 忠县柑橘 --trees 10
    python cli.py --image sample_data/sample_00.jpg --output result.json
"""

import os
import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import get_available_varieties
from core.detector import CitrusDetector, get_detector
from core.stage_classifier import StageClassifier
from core.yield_estimator import YieldEstimator
from core.risk_alert import RiskAlerter
from data.database import get_db


def predict_image(image_path: str, variety: str, tree_count: int, save_db: bool = False):
    """对图片进行预测"""
    dt = get_detector(device="cpu")
    result = dt.detect_image(image_path)

    counts = result["counts"]
    total = result["total"]

    stage_info = StageClassifier.classify(counts, total)
    estimator = YieldEstimator(variety)
    yield_result = estimator.estimate(counts, stage_info, tree_count=tree_count)

    alerter = RiskAlerter(variety)
    risk = alerter.evaluate(counts, stage_info)

    output = {
        "input_type": "image",
        "input_path": image_path,
        "variety": variety,
        "tree_count": tree_count,
        "timestamp": datetime.now().isoformat(),
        "detection": {
            "flower": counts.get("flower", 0),
            "immature_fruit": counts.get("immature_fruit", 0),
            "mature_fruit": counts.get("mature_fruit", 0),
            "total": total,
        },
        "stage": {
            "stage": stage_info["stage"],
            "stage_name": stage_info["stage_name"],
            "confidence": stage_info["confidence"],
            "description": stage_info["description"],
        },
        "yield_prediction": yield_result,
        "risk": {
            "level": risk["risk_level"],
            "name": risk["risk_name"],
            "emoji": risk["emoji"],
            "ratio": risk["ratio"],
            "message": risk["message"],
            "suggestions": risk["suggestions"],
        },
    }

    if save_db:
        db = get_db()
        orchard_id = db.add_orchard("CLI果园", variety, tree_count)
        db.add_detection(
            orchard_id=orchard_id,
            counts=counts,
            stage=stage_info["stage"],
            predicted_yield=yield_result["predicted_yield_kg"],
            confidence=yield_result["confidence"],
            risk_level=risk["risk_level"],
            risk_ratio=risk["ratio"],
            variety=variety,
            image_path=image_path,
        )
        output["saved_to_db"] = True
        output["orchard_id"] = orchard_id
    else:
        output["saved_to_db"] = False

    return output


def predict_video(video_path: str, variety: str, tree_count: int, save_db: bool = False):
    """对视频进行预测"""
    dt = get_detector(device="cpu")
    result = dt.detect_video(video_path)

    if not result.get("success"):
        return {"error": result.get("error", "视频处理失败")}

    counts = result["avg_counts"]
    total = sum(counts.values())

    stage_info = StageClassifier.classify(counts, total)
    estimator = YieldEstimator(variety)
    yield_result = estimator.estimate(counts, stage_info, tree_count=tree_count)

    alerter = RiskAlerter(variety)
    risk = alerter.evaluate(counts, stage_info)

    output = {
        "input_type": "video",
        "input_path": video_path,
        "variety": variety,
        "tree_count": tree_count,
        "timestamp": datetime.now().isoformat(),
        "video_stats": {
            "total_frames": result.get("total_frames", 0),
            "sampled_frames": result.get("sampled_frames", 0),
        },
        "detection": {
            "flower": counts.get("flower", 0),
            "immature_fruit": counts.get("immature_fruit", 0),
            "mature_fruit": counts.get("mature_fruit", 0),
            "total": total,
        },
        "stage": {
            "stage": stage_info["stage"],
            "stage_name": stage_info["stage_name"],
            "confidence": stage_info["confidence"],
            "description": stage_info["description"],
        },
        "yield_prediction": yield_result,
        "risk": {
            "level": risk["risk_level"],
            "name": risk["risk_name"],
            "emoji": risk["emoji"],
            "ratio": risk["ratio"],
            "message": risk["message"],
            "suggestions": risk["suggestions"],
        },
    }

    if save_db:
        db = get_db()
        orchard_id = db.add_orchard("CLI果园", variety, tree_count)
        db.add_detection(
            orchard_id=orchard_id,
            counts=counts,
            stage=stage_info["stage"],
            predicted_yield=yield_result["predicted_yield_kg"],
            confidence=yield_result["confidence"],
            risk_level=risk["risk_level"],
            risk_ratio=risk["ratio"],
            variety=variety,
            image_path=video_path,
        )
        output["saved_to_db"] = True
        output["orchard_id"] = orchard_id
    else:
        output["saved_to_db"] = False

    return output


def print_report(data: dict):
    """打印格式化报告到控制台"""
    print("\n" + "=" * 60)
    print(" 🍊 柑橘产量预测报告 ".center(56))
    print("=" * 60)

    if "error" in data:
        print(f"❌ 错误: {data['error']}")
        return

    print(f"\n输入: {data['input_path']} ({data['input_type']})")
    print(f"品种: {data['variety']} | 果树数: {data['tree_count']}棵")

    if "video_stats" in data:
        vs = data["video_stats"]
        print(f"视频帧: 总{vs['total_frames']}帧, 采样{vs['sampled_frames']}帧")

    det = data["detection"]
    print(f"\n📊 检测结果:")
    print(f"  🌸 花朵:       {det['flower']}")
    print(f"  🍏 幼果:       {det['immature_fruit']}")
    print(f"  🍊 成熟果:     {det['mature_fruit']}")
    print(f"  合计:         {det['total']}")

    stage = data["stage"]
    print(f"\n🌱 生长阶段: {stage['stage_name']} (置信度: {stage['confidence']:.1%})")

    yd = data["yield_prediction"]
    print(f"\n📈 产量预测:")
    print(f"  预测产量:     {yd['predicted_yield_kg']} kg ({yd['predicted_yield_jin']} 市斤)")
    print(f"  单棵产量:     {yd['per_tree_yield_kg']} kg/棵")
    print(f"  预测公式:     {yd['formula']}")
    print(f"  置信度:       {yd['confidence']:.0%}")

    risk = data["risk"]
    print(f"\n⚠️ 风险预警: {risk['emoji']} {risk['name']}")
    print(f"  {risk['message']}")
    print(f"\n建议措施:")
    for i, sug in enumerate(risk['suggestions'], 1):
        print(f"  {i}. {sug}")

    if data.get("saved_to_db"):
        print(f"\n💾 已保存到数据库 (果园ID: {data['orchard_id']})")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="柑橘产量预测命令行工具")
    parser.add_argument("--image", type=str, help="输入图片路径")
    parser.add_argument("--video", type=str, help="输入视频路径")
    parser.add_argument("--variety", type=str, default="奉节脐橙",
                        choices=get_available_varieties(),
                        help="柑橘品种")
    parser.add_argument("--trees", type=int, default=1, help="果树数量")
    parser.add_argument("--output", type=str, default="", help="输出JSON文件路径")
    parser.add_argument("--save-db", action="store_true", help="保存结果到数据库")
    parser.add_argument("--quiet", action="store_true", help="仅输出JSON，不打印报告")
    args = parser.parse_args()

    if not args.image and not args.video:
        parser.print_help()
        print("\n错误: 请指定 --image 或 --video")
        sys.exit(1)

    if args.image and args.video:
        print("错误: 请只指定 --image 或 --video 之一")
        sys.exit(1)

    try:
        if args.image:
            result = predict_image(args.image, args.variety, args.trees, save_db=args.save_db)
        else:
            result = predict_video(args.video, args.variety, args.trees, save_db=args.save_db)
    except Exception as e:
        print(f"预测失败: {e}")
        sys.exit(1)

    if not args.quiet:
        print_report(result)

    # 输出JSON
    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        if not args.quiet:
            print(f"\n结果已保存到: {args.output}")
    else:
        # 如果没有指定输出文件且是quiet模式，输出到stdout
        if args.quiet:
            print(json_str)


if __name__ == "__main__":
    main()
