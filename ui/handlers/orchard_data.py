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
from ui.components import toast_payload
from ui.constants import (
    DEFAULT_SYSTEM_PARAMS,
    MANUAL_RECORD_OPTION,
    MEDIA_PREVIEW_PLACEHOLDER,
    MEDIA_VIDEO_EXTENSIONS,
    STAGE_DISPLAY,
    STAGE_UI_MAP,
    SYSTEM_PARAMS_PATH,
)
from ui.detector_state import ensure_detector

try:
    import gradio as gr
except ImportError:
    gr = None

def load_system_params() -> dict:
    if os.path.isfile(SYSTEM_PARAMS_PATH):
        with open(SYSTEM_PARAMS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {**DEFAULT_SYSTEM_PARAMS, **data}
    return dict(DEFAULT_SYSTEM_PARAMS)


def save_system_params(params: dict):
    os.makedirs(os.path.dirname(SYSTEM_PARAMS_PATH), exist_ok=True)
    with open(SYSTEM_PARAMS_PATH, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
    RISK_THRESHOLDS["warning"] = params["risk_warning_threshold"] / 100.0


def apply_system_params_to_estimator(estimator: YieldEstimator, params: dict):
    rate = params["flower_fruit_rate_pct"] / 100.0
    weight = params["avg_weight_g"] / 1000.0
    estimator.variety.flower_fruit_rate = rate
    estimator.variety.avg_weight_kg = weight


def get_orchard_list() -> List[str]:
    db = get_db()
    orchards = db.list_orchards()
    if not orchards:
        return ["默认果园"]
    return [o["name"] for o in orchards]


def default_orchard_name() -> str:
    orchards = get_orchard_list()
    return orchards[0] if orchards else "默认果园"


def get_orchard_id(name: str) -> Optional[int]:
    for o in get_db().list_orchards():
        if o["name"] == name:
            return o["id"]
    return None


def get_orchard_variety(name: str) -> str:
    oid = get_orchard_id(name)
    if oid:
        info = get_db().get_orchard(oid)
        if info and info.get("variety"):
            return info["variety"]
    return "通用柑橘"


def refresh_orchard_dropdown():
    choices = get_orchard_list()
    return gr.Dropdown(choices=choices, value=choices[0])


def format_risk_label(risk_level: str) -> str:
    if risk_level in ("severe", "warning"):
        return "低产预警"
    return "正常"
