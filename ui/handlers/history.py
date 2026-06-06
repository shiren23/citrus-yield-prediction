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
from ui.components import status_html, toast_output
from ui.constants import (
    DEFAULT_SYSTEM_PARAMS,
    MANUAL_RECORD_OPTION,
    MEDIA_PREVIEW_PLACEHOLDER,
    MEDIA_VIDEO_EXTENSIONS,
    STAGE_DISPLAY,
    STAGE_UI_MAP,
    SYSTEM_PARAMS_PATH,
)
from ui.handlers.orchard_data import default_orchard_name, format_risk_label, get_orchard_id, get_orchard_list

try:
    import gradio as gr
except ImportError:
    gr = None

def generate_comparative_trend(orchard_name: str, stage_filter: str, period: str):
    if not MATPLOTLIB_OK:
        return None

    setup_matplotlib_chinese()
    orchard_id = get_orchard_id(orchard_name)
    if orchard_id is None:
        return None

    records = get_db().get_yield_trend(orchard_id)
    if not records:
        return None

    now = datetime.now()
    filtered = []
    for r in records:
        dt_str = str(r.get("detected_at", ""))[:10]
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d")
        except ValueError:
            continue
        if stage_filter != "全部阶段":
            stage_label = STAGE_DISPLAY.get(r.get("stage", ""), "")
            if stage_filter == "花期" and stage_label != "花期":
                continue
            if stage_filter == "成熟期" and stage_label != "成熟期":
                continue
        if period == "近3个月" and (now - dt).days > 92:
            continue
        if period == "近6个月" and (now - dt).days > 183:
            continue
        if period == "近1年" and (now - dt).days > 365:
            continue
        filtered.append({**r, "_dt": dt})

    if not filtered:
        return None

    current_year = now.year
    curr = [r for r in filtered if r["_dt"].year == current_year]
    prev = [r for r in filtered if r["_dt"].year < current_year]

    fig, ax = plt.subplots(figsize=(12, 4.5))
    fig.patch.set_facecolor("#ffffff")

    if curr:
        sorted_curr = sorted(curr, key=lambda x: x["_dt"])
        xs = [r["_dt"] for r in sorted_curr]
        ys = [r["predicted_yield"] for r in sorted_curr]
        ax.plot(xs, ys, color="#2563eb", linestyle="-", linewidth=2.5, marker="o",
                markersize=6, label="当年预测")

    if prev:
        month_vals: dict = {}
        for r in prev:
            key = r["_dt"].month
            month_vals.setdefault(key, []).append(r["predicted_yield"])
        months = sorted(month_vals.keys())
        avg_y = [sum(month_vals[m]) / len(month_vals[m]) for m in months]
        month_dates = [datetime(current_year, m, 15) for m in months]
        ax.plot(month_dates, avg_y, color="#94a3b8", linestyle="--", linewidth=2,
                marker="s", markersize=5, label="往年同期均值")

    ax.set_xlabel("日期", fontsize=13, color="#334155", labelpad=8)
    ax.set_ylabel("预测产量 (kg)", fontsize=13, color="#334155", labelpad=8)
    ax.set_title(f"{orchard_name} 产量趋势", fontsize=15, fontweight="bold", color="#1e293b", pad=12)
    ax.grid(True, axis="y", alpha=0.35, color="#cbd5e1", linestyle="-", linewidth=0.8)
    ax.grid(True, axis="x", alpha=0.15, color="#e2e8f0", linestyle="-", linewidth=0.6)
    ax.legend(fontsize=12, loc="upper left", frameon=True, framealpha=0.95,
              edgecolor="#e2e8f0", facecolor="#ffffff")
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=False))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    if curr:
        curr_dates = [r["_dt"] for r in sorted(curr, key=lambda x: x["_dt"])]
        ax.set_xticks(curr_dates)
        ax.set_xticklabels([d.strftime("%Y-%m-%d") for d in curr_dates])
    elif prev:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.tick_params(axis="both", labelsize=11, colors="#475569", width=1, length=4)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.margins(x=0.05, y=0.12)
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")

    plt.tight_layout()
    tmp_path = os.path.join(tempfile.gettempdir(), f"trend_{orchard_id}.png")
    plt.savefig(tmp_path, dpi=140, facecolor="#ffffff", bbox_inches="tight")
    plt.close(fig)
    return tmp_path


