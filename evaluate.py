"""
柑橘产量预测系统 - 自评测脚本
对系统各模块进行功能验证和性能评估
"""

import os
import sys
import time
import random
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import get_variety_config, CLASS_NAMES, RISK_THRESHOLDS, get_fruit_count
from core.stage_classifier import StageClassifier
from core.yield_estimator import YieldEstimator
from core.risk_alert import RiskAlerter
from data.database import CitrusDatabase


class SelfEvaluator:
    """系统自评测器"""

    def __init__(self):
        self.results = []

    def log(self, module: str, test: str, passed: bool, detail: str = ""):
        status = "[PASS]" if passed else "[FAIL]"
        self.results.append({
            "module": module,
            "test": test,
            "passed": passed,
            "detail": detail,
        })
        print(f"[{module}] {status} - {test} {detail}")

    def run_all(self):
        print("=" * 60)
        print(" Citrus Yield Prediction System - Self Evaluation ")
        print("=" * 60)

        self.test_config()
        self.test_stage_classifier()
        self.test_yield_estimator()
        self.test_risk_alert()
        self.test_database()
        self.test_detector_placeholder()
        self.test_integration()

        self.print_summary()

    def test_config(self):
        print("\n[Config Module] Testing started")
        try:
            v = get_variety_config("奉节脐橙")
            self.log("Config", "品种配置读取", v.avg_weight_kg == 0.25)

            v2 = get_variety_config("不存在的品种")
            self.log("Config", "默认品种回退", v2.name == "通用柑橘")

            from core.config import get_available_varieties
            varieties = get_available_varieties()
            self.log("Config", "品种列表", len(varieties) >= 3, f"({len(varieties)}个品种)")
        except Exception as e:
            self.log("Config", "整体测试", False, str(e))

    def test_stage_classifier(self):
        print("\n[Stage Classifier] Testing started")
        try:
            # 花期测试
            counts = {"flower": 80, "immature_fruit": 10, "mature_fruit": 5}
            r = StageClassifier.classify(counts)
            self.log("Stage", "花期判断", r["stage"] == "flowering",
                     f"stage={r['stage']}, conf={r['confidence']}")

            # 成熟期（果实期）测试
            counts = {"flower": 5, "immature_fruit": 0, "fruit": 80, "mature_fruit": 80, "total": 85}
            r = StageClassifier.classify(counts)
            self.log("Stage", "果实期判断", r["stage"] == "mature",
                     f"stage={r['stage']}, conf={r['confidence']}")

            # 空数据测试
            counts = {"flower": 0, "immature_fruit": 0, "fruit": 0, "mature_fruit": 0, "total": 0}
            r = StageClassifier.classify(counts)
            self.log("Stage", "空数据处理", r["stage"] == "unknown")

            # 混合期测试
            counts = {"flower": 30, "fruit": 35, "mature_fruit": 35, "immature_fruit": 0, "total": 100}
            r = StageClassifier.classify(counts)
            self.log("Stage", "混合期判断", r["stage"] == "mixed")
        except Exception as e:
            self.log("Stage", "整体测试", False, str(e))

    def test_yield_estimator(self):
        print("\n[Yield Estimator] Testing started")
        try:
            estimator = YieldEstimator("奉节脐橙")

            # 花期预测
            counts = {"flower": 500, "immature_fruit": 0, "mature_fruit": 0}
            stage = {"stage": "flowering"}
            r = estimator.estimate(counts, stage)
            expected = 500 * 0.08 * 0.25  # 10.0
            self.log("Yield", "花期产量预测",
                     abs(r["predicted_yield_kg"] - expected) < 0.01,
                     f"预测={r['predicted_yield_kg']}kg, 期望={expected}kg")

            # 果实期预测
            counts = {"flower": 0, "fruit": 100, "mature_fruit": 100, "total": 100}
            stage = {"stage": "mature"}
            r = estimator.estimate(counts, stage)
            expected = 100 * 0.25 * (1 - 0.05)  # 23.75
            self.log("Yield", "果实期产量校正",
                     abs(r["predicted_yield_kg"] - expected) < 0.01,
                     f"预测={r['predicted_yield_kg']}kg, 期望={expected}kg")

            # 多棵树扩展
            counts = {"flower": 0, "fruit": 100, "mature_fruit": 100, "total": 100}
            stage = {"stage": "mature"}
            r = estimator.estimate(counts, stage, tree_count=10)
            self.log("Yield", "多棵树产量扩展", r["predicted_yield_kg"] == expected * 10,
                     f"10棵总产量={r['predicted_yield_kg']}kg")

            # 单位换算
            self.log("Yield", "市斤换算", r["predicted_yield_jin"] == r["predicted_yield_kg"] * 2)

        except Exception as e:
            self.log("Yield", "整体测试", False, str(e))

    def test_risk_alert(self):
        print("\n[Risk Alert] Testing started")
        try:
            alerter = RiskAlerter("奉节脐橙")

            # 正常产量
            counts = {"flower": 800, "immature_fruit": 0, "mature_fruit": 0}
            stage = {"stage": "flowering"}
            r = alerter.evaluate(counts, stage)
            self.log("Risk", "正常产量预警",
                     r["risk_level"] == "normal",
                     f"ratio={r['ratio']:.2f}")

            # 低产风险
            counts = {"flower": 600, "immature_fruit": 0, "mature_fruit": 0}
            r = alerter.evaluate(counts, stage)
            self.log("Risk", "低产风险预警",
                     r["risk_level"] == "warning",
                     f"ratio={r['ratio']:.2f}")

            # 严重低产
            counts = {"flower": 400, "immature_fruit": 0, "mature_fruit": 0}
            r = alerter.evaluate(counts, stage)
            self.log("Risk", "严重低产预警",
                     r["risk_level"] == "severe",
                     f"ratio={r['ratio']:.2f}")

            # 使用历史记录
            hist = [{"counts": {"flower": 800}}, {"counts": {"flower": 850}}]
            counts = {"flower": 700}
            r = alerter.evaluate(counts, stage, historical_records=hist)
            self.log("Risk", "历史记录对比", r["reference_avg"] == 825.0,
                     f"历史均值={r['reference_avg']}")

        except Exception as e:
            self.log("Risk", "整体测试", False, str(e))

    def test_database(self):
        print("\n[Database] Testing started")
        try:
            db_path = "data/test_citrus.db"
            if os.path.exists(db_path):
                os.remove(db_path)

            db = CitrusDatabase(db_path)

            # 添加果园
            oid = db.add_orchard("测试果园", "奉节脐橙", 5, "重庆奉节")
            self.log("DB", "添加果园", oid is not None, f"id={oid}")

            orchard = db.get_orchard(oid)
            self.log("DB", "查询果园", orchard["name"] == "测试果园")

            # 添加检测记录
            rid = db.add_detection(
                orchard_id=oid,
                counts={"flower": 100, "immature_fruit": 20, "mature_fruit": 5},
                stage="flowering",
                predicted_yield=10.5,
                confidence=0.6,
                risk_level="normal",
                risk_ratio=1.0,
                variety="奉节脐橙",
            )
            self.log("DB", "添加检测记录", rid is not None)

            records = db.get_detections(oid)
            self.log("DB", "查询检测记录", len(records) == 1)

            # 历史产量
            yid = db.add_history_yield(oid, 2025, "秋季", 120.0)
            self.log("DB", "添加历史产量", yid is not None)

            yields = db.get_history_yields(oid)
            self.log("DB", "查询历史产量", len(yields) == 1)

            # 趋势
            trend = db.get_yield_trend(oid)
            self.log("DB", "产量趋势", len(trend) == 1)

            # 导出CSV
            csv = db.export_to_csv(oid)
            self.log("DB", "CSV导出", len(csv) > 0)

            # 清理
            os.remove(db_path)
            self.log("DB", "清理测试数据", not os.path.exists(db_path))

        except Exception as e:
            self.log("DB", "整体测试", False, str(e))

    def test_detector_placeholder(self):
        print("\n[Detector] Testing started")
        try:
            # 由于可能没有安装ultralytics或模型文件，做基础导入测试
            from core.detector import CitrusDetector
            self.log("Detector", "模块导入", True)

            # 创建一张测试图
            test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

            # 测试检测器初始化（如果没有模型会尝试下载或报错）
            try:
                from core.detector import get_detector
                dt = get_detector()
                self.log("Detector", "模型加载", True)

                # 测试图片检测
                r = dt.detect_image(test_img)
                self.log("Detector", "图片检测", isinstance(r, dict) and "counts" in r)
            except Exception as e:
                self.log("Detector", "模型加载/检测", False,
                         f"(可能模型未下载: {str(e)[:50]}...)")

        except Exception as e:
            self.log("Detector", "整体测试", False, str(e))

    def test_integration(self):
        print("\n[Integration] Testing started")
        try:
            # 模拟完整预测流程
            counts = {"flower": 600, "immature_fruit": 50, "mature_fruit": 10}
            total = sum(counts.values())

            stage_info = StageClassifier.classify(counts, total)
            estimator = YieldEstimator("奉节脐橙")
            yield_result = estimator.estimate(counts, stage_info, tree_count=1)
            alerter = RiskAlerter("奉节脐橙")
            risk = alerter.evaluate(counts, stage_info)

            passed = (
                yield_result["predicted_yield_kg"] > 0
                and risk["risk_level"] in ["normal", "warning", "severe", "unknown"]
                and stage_info["stage"] in ["flowering", "immature", "mature", "mixed", "unknown"]
            )
            self.log("Integration", "端到端预测流程", passed,
                     f"stage={stage_info['stage']}, yield={yield_result['predicted_yield_kg']}kg, risk={risk['risk_level']}")

            # 测试性能
            start = time.time()
            for _ in range(100):
                StageClassifier.classify(counts)
            elapsed = time.time() - start
            self.log("Integration", "阶段分类性能(100次)", elapsed < 1.0,
                     f"耗时={elapsed:.3f}s")

            start = time.time()
            for _ in range(100):
                estimator.estimate(counts, stage_info)
            elapsed = time.time() - start
            self.log("Integration", "产量估算性能(100次)", elapsed < 1.0,
                     f"耗时={elapsed:.3f}s")

        except Exception as e:
            self.log("Integration", "整体测试", False, str(e))

    def print_summary(self):
        print("\n" + "=" * 60)
        print(" Evaluation Summary ")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed

        print(f"总测试数: {total}")
        print(f"通过: {passed} | 失败: {failed}")
        print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "N/A")

        if failed > 0:
            print("\n[Failed Items]:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - [{r['module']}] {r['test']}: {r['detail']}")

        print("=" * 60)
        return passed, failed


def main():
    evaluator = SelfEvaluator()
    evaluator.run_all()


if __name__ == "__main__":
    main()
