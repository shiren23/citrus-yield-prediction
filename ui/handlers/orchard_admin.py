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
import html
from ui.handlers.orchard_data import (
    ORCHARD_DROPDOWNS,
    default_orchard_name,
    get_orchard_list,
    save_system_params,
)
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

def build_orchard_table() -> List[List]:
    rows = []
    for o in get_db().list_orchards():
        planted = str(o.get("created_at", ""))[:10]
        rows.append([o["name"], planted, o.get("tree_count", 0), o["id"]])
    return rows or [["", "", "", ""]]


def get_orchard_dropdown_choices():
    return [(o["name"], o["id"]) for o in get_db().list_orchards()]


def build_orchard_table_html() -> str:
    orchards = get_db().list_orchards()
    if not orchards:
        return '<p class="hint-text" style="padding:8px 0">暂无果园，请先新增</p>'
    rows = []
    for o in orchards:
        oid = html.escape(str(o.get("id", "")), quote=True)
        name = html.escape(str(o.get("name", "")), quote=True)
        planted = html.escape(str(o.get("created_at", ""))[:10], quote=True)
        trees = html.escape(str(o.get("tree_count", 0)), quote=True)
        rows.append(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td>{planted}</td>"
            f"<td>{trees}</td>"
            f"<td><div class='orchard-actions'>"
            f"<button type='button' class='orchard-edit-btn' data-orchard-edit='{oid}' data-orchard-name='{name}' data-orchard-trees='{trees}'>编辑</button>"
            f"<button type='button' class='orchard-del-btn' data-orchard-delete='{oid}' data-orchard-name='{name}'>删除</button>"
            f"</div></td>"
            f"</tr>"
        )
    return f"""
    <div class="history-table-wrap orchard-table-wrap">
        <table>
            <thead>
                <tr><th>果园名称</th><th>建园日期</th><th>果树总量</th><th>操作</th></tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </div>
    """


def orchard_ui_pack(selected_id=None, msg="", ok=False):
    choices = get_orchard_dropdown_choices()
    html = build_orchard_table_html()
    msg_html = gr.update(value="", visible=False)

    # Always refresh the other registered orchard dropdowns so that
    # prediction/history/config filters stay in sync.
    dropdown_updates = []
    for dropdown in ORCHARD_DROPDOWNS:
        dropdown_updates.append(gr.update(choices=get_orchard_list(), value=default_orchard_name()))

    if not choices:
        return (
            html,
            gr.update(choices=[], value=None),
            "", 100,
            msg_html,
            *dropdown_updates,
        )
    if selected_id is None:
        selected_id = choices[0][1]
    orchard = get_db().get_orchard(int(selected_id))
    if orchard is None:
        selected_id = choices[0][1]
        orchard = get_db().get_orchard(int(selected_id))
    return (
        html,
        gr.update(choices=choices, value=selected_id),
        orchard["name"],
        orchard.get("tree_count", 1),
        msg_html,
        *dropdown_updates,
    )


def add_orchard_row(name, tree_count):
    if not name or not str(name).strip():
        return "果园名称不能为空"
    db = get_db()
    db.add_orchard(str(name).strip(), "通用柑橘", int(tree_count or 1))
    return f"已新增果园：{name}"


def save_system_params_ui(rate_pct, weight_g, risk_threshold):
    params = {
        "flower_fruit_rate_pct": float(rate_pct),
        "avg_weight_g": float(weight_g),
        "risk_warning_threshold": float(risk_threshold),
    }
    save_system_params(params)
    return "系统参数已保存"


def delete_orchard_by_id(orchard_id: int) -> str:
    get_db().delete_orchard(int(orchard_id))
    return "已删除果园"


def update_orchard_by_id(orchard_id: int, name: str, tree_count) -> str:
    name = str(name or "").strip()
    if not name:
        return "果园名称不能为空"
    get_db().update_orchard(int(orchard_id), name=name, tree_count=int(tree_count or 1))
    return f"已更新果园：{name}"