def get_filtered_detections(orchard_name: str, stage_filter: str, period: str) -> List[dict]:
    orchard_id = get_orchard_id(orchard_name)
    if orchard_id is None:
        return []

    records = get_db().get_detections(orchard_id, limit=200)
    if not records:
        return []

    now = datetime.now()
    filtered = []
    for r in records:
        dt_str = str(r.get("detected_at", ""))[:10]
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d")
        except ValueError:
            dt = now
        stage_label = STAGE_DISPLAY.get(r.get("stage", ""), r.get("stage", ""))
        if stage_filter != "全部阶段":
            if stage_filter == "花期" and stage_label != "花期":
                continue
            if stage_filter == "成熟期" and stage_label != "成熟期":
                continue
        if period == "近3个月" and (now - dt).days > 92:
            continue
        if period == "近6个月" and (now - dt).days > 183:
            continue
        if period == "近1年" and (now - dt).days > 365:
            continue

        fruit = get_fruit_count({
            "fruit": 0,
            "mature_fruit": r.get("mature_count", 0),
            "immature_fruit": r.get("immature_count", 0),
        }) + r.get("immature_count", 0)
        filtered.append({
            "id": r["id"],
            "date": dt_str,
            "stage": stage_label,
            "flowers": r.get("flower_count", 0),
            "fruit": fruit,
            "yield_kg": r.get("predicted_yield", 0),
            "risk_label": format_risk_label(r.get("risk_level", "normal")),
        })
    return filtered


HISTORY_TABLE_PLACEHOLDER = (
    '<p class="hint-text" style="padding:12px;border:1px solid #e2e8f0;border-radius:6px">'
    '请设置筛选条件后，点击「查询数据」查看明细</p>'
)

HIST_DELETE_JS = """
() => {
    if (window.__citrusAppBound) return;
    window.__citrusAppBound = true;
    function queryAll(selector) {
        const found = [];
        const visit = (root) => {
            if (!root) return;
            root.querySelectorAll(selector).forEach((el) => found.push(el));
            root.querySelectorAll('*').forEach((el) => {
                if (el.shadowRoot) visit(el.shadowRoot);
            });
        };
        visit(document);
        const app = document.querySelector('gradio-app');
        if (app && app.shadowRoot) visit(app.shadowRoot);
        return found;
    }
    function showCitrusToast(message, type) {
        if (!message) return;
        type = type || 'success';
        let toast = document.getElementById('citrus-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'citrus-toast';
            toast.className = 'citrus-toast';
            toast.setAttribute('role', 'status');
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.className = 'citrus-toast citrus-toast-' + type + ' citrus-toast-show';
        clearTimeout(window.__citrusToastTimer);
        window.__citrusToastTimer = setTimeout(() => {
            toast.classList.remove('citrus-toast-show');
        }, 2000);
    }
    window.showCitrusToast = showCitrusToast;
    function bindToastTriggers() {
        queryAll('.toast-trigger textarea, #toast_trigger textarea').forEach((ta) => {
            if (ta.dataset.toastBound) return;
            ta.dataset.toastBound = '1';
            let last = '';
            const check = () => {
                const v = (ta.value || '').trim();
                if (!v || v === last) return;
                last = v;
                const sep = v.lastIndexOf('|');
                const msg = sep >= 0 ? v.slice(0, sep) : v;
                const type = sep >= 0 ? v.slice(sep + 1) : 'success';
                showCitrusToast(msg, type === 'error' ? 'error' : 'success');
                ta.value = '';
                ta.dispatchEvent(new Event('input', { bubbles: true }));
                last = '';
            };
            ta.addEventListener('input', check);
            new MutationObserver(check).observe(ta, {
                attributes: true, characterData: true, childList: true, subtree: true,
            });
        });
    }
    setInterval(bindToastTriggers, 600);
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-hist-delete]');
        if (!btn) return;
        e.preventDefault();
        const id = btn.getAttribute('data-hist-delete');
        const inputs = queryAll('.hist-delete-id-input textarea, #hist_delete_id textarea');
        const submits = queryAll('.hist-delete-submit button, #hist_delete_submit button');
        const input = inputs[0];
        const submit = submits[0];
        if (!input || !submit) return;
        input.value = id;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        submit.click();
    }, true);
}
"""


def build_history_table_html(orchard_name: str, stage_filter: str, period: str) -> str:
    records = get_filtered_detections(orchard_name, stage_filter, period)
    if not records:
        return (
            '<p class="hint-text" style="padding:12px;border:1px solid #e2e8f0;border-radius:6px">'
            '暂无符合条件的记录</p>'
        )

    rows = []
    for r in records:
        risk_cls = "risk-warning" if r["risk_label"] == "低产预警" else "risk-normal"
        rows.append(
            f"<tr>"
            f"<td>{r['date']}</td>"
            f"<td>{r['stage']}</td>"
            f"<td>{r['flowers']}</td>"
            f"<td>{r['fruit']}</td>"
            f"<td>{r['yield_kg']}</td>"
            f"<td class='{risk_cls}'>{r['risk_label']}</td>"
            f"<td><button type=\"button\" class=\"hist-del-btn\" "
            f"data-hist-delete=\"{r['id']}\">删除</button></td>"
            f"</tr>"
        )

    return f"""
    <div class="history-table-wrap">
    <table>
        <thead>
            <tr>
                <th>日期</th><th>生长阶段</th><th>花朵数</th><th>果实数</th>
                <th>预测产量(kg)</th><th>风险</th><th>操作</th>
            </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    </div>
    """


