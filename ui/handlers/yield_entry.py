import csv
import io
import json
import os
import tempfile
import traceback
from datetime import datetime
from typing import List, Optional, Tuple

from core.config import RISK_THRESHOLDS, get_fruit_count
from core.count_scaler import scale_counts_to_tree
from core.risk_alert import RiskAlerter
from core.stage_classifier import StageClassifier
from core.yield_estimator import YieldEstimator
from data.database import get_db

from ui.charts import MATPLOTLIB_OK, MaxNLocator, mdates, plt, setup_matplotlib_chinese
from ui.components import toast_output
from ui.constants import (
    DEFAULT_SYSTEM_PARAMS,
    MANUAL_RECORD_OPTION,
    MEDIA_PREVIEW_PLACEHOLDER,
    MEDIA_VIDEO_EXTENSIONS,
    STAGE_DISPLAY,
    STAGE_UI_MAP,
    SYSTEM_PARAMS_PATH,
)
from ui.handlers.orchard_data import get_orchard_id

try:
    import gradio as gr
except ImportError:
    gr = None

def format_prediction_option_label(r: dict) -> str:
    stage = STAGE_DISPLAY.get(r.get("stage", ""), r.get("stage", ""))
    date_part = str(r.get("detected_at", ""))[:10]
    yld = round(float(r.get("predicted_yield", 0) or 0), 2)
    return f"{date_part} · {stage} · {yld}kg"


def get_prediction_options(orchard_name: Optional[str] = None) -> List[Tuple[str, str]]:
    orchard_id = get_orchard_id(orchard_name) if orchard_name else None
    records = get_db().get_detections_with_orchard(orchard_id=orchard_id, limit=100)
    options = [(MANUAL_RECORD_OPTION, "manual")]
    options.extend(
        (format_prediction_option_label(r), str(r["id"]))
        for r in records
    )
    return options


def refresh_prediction_record_options(orchard_name: str, current_option: str):
    options = get_prediction_options(orchard_name)
    valid_values = {value for _, value in options}
    value = current_option if current_option in valid_values else "manual"
    return gr.update(choices=options, value=value)


def default_prediction_option_value() -> str:
    options = get_prediction_options()
    if len(options) > 1:
        return options[0][1]
    return "manual"


def parse_prediction_option(option: str) -> Optional[int]:
    if not option or option == "manual":
        return None
    try:
        return int(option)
    except (TypeError, ValueError):
        return None


def on_prediction_record_select(option: str):
    manual = option == "manual"
    if manual:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
        )
    det_id = parse_prediction_option(option)
    if det_id is None:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
        )
    rec = get_db().get_detection(det_id)
    orchard = get_db().get_orchard(rec["orchard_id"]) if rec else None
    orchard_name = orchard["name"] if orchard else ""
    date_str = str(rec.get("detected_at", ""))[:10]
    stage = STAGE_DISPLAY.get(rec.get("stage", ""), rec.get("stage", ""))
    predicted = rec.get("predicted_yield", 0)
    fill_html = f"""
    <div class="auto-fill-block">
        <div><span class="info-label">果园：</span>{orchard_name}</div>
        <div><span class="info-label">日期：</span>{date_str}</div>
        <div><span class="info-label">阶段：</span>{stage}</div>
        <div><span class="info-label">预测产量：</span>{predicted} kg</div>
    </div>
    """
    return (
        gr.update(visible=True, value=fill_html),
        gr.update(visible=False),
        gr.update(value=orchard_name),
        gr.update(value=date_str),
        gr.update(value=stage),
        gr.update(value=str(predicted)),
    )


def submit_actual_yield(option, manual_orchard, harvest_date, total_yield_kg, predicted_str):
    try:
        actual_total = float(total_yield_kg)
        if actual_total <= 0:
            return "", toast_output("请输入大于 0 的实际采收总产量", False)
    except (TypeError, ValueError):
        return "", toast_output("请输入有效的实际采收总产量（单位：kg）", False)

    det_id = parse_prediction_option(option)
    db = get_db()

    if det_id is not None:
        rec = db.get_detection(det_id)
        if rec is None:
            return "", toast_output("关联的预测记录不存在，请重新选择或改用手动录入", False)
        orchard_id = rec["orchard_id"]
        predicted = rec.get("predicted_yield", 0)
        tree_count = db.get_orchard(orchard_id).get("tree_count", 1)
        date_str = (harvest_date or "").strip()[:10] or str(rec.get("detected_at", ""))[:10]
    else:
        orchard_id = get_orchard_id(manual_orchard)
        if orchard_id is None:
            return "", toast_output("果园不存在，请先在果园管理中新增", False)
        date_str = (harvest_date or "").strip()[:10]
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        if len(date_str) != 10:
            return "", toast_output("采收日期格式应为 YYYY-MM-DD", False)
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return "", toast_output("采收日期格式无效，请使用 YYYY-MM-DD", False)
        predicted = float(predicted_str) if predicted_str else 0
        tree_count = db.get_orchard(orchard_id).get("tree_count", 1)

    per_tree = actual_total / tree_count if tree_count else actual_total
    year = int(date_str[:4])
    season = "秋季"
    db.add_history_yield(
        orchard_id, year, season, actual_total,
        detection_id=det_id,
        harvest_date=date_str,
        per_tree_yield=per_tree,
    )

    if predicted > 0:
        error_pct = abs(actual_total - predicted) / predicted * 100
        return "", toast_output(
            f"保存成功。预测 {predicted} kg，实际 {actual_total:.2f} kg，误差 {error_pct:.1f}%",
        )
    return "", toast_output(
        f"保存成功。实际总产量 {actual_total:.2f} kg（约 {per_tree:.2f} kg/棵）",
    )