def query_history(orchard_name, stage_filter, period):
    title = f"{orchard_name}产量趋势"
    fig = generate_comparative_trend(orchard_name, stage_filter, period)
    return title, fig


def build_history_filter_summary(orchard_name: str, stage_filter: str, period: str) -> str:
    records = get_filtered_detections(orchard_name, stage_filter, period)
    return (
        f'<div class="filter-summary">'
        f'<span>果园：<strong>{orchard_name or "未选择"}</strong></span>'
        f'<span>阶段：<strong>{stage_filter}</strong></span>'
        f'<span>统计周期：<strong>{period}</strong></span>'
        f'<span>匹配记录：<strong>{len(records)}</strong> 条</span>'
        f'</div>'
    )


def format_history_title(orchard_name: str, stage_filter: str, period: str) -> str:
    return f"**{orchard_name} 产量趋势（{period} · {stage_filter}）**"


def parse_delete_record_id(raw) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        raw = raw[-1] if raw else None
    s = str(raw).strip()
    if s.isdigit():
        return int(s)
    for token in s.replace("·", " ").split():
        if token.isdigit():
            return int(token)
    return None


def initial_history_view():
    """页面初始默认展示（无需先点查询）。"""
    orchard = default_orchard_name()
    if not orchard:
        orchards = get_orchard_list()
        orchard = orchards[0] if orchards else ""
    stage, period = "全部阶段", "近1年"
    if not orchard:
        return (
            "**产量趋势**",
            None,
            '<div class="filter-summary"><span>请先添加果园</span></div>',
            HISTORY_TABLE_PLACEHOLDER,
        )
    title, fig = query_history(orchard, stage, period)
    summary = build_history_filter_summary(orchard, stage, period)
    table = build_history_table_html(orchard, stage, period)
    return (
        format_history_title(orchard, stage, period),
        fig,
        summary,
        table,
    )


def apply_history_filters(orchard_name, stage_filter, period):
    title, fig = query_history(orchard_name, stage_filter, period)
    summary = build_history_filter_summary(orchard_name, stage_filter, period)
    table = build_history_table_html(orchard_name, stage_filter, period)
    return (
        format_history_title(orchard_name, stage_filter, period),
        fig,
        summary,
        table,
    )


def handle_table_delete(record_id_raw, orchard_name, stage_filter, period):
    record_id = parse_delete_record_id(record_id_raw)
    if record_id is None:
        msg = "删除失败，请重试"
        if gr is not None:
            gr.Warning(msg, duration=3, title="")
        return (
            gr.update(), gr.update(), gr.update(),
            build_history_table_html(orchard_name, stage_filter, period),
            toast_output(msg, False),
            status_html(msg, False),
        )
    get_db().delete_detection(record_id)
    msg = "记录已删除"
    if gr is not None:
        gr.Info(msg, duration=2, title="")
    title, fig = query_history(orchard_name, stage_filter, period)
    summary = build_history_filter_summary(orchard_name, stage_filter, period)
    table = build_history_table_html(orchard_name, stage_filter, period)
    return (
        format_history_title(orchard_name, stage_filter, period),
        fig,
        summary,
        table,
        toast_output(msg),
        status_html(msg, True),
    )


def export_history_batch(orchard_name, stage_filter, period):
    records = get_filtered_detections(orchard_name, stage_filter, period)
    if not records:
        raise gr.Error("暂无符合条件的记录可导出")
    content = io.StringIO()
    writer = csv.writer(content)
    writer.writerow(["日期", "生长阶段", "花朵数", "果实数", "预测产量(kg)", "风险"])
    for r in records:
        writer.writerow([
            r["date"], r["stage"], r["flowers"], r["fruit"], r["yield_kg"], r["risk_label"],
        ])
    safe_name = str(orchard_name or "orchard").replace("/", "_").replace("\\", "_")
    tmp = os.path.join(
        tempfile.gettempdir(),
        f"history_{safe_name}_{datetime.now():%Y%m%d_%H%M%S}.csv",
    )
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(content.getvalue())
    return tmp

