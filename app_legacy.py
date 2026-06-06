"""
柑橘产量预测系统 - Gradio Web 主应用
功能：产量预测、历史趋势、数据管理
"""

import os
import sys
import json
import csv
import io
import tempfile
import traceback
from datetime import datetime
from typing import Optional, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import (
    get_available_varieties,
    BASE_DIR,
    get_fruit_count,
    DATA_DIR,
    RISK_THRESHOLDS,
)
from core.detector import CitrusDetector, reset_detector
from core.stage_classifier import StageClassifier
from core.yield_estimator import YieldEstimator
from core.yield_corrector import YieldCorrector
from core.risk_alert import RiskAlerter
from core.count_scaler import scale_counts_to_tree
from data.database import get_db

try:
    import gradio as gr
except ImportError:
    gr = None
    print("警告: Gradio 未安装，Web界面不可用。请运行: pip install gradio")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import MaxNLocator
    MATPLOTLIB_OK = True

    def setup_matplotlib_chinese():
        plt.rcParams["font.sans-serif"] = [
            "Microsoft YaHei", "SimHei", "PingFang SC", "Noto Sans CJK SC", "sans-serif",
        ]
        plt.rcParams["axes.unicode_minus"] = False
except ImportError:
    MATPLOTLIB_OK = False
    MaxNLocator = None

    def setup_matplotlib_chinese():
        pass

detector: Optional[CitrusDetector] = None

STAGE_UI_OPTIONS = ["花期（早期估产）", "成熟期（产量校正）"]
STAGE_UI_MAP = {
    "花期（早期估产）": "flowering",
    "成熟期（产量校正）": "mature",
}
STAGE_DISPLAY = {
    "flowering": "花期",
    "immature": "幼果期",
    "mature": "成熟期",
    "mixed": "混合期",
    "unknown": "未知",
}
MANUAL_RECORD_OPTION = "无对应预测记录，手动录入"
MEDIA_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"}
MEDIA_FILE_TYPES = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".mp4", ".avi", ".mov", ".mkv", ".wmv"]
MEDIA_PREVIEW_PLACEHOLDER = '<div class="media-preview-placeholder">上传后将在此预览</div>'
SYSTEM_PARAMS_PATH = os.path.join(DATA_DIR, "system_params.json")
DEFAULT_SYSTEM_PARAMS = {
    "flower_fruit_rate_pct": 2.5,
    "avg_weight_g": 150,
    "risk_warning_threshold": 80,
}

INPUT_KW = {"show_label": False, "container": False}


def input_cls(*classes):
    kw = dict(INPUT_KW)
    kw["elem_classes"] = list(classes)
    return kw


def dropdown_cls(*classes):
    return {
        "show_label": False,
        "container": False,
        "elem_classes": list(classes) + ["dropdown-field"],
    }


def record_select_cls():
    return {
        "show_label": False,
        "container": False,
        "elem_classes": ["field-input", "dropdown-field", "record-select"],
    }


def toast_payload(message: str, ok: bool = True) -> str:
    return f"{message}|{'success' if ok else 'error'}"


def build_theme():
    return gr.themes.Base(
        primary_hue=gr.themes.colors.blue,
        neutral_hue=gr.themes.colors.slate,
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        body_background_fill="#f8fafc",
        background_fill_primary="#ffffff",
        background_fill_secondary="#f8fafc",
        border_color_primary="transparent",
        block_background_fill="transparent",
        block_border_color="transparent",
        block_border_width="0px",
        block_shadow="none",
        block_radius="0px",
        block_padding="0",
        block_label_background_fill="transparent",
        block_label_text_color="#334155",
        block_label_margin="0",
        block_label_padding="0",
        block_title_text_color="#334155",
        block_title_background_fill="transparent",
        input_background_fill="#ffffff",
        input_border_color="#e2e8f0",
        input_border_width="1px",
        input_radius="6px",
        input_shadow="none",
        input_padding="7px 10px",
        button_primary_background_fill="#2563eb",
        button_primary_background_fill_hover="#1d4ed8",
        button_primary_text_color="#ffffff",
        button_primary_border_color="#2563eb",
        button_secondary_background_fill="#ffffff",
        button_secondary_background_fill_hover="#f8fafc",
        button_secondary_text_color="#334155",
        button_secondary_border_color="#e2e8f0",
        button_large_radius="6px",
        button_small_radius="6px",
        button_medium_radius="6px",
        button_large_padding="8px 16px",
        button_medium_padding="8px 16px",
        button_small_padding="8px 16px",
        checkbox_border_color="#e2e8f0",
        slider_color="#2563eb",
        body_text_color="#334155",
        body_text_color_subdued="#64748b",
        body_text_size="14px",
        section_header_text_size="16px",
    )


def field_label(text: str):
    return gr.HTML(f'<div class="field-label">{text}</div>')


GLOBAL_CSS = """
.gradio-container {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 24px 32px !important;
    background: #f1f5f9 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    font-size: 14px !important;
    color: #334155 !important;
}
main.contain, .app, .wrap.svelte-zxu34v, .gradio-container > .main {
    width: 100% !important;
    max-width: 100% !important;
}
.tabitem, .tabs, .row, .column, .form {
    width: 100% !important;
    max-width: 100% !important;
}
footer, .gradio-footer, .built-with { display: none !important; }

/* ===== 加载状态：单一圆环，隐藏多处 processing 图标 ===== */
.progress-text,
.meta-text-center,
.timer,
.footer-bar,
.status-tracker,
[data-testid="status-display"],
.wrap .loader,
.block .loader,
.generating .icon-loading,
.generating .loading {
    display: none !important;
    visibility: hidden !important;
}
.generating {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    animation: none !important;
}
.block.html.generating,
.block.markdown.generating,
.form .block.generating:not(.predict-result-image):not(.predict-chart-image) {
    opacity: 1 !important;
    filter: none !important;
}
.block.html.generating::before,
.block.html.generating::after,
.block.markdown.generating::before,
.block.markdown.generating::after,
.form .block.generating:not(.predict-result-image):not(.predict-chart-image)::before,
.form .block.generating:not(.predict-result-image):not(.predict-chart-image)::after {
    display: none !important;
    content: none !important;
}
.predict-result-image.generating,
.predict-chart-image.generating {
    position: relative !important;
}
.predict-result-image.generating .image-container,
.predict-result-image.generating .container,
.predict-chart-image.generating .image-container,
.predict-chart-image.generating .container {
    position: relative !important;
    min-height: 160px !important;
}
.predict-result-image.generating .image-container::before,
.predict-result-image.generating .container::before,
.predict-chart-image.generating .image-container::before,
.predict-chart-image.generating .container::before {
    content: "正在分析，请稍候…" !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding-top: 72px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #2563eb !important;
    letter-spacing: 0.02em !important;
    position: absolute !important;
    inset: 0 !important;
    background: rgba(255, 255, 255, 0.82) !important;
    border-radius: 6px !important;
    z-index: 10 !important;
    pointer-events: none !important;
}
.predict-result-image.generating .image-container::after,
.predict-result-image.generating .container::after,
.predict-chart-image.generating .image-container::after,
.predict-chart-image.generating .container::after {
    content: "" !important;
    display: block !important;
    position: absolute !important;
    top: calc(50% - 18px) !important;
    left: 50% !important;
    width: 56px !important;
    height: 56px !important;
    margin: -28px 0 0 -28px !important;
    border: 4px solid #dbeafe !important;
    border-top-color: #2563eb !important;
    border-radius: 50% !important;
    animation: citrus-spin 0.75s linear infinite !important;
    z-index: 11 !important;
    pointer-events: none !important;
    background: transparent !important;
    box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.08) !important;
}
@keyframes citrus-spin {
    to { transform: rotate(360deg); }
}

.page-header {
    text-align: center;
    padding: 18px 24px;
    margin: 0 -24px 20px;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    width: calc(100% + 48px) !important;
}
.page-header h1 {
    font-size: 18px;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
    letter-spacing: 0.02em;
}
.page-header p {
    font-size: 12px;
    color: #64748b;
    margin: 6px 0 0;
}

.app-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
    gap: 12px !important;
    overflow: visible !important;
}
.form-stack, .column, .row-compact, .tabitem {
    overflow: visible !important;
}
.card-title {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 4px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}
.field-label {
    font-size: 13px;
    font-weight: 500;
    color: #475569;
    margin: 0 0 6px 0;
    line-height: 1.4;
}
.hint-text {
    font-size: 12px;
    color: #64748b;
    margin: 0;
    line-height: 1.5;
}
.form-stack { gap: 12px !important; }

.app-card .form,
.app-card.form,
.form-stack .form,
.tabitem .form,
.column .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    gap: 12px !important;
    padding: 0 !important;
}
.app-card .block,
.form-stack .block,
.tabitem .block.padded {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 0 12px 0 !important;
}
.app-card .block:last-child,
.form-stack .block:last-child { margin-bottom: 0 !important; }
.label-wrap, .block-label {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 0 !important;
}
.icon-wrap, .label-icon { display: none !important; }
.upload-box .icon-button,
.upload-box .icon-wrap,
.upload-box .source-selection,
.upload-box .button-row,
.upload-box .image-buttons,
.upload-box .footer,
.upload-box .toolbar-wrap,
.upload-box .tool-buttons {
    display: none !important;
}
/* 文本/数字：单层边框在 wrap 上 */
.field-input input,
.field-input textarea,
.field-input select {
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    background-image: none !important;
    font-size: 14px !important;
    color: #334155 !important;
    box-shadow: none !important;
    filter: none !important;
    min-height: 32px !important;
    line-height: 1.35 !important;
    padding: 5px 10px !important;
}
.field-input .wrap {
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    background-image: none !important;
    box-shadow: none !important;
    filter: none !important;
    min-height: 32px !important;
    padding: 0 !important;
    overflow: visible !important;
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
}
/* 下拉：仅外层 wrap 有边框，内层全部透明无边框，避免「框套框」 */
.field-input.dropdown-field .wrap .container,
.field-input.dropdown-field .wrap .input-container,
.field-input.dropdown-field .wrap .single-select,
.field-input.dropdown-field .wrap .multiselect,
.field-input.dropdown-field .wrap [role="combobox"],
.field-input.dropdown-field .wrap input {
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    outline: none !important;
    min-height: 32px !important;
    line-height: 1.35 !important;
    padding: 5px 10px !important;
    width: 100% !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}
.dropdown-field.block,
.dropdown-field .block,
.dropdown-field .form,
.dropdown-field .label-wrap {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
.field-input ul.options li,
.field-input [role="option"],
.field-input .option {
    cursor: pointer !important;
    padding: 10px 12px !important;
    line-height: 1.45 !important;
    white-space: normal !important;
}
.stage-choice .wrap {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.stage-choice label {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 10px 12px !important;
    margin: 0 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    cursor: pointer !important;
    font-size: 14px !important;
    line-height: 1.45 !important;
}
.stage-choice label:hover {
    border-color: #2563eb !important;
    background: #f8fafc !important;
}
.stage-choice input {
    margin: 0 !important;
    accent-color: #2563eb !important;
}
.field-input input:focus,
.field-input textarea:focus,
.field-input .wrap:focus-within {
    border-color: #2563eb !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.12) !important;
}
.field-input.dropdown-field .wrap:focus-within .container,
.field-input.dropdown-field .wrap:focus-within [role="combobox"] {
    box-shadow: none !important;
}
/* 关联历史预测记录：下拉列表独立定位，避免与输入文字重叠乱码 */
.record-select.field-input .wrap {
    position: relative !important;
}
.record-select .options-wrap,
.record-select ul.options,
.record-select [role="listbox"] {
    position: absolute !important;
    top: calc(100% + 4px) !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    margin: 0 !important;
    z-index: 2000 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12) !important;
    max-height: 260px !important;
    overflow-y: auto !important;
}
.record-select ul.options li,
.record-select [role="option"] {
    font-weight: 400 !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
    line-height: 1.4 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    min-height: unset !important;
}
.record-select .wrap [role="combobox"] {
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}

.upload-box .image-container,
.upload-box .container,
.upload-box .video-container {
    border: 1px dashed #cbd5e1 !important;
    border-radius: 6px !important;
    background: #fafbfc !important;
    min-height: 130px !important;
    transition: border-color 0.15s, background 0.15s !important;
}
.upload-box .image-container:hover,
.upload-box .container:hover {
    border-color: #2563eb !important;
    background: #f8fafc !important;
}
.upload-box .icon-button,
.upload-box .source-selection,
.upload-box .icon-wrap,
.upload-box .button-row,
.upload-box .image-buttons,
.upload-box .footer,
.upload-box .toolbar-wrap,
.upload-box .tool-buttons {
    display: none !important;
}
.upload-box .empty,
.upload-box .upload-text {
    font-size: 13px !important;
    color: #64748b !important;
}
.media-upload-box .wrap,
.media-upload-box .file-preview,
.media-upload-box .upload-container,
.media-upload-box .container,
.media-upload-box .upload-area {
    border: 1px dashed #cbd5e1 !important;
    border-radius: 6px !important;
    background: #fafbfc !important;
    background-image: none !important;
    box-shadow: none !important;
    filter: none !important;
    min-height: 120px !important;
    padding: 16px 12px !important;
    transition: border-color 0.15s, background 0.15s !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}
.media-upload-box .wrap:hover,
.media-upload-box .upload-container:hover,
.media-upload-box .upload-area:hover {
    border-color: #2563eb !important;
    background: #f8fafc !important;
}
.media-upload-box .file-name,
.media-upload-box label,
.media-upload-box .upload-text,
.media-upload-box .empty,
.media-upload-box p,
.media-upload-box span {
    font-size: 12px !important;
    line-height: 1.6 !important;
    color: #64748b !important;
    margin: 0 !important;
    white-space: normal !important;
    word-break: break-word !important;
}
.media-upload-box .file-preview {
    min-height: auto !important;
    padding: 10px 12px !important;
    justify-content: flex-start !important;
    text-align: left !important;
}
.media-upload-box button,
.media-upload-box .icon-button,
.media-upload-box .x-button {
    display: inline-flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}
.media-clear-row {
    margin-top: 4px !important;
}
.media-clear-row button {
    width: auto !important;
    min-height: 34px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    color: #dc2626 !important;
    background: #ffffff !important;
    border: 1px solid #fecaca !important;
    border-radius: 6px !important;
}
.media-clear-row button:hover {
    background: #fef2f2 !important;
    border-color: #fca5a5 !important;
}
.media-preview-wrap {
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    background: #f8fafc !important;
    overflow: hidden !important;
    min-height: 220px !important;
}
.media-preview-wrap .image-container,
.media-preview-wrap .video-container,
.media-preview-wrap .container {
    min-height: 220px !important;
    background: #f8fafc !important;
}
.media-preview-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 220px;
    color: #94a3b8;
    font-size: 13px;
    border: 1px dashed #cbd5e1;
    border-radius: 6px;
    background: #fafbfc;
}

.btn-row { gap: 10px !important; align-items: center !important; margin-top: 4px !important; }
.btn-row > .block { flex: 1 !important; margin: 0 !important; }
.btn-row .form { gap: 10px !important; flex-direction: row !important; }
.btn-row button {
    width: 100% !important;
    min-height: 38px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
.btn-row button.primary {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #2563eb !important;
}
.btn-row button.primary:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}
.btn-row button.secondary {
    background: #ffffff !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
}
.btn-row button.secondary:hover {
    background: #f8fafc !important;
    border-color: #cbd5e1 !important;
}
.btn-full button {
    width: 100% !important;
    min-height: 38px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
}
.btn-full button.primary {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #2563eb !important;
}
.btn-danger-wrap button {
    background: #ffffff !important;
    color: #dc2626 !important;
    border: 1px solid #fecaca !important;
    border-radius: 6px !important;
    min-height: 36px !important;
}

.tabs {
    border-bottom: 1px solid #e2e8f0 !important;
    margin-bottom: 16px !important;
    background: #ffffff !important;
    padding: 0 4px !important;
    border-radius: 8px 8px 0 0 !important;
}
.tab-nav button,
button[role="tab"] {
    font-size: 14px !important;
    color: #64748b !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    background: transparent !important;
    padding: 12px 18px !important;
    box-shadow: none !important;
    font-weight: 400 !important;
}
.tab-nav button.selected,
button[role="tab"][aria-selected="true"] {
    color: #2563eb !important;
    font-weight: 500 !important;
    border-bottom: 2px solid #2563eb !important;
    background: transparent !important;
}
.tabitem { padding-top: 4px !important; }

.yield-value {
    font-size: 36px;
    font-weight: 700;
    color: #2563eb;
    line-height: 1.2;
    margin: 12px 0 8px;
}
.yield-unit { font-size: 16px; color: #64748b; font-weight: 400; }
.info-row { font-size: 14px; color: #334155; margin: 5px 0; line-height: 1.5; }
.info-label { color: #64748b; }
.risk-alert {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    padding: 12px 14px;
    margin-top: 12px;
}
.risk-alert-title { color: #dc2626; font-weight: 600; font-size: 14px; margin-bottom: 6px; }
.risk-alert-text { font-size: 12px; color: #334155; line-height: 1.6; }
.auto-fill-block {
    background: #f1f5f9;
    border-radius: 6px;
    padding: 12px 14px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 16px;
    font-size: 14px;
    margin: 4px 0;
}
.error-calc-block {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 12px;
    color: #334155;
    line-height: 1.6;
    margin: 4px 0;
}
.success-text { color: #16a34a; font-size: 14px; margin: 8px 0 0; }
.fail-text { color: #dc2626; font-size: 14px; margin: 8px 0 0; }
.citrus-toast {
    position: fixed;
    top: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(-12px);
    z-index: 99999;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    line-height: 1.4;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.16);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.22s ease, transform 0.22s ease;
    max-width: min(420px, calc(100vw - 32px));
    text-align: center;
}
.citrus-toast-show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}
.citrus-toast-success {
    background: #f0fdf4;
    color: #15803d;
    border: 1px solid #bbf7d0;
}
.citrus-toast-error {
    background: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
}
.center-narrow { max-width: 960px; width: 100%; }
.center-wide { max-width: 1100px; width: 100%; }
.config-panel { max-width: 720px; width: 100%; overflow: visible !important; }
.config-panel .form-stack { gap: 8px !important; }
.config-panel .field-label { margin: 0 0 4px !important; }
.config-panel .block { margin-bottom: 0 !important; }
.config-panel .form-stack { gap: 8px !important; }
.config-panel .block { margin-bottom: 0 !important; }
.config-panel .field-label { margin-bottom: 4px !important; }

.detection-stats { font-size: 14px; color: #334155; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f1f5f9; }
.history-table-host .prose, .history-table-host .html-container,
.history-table-host [data-testid="html"] {
    overflow: visible !important;
    max-width: 100% !important;
}
.history-table-wrap {
    overflow-x: auto;
    margin-top: 8px;
    width: 100%;
    -webkit-overflow-scrolling: touch;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}
.history-table-wrap table {
    width: 100%;
    min-width: 640px;
    border-collapse: collapse;
    font-size: 14px;
    table-layout: auto;
    border: none;
    margin: 0;
}
.history-table-wrap th {
    font-weight: 600; text-align: left; padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0; background: #f8fafc; color: #475569;
    white-space: nowrap;
}
.history-table-wrap td {
    padding: 8px 12px; border-bottom: 1px solid #e2e8f0;
    color: #334155; white-space: normal; word-break: break-word;
}
.history-table-wrap tbody tr:last-child td { border-bottom: none; }
.history-table-wrap tr:hover td { background: #f8fafc; }
.history-table-header {
    display: grid;
    grid-template-columns: 1.1fr 0.9fr 0.65fr 0.65fr 0.9fr 0.75fr 72px;
    gap: 8px;
    padding: 8px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    font-size: 13px;
    color: #475569;
}
.history-data-row {
    display: grid !important;
    grid-template-columns: 1.1fr 0.9fr 0.65fr 0.65fr 0.9fr 0.75fr 72px !important;
    gap: 8px !important;
    align-items: center !important;
    padding: 8px 12px !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    background: #ffffff !important;
    margin: 0 !important;
}
.history-data-row:last-of-type {
    border-radius: 0 0 6px 6px !important;
}
.history-data-row:hover { background: #f8fafc !important; }
.history-data-row > .block,
.history-data-row > .form {
    margin: 0 !important;
    padding: 0 !important;
    min-width: 0 !important;
}
.history-cell {
    font-size: 14px;
    color: #334155;
    line-height: 1.4;
    word-break: break-word;
}
.btn-delete-row button {
    min-height: 32px !important;
    padding: 4px 10px !important;
    font-size: 13px !important;
    color: #dc2626 !important;
    background: #ffffff !important;
    border: 1px solid #fecaca !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
.btn-delete-row button:hover {
    background: #fef2f2 !important;
    border-color: #fca5a5 !important;
}
.hist-del-btn {
    min-height: 32px;
    padding: 4px 10px;
    font-size: 13px;
    color: #dc2626;
    background: #ffffff;
    border: 1px solid #fecaca;
    border-radius: 6px;
    cursor: pointer;
}
.hist-del-btn:hover {
    background: #fef2f2;
    border-color: #fca5a5;
}
.risk-normal { color: #16a34a; font-weight: 500; }
.risk-warning { color: #dc2626; font-weight: 500; }
.about-content h2 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 18px 0 8px; }
.about-content h2:first-child { margin-top: 0; }
.about-content p, .about-content li { font-size: 14px; color: #334155; line-height: 1.75; }
.about-content ol { padding-left: 20px; margin: 0; }
.trend-title { font-size: 15px !important; font-weight: 700 !important; color: #1e293b !important; margin: 0 0 12px !important; }
.trend-title p { margin: 0 !important; font-size: 15px !important; font-weight: 700 !important; color: #1e293b !important; }

.filter-col { min-width: 260px !important; flex: 0 0 260px !important; }
.filter-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 20px;
    padding: 10px 14px;
    margin-top: 4px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 13px;
    color: #475569;
}
.filter-summary span { white-space: nowrap; }
.filter-summary strong { color: #1e293b; font-weight: 600; }
.chart-col { flex: 1 1 auto !important; min-width: 0 !important; }
.history-filter-bar .block { margin-bottom: 0 !important; }
.history-filter-bar .form-stack { gap: 4px !important; }
.history-filter-bar .field-label { margin-bottom: 2px !important; }
.history-filter-bar .column { gap: 4px !important; }
.orchard-header {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 160px;
    gap: 12px;
    padding: 8px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    font-size: 13px;
    color: #475569;
}
.orchard-data-row {
    display: grid !important;
    grid-template-columns: 2fr 1fr 1fr 160px !important;
    gap: 12px !important;
    align-items: center !important;
    padding: 10px 12px !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    background: #ffffff !important;
}
.orchard-data-row:last-child { border-radius: 0 0 6px 6px !important; }
.orchard-actions { display: flex !important; gap: 8px !important; }
.orchard-actions button:last-child {
    color: #dc2626 !important;
    border-color: #fecaca !important;
}
.orchard-actions button:last-child:hover {
    background: #fef2f2 !important;
}
.row-compact { gap: 20px !important; width: 100% !important; }
.layout-full { width: 100% !important; }
"""


def ensure_detector():
    global detector
    if detector is None:
        try:
            detector = reset_detector(device="cpu")
        except Exception as e:
            print(f"检测器初始化失败: {e}")
            return None
    return detector


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



def clean_display_text(text: str) -> str:
    """移除 emoji，避免 HTML 渲染异常"""
    if not text:
        return ""
    return "".join(ch for ch in str(text) if ord(ch) < 0x10000)


def prepare_display_image(img):
    if img is None:
        return None
    import numpy as np
    from PIL import Image as PILImage
    arr = np.asarray(img)
    if arr.dtype != np.uint8:
        arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8) if arr.max() <= 1.0 else arr.astype(np.uint8)
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    h, w = arr.shape[:2]
    max_side = 960
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        pil = PILImage.fromarray(arr)
        pil = pil.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
        arr = np.array(pil)
    return arr


def resolve_media_path(media_file) -> Optional[str]:
    if media_file is None:
        return None
    if isinstance(media_file, str):
        return media_file
    if isinstance(media_file, dict):
        return media_file.get("path") or media_file.get("name")
    return getattr(media_file, "name", None) or str(media_file)


def is_video_path(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in MEDIA_VIDEO_EXTENSIONS


def preview_media(media_file):
    path = resolve_media_path(media_file)
    if not path or not os.path.isfile(path):
        return clear_preview_outputs()

    if is_video_path(path):
        return (
            gr.update(visible=False),
            gr.update(visible=False, value=None),
            gr.update(visible=True, value=path),
        )
    return (
        gr.update(visible=False),
        gr.update(visible=True, value=path),
        gr.update(visible=False, value=None),
    )


def clear_preview_outputs():
    return (
        gr.update(visible=True, value=MEDIA_PREVIEW_PLACEHOLDER),
        gr.update(visible=False, value=None),
        gr.update(visible=False, value=None),
    )


def clear_media_outputs():
    return (
        gr.update(value=None),
        *clear_preview_outputs(),
    )


def clear_media():
    return clear_media_outputs()


def on_media_upload(media_file):
    path = resolve_media_path(media_file)
    if not path:
        return clear_media_outputs()
    previews = preview_media(media_file)
    return (gr.update(value=media_file), *previews)


def run_prediction(media_file, orchard_name, tree_count, stage_choice, canopy_ratio_pct):
    empty = (None, "", "", "", "", "", gr.update(visible=False, value=""), "", "")
    path = resolve_media_path(media_file)
    if not path or not os.path.isfile(path):
        return empty + (toast_payload("请先上传图片或视频", False),)

    dt = ensure_detector()
    if dt is None:
        return empty + (toast_payload("模型加载失败，请检查依赖安装", False),)

    try:
        params = load_system_params()
        variety = get_orchard_variety(orchard_name)

        video_meta = None
        if is_video_path(path):
            video_result = dt.detect_video(path)
            if not video_result.get("success"):
                return empty + (toast_payload(f"视频处理失败: {video_result.get('error', '未知错误')}", False),)
            counts = video_result["max_counts"]
            total = counts.get("total", 0)
            annotated_img = prepare_display_image(video_result.get("preview_image"))
            video_meta = video_result
        else:
            result = dt.detect_image(path)
            annotated_img = prepare_display_image(result["image"])
            counts = result["counts"]
            total = result["total"]

        stage_info = StageClassifier.classify(counts, total)
        forced = STAGE_UI_MAP.get(stage_choice)
        if forced == "flowering":
            stage_info = {
                **stage_info,
                "stage": "flowering",
                "stage_name": "花期（早期估产）",
                "prediction_mode": "early",
            }
        elif forced == "mature":
            stage_info = {
                **stage_info,
                "stage": "mature",
                "stage_name": "成熟期（产量校正）",
                "prediction_mode": "correction",
            }

        ratio = max(0.05, float(canopy_ratio_pct or 12) / 100.0)
        scale_info = scale_counts_to_tree(
            counts, stage_info["stage"],
            canopy_ratio=ratio,
            variety_name=variety,
        )
        tree_counts = scale_info["scaled"]
        tree_counts["total"] = tree_counts.get("total", 0)

        estimator = YieldEstimator(variety)
        apply_system_params_to_estimator(estimator, params)
        yield_result = estimator.estimate(tree_counts, stage_info, tree_count=int(tree_count or 1))

        db = get_db()
        orchard_id = get_orchard_id(orchard_name)
        if orchard_id is None:
            orchard_id = db.add_orchard(orchard_name, variety, int(tree_count or 1))

        hist = db.get_detection_counts_history(orchard_id)
        alerter = RiskAlerter(variety)
        risk = alerter.evaluate(tree_counts, stage_info, historical_records=hist)

        stage = stage_info["stage"]
        flower_total = tree_counts.get("flower", 0)
        fruit_total = get_fruit_count(tree_counts)

        if stage == "flowering":
            stats_text = f'<div class="detection-stats">检出花朵总数：{flower_total}朵</div>'
        else:
            stats_text = f'<div class="detection-stats">检出果实总数：{fruit_total}个</div>'

        if video_meta is not None:
            sampled = video_meta.get("sampled_frames", 0)
            frame_no = video_meta.get("preview_frame_index")
            if annotated_img is not None and frame_no is not None:
                stats_text += (
                    f'<div class="hint-text" style="margin-top:6px">'
                    f'视频共采样 {sampled} 帧；标注图随机展示第 {frame_no + 1} 帧'
                    f'</div>'
                )
            elif annotated_img is None:
                stats_text += (
                    '<div class="hint-text" style="margin-top:6px">'
                    '未能生成视频标注预览图，产量仍按各采样帧最大值统计'
                    '</div>'
                )

        per_tree = yield_result["per_tree_yield_kg"]
        total_kg = yield_result["predicted_yield_kg"]
        conf = yield_result["confidence"]
        margin = (1 - conf) * 0.25
        low = round(total_kg * (1 - margin), 2)
        high = round(total_kg * (1 + margin), 2)

        info_html = f"""
        <div class="info-row"><span class="info-label">果园：</span>{orchard_name}</div>
        <div class="info-row"><span class="info-label">生长阶段：</span>{stage_info['stage_name']}</div>
        <div class="info-row"><span class="info-label">果树棵数：</span>{int(tree_count or 1)}棵</div>
        """

        yield_html = f'<div class="yield-value">{total_kg}<span class="yield-unit"> kg</span></div>'

        formula_html = f"""
        <div class="info-row">单棵预测：{per_tree} kg/棵</div>
        <div class="info-row">计算逻辑：{yield_result['formula']}</div>
        <div class="info-row">置信度：{conf:.0%}</div>
        """

        range_html = f'<div class="info-row">预估区间：{low} ~ {high} kg</div>'

        show_risk = risk["risk_level"] in ("severe", "warning")
        if show_risk:
            suggestions = "<br>".join(clean_display_text(s) for s in risk.get("suggestions", [])[:3])
            risk_html = f"""
            <div class="risk-alert">
                <div class="risk-alert-title">{clean_display_text(risk['risk_name'])}</div>
                <div class="risk-alert-text">{clean_display_text(risk.get('metric_name', ''))}：当前水平低于历史同期，请关注。<br>{suggestions}</div>
            </div>
            """
        else:
            risk_html = ""

        state = json.dumps({
            "saved": False,
            "orchard_id": orchard_id,
            "counts": tree_counts,
            "stage": stage_info["stage"],
            "predicted_yield": yield_result["predicted_yield_kg"],
            "confidence": yield_result["confidence"],
            "risk_level": risk["risk_level"],
            "risk_ratio": risk["ratio"],
            "variety": variety,
            "orchard": orchard_name,
            "yield_kg": total_kg,
            "stage_name": stage_info["stage_name"],
            "stats": clean_display_text(stats_text),
        }, ensure_ascii=False)

        return (
            annotated_img,
            stats_text,
            info_html,
            yield_html,
            formula_html,
            range_html,
            gr.update(visible=show_risk, value=risk_html),
            state,
            "",
            toast_payload("预测完成，可点击「保存记录」写入历史"),
        )
    except Exception as e:
        traceback.print_exc()
        return empty + (toast_payload(f"处理出错: {str(e)}", False),)


def export_current_record(state_json: str):
    if not state_json:
        return None
    data = json.loads(state_json)
    content = io.StringIO()
    writer = csv.writer(content)
    writer.writerow(["果园", "生长阶段", "预测产量(kg)", "检测统计"])
    writer.writerow([
        data.get("orchard", ""),
        data.get("stage_name", data.get("stage", "")),
        data.get("yield_kg", data.get("predicted_yield", "")),
        data.get("stats", ""),
    ])
    suffix = data.get("record_id", "export")
    tmp = os.path.join(tempfile.gettempdir(), f"prediction_{suffix}.csv")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(content.getvalue())
    return tmp


def save_record_confirm(state_json: str):
    if not state_json:
        return state_json, toast_payload("暂无预测记录可保存", False)
    data = json.loads(state_json)
    if data.get("saved"):
        return state_json, toast_payload("记录已保存")
    db = get_db()
    record_id = db.add_detection(
        orchard_id=data["orchard_id"],
        counts=data["counts"],
        stage=data["stage"],
        predicted_yield=data["predicted_yield"],
        confidence=data["confidence"],
        risk_level=data["risk_level"],
        risk_ratio=data["risk_ratio"],
        variety=data.get("variety", "通用柑橘"),
        image_path="",
    )
    data["saved"] = True
    data["record_id"] = record_id
    return json.dumps(data, ensure_ascii=False), toast_payload("记录已保存")


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


def handle_table_delete(record_id_str, orchard_name, stage_filter, period):
    if not record_id_str or not str(record_id_str).strip().isdigit():
        return (
            gr.update(), gr.update(), gr.update(),
            build_history_table_html(orchard_name, stage_filter, period),
            toast_payload("删除失败，请重试", False),
        )
    get_db().delete_detection(int(record_id_str))
    title, fig = query_history(orchard_name, stage_filter, period)
    summary = build_history_filter_summary(orchard_name, stage_filter, period)
    table = build_history_table_html(orchard_name, stage_filter, period)
    return (
        format_history_title(orchard_name, stage_filter, period),
        fig,
        summary,
        table,
        toast_payload("记录已删除"),
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
        rows.append(
            f"<tr>"
            f"<td>{o['name']}</td>"
            f"<td>{str(o.get('created_at', ''))[:10]}</td>"
            f"<td>{o.get('tree_count', 0)}</td>"
            f"</tr>"
        )
    return f"""
    <div class="history-table-wrap">
        <table>
            <thead>
                <tr><th>果园名称</th><th>建园日期</th><th>果树总量</th></tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </div>
    """


def orchard_ui_pack(selected_id=None, msg="", ok=False):
    choices = get_orchard_dropdown_choices()
    html = build_orchard_table_html()
    if not choices:
        return (
            html,
            gr.update(choices=[], value=None),
            "", 100,
            gr.update(value=f'<p class="fail-text">{msg}</p>' if msg else "", visible=bool(msg)),
        )
    if selected_id is None:
        selected_id = choices[0][1]
    orchard = get_db().get_orchard(int(selected_id))
    if orchard is None:
        selected_id = choices[0][1]
        orchard = get_db().get_orchard(int(selected_id))
    cls = "success-text" if ok else "fail-text"
    msg_html = gr.update(
        value=f'<p class="{cls}">{msg}</p>' if msg else "",
        visible=bool(msg),
    )
    return (
        html,
        gr.update(choices=choices, value=selected_id),
        orchard["name"],
        orchard.get("tree_count", 1),
        msg_html,
    )


def delete_orchard_by_id(orchard_id: int) -> str:
    get_db().delete_orchard(int(orchard_id))
    return "已删除果园"


def update_orchard_by_id(orchard_id: int, name: str, tree_count) -> str:
    name = str(name or "").strip()
    if not name:
        return "果园名称不能为空"
    get_db().update_orchard(int(orchard_id), name=name, tree_count=int(tree_count or 1))
    return f"已更新果园：{name}"


def add_orchard_row(name, tree_count):
    if not name or not str(name).strip():
        return "果园名称不能为空"
    db = get_db()
    db.add_orchard(str(name).strip(), "通用柑橘", int(tree_count or 1))
    return f"已新增果园：{name}"


def submit_actual_yield(option, manual_orchard, harvest_date, total_yield_kg, predicted_str):
    try:
        actual_total = float(total_yield_kg)
        if actual_total <= 0:
            return "", toast_payload("请输入大于 0 的实际采收总产量", False)
    except (TypeError, ValueError):
        return "", toast_payload("请输入有效的实际采收总产量（单位：kg）", False)

    det_id = parse_prediction_option(option)
    db = get_db()

    if det_id is not None:
        rec = db.get_detection(det_id)
        if rec is None:
            return "", toast_payload("关联的预测记录不存在，请重新选择或改用手动录入", False)
        orchard_id = rec["orchard_id"]
        predicted = rec.get("predicted_yield", 0)
        tree_count = db.get_orchard(orchard_id).get("tree_count", 1)
        date_str = (harvest_date or "").strip()[:10] or str(rec.get("detected_at", ""))[:10]
    else:
        orchard_id = get_orchard_id(manual_orchard)
        if orchard_id is None:
            return "", toast_payload("果园不存在，请先在果园管理中新增", False)
        date_str = (harvest_date or "").strip()[:10]
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        if len(date_str) != 10:
            return "", toast_payload("采收日期格式应为 YYYY-MM-DD", False)
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return "", toast_payload("采收日期格式无效，请使用 YYYY-MM-DD", False)
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
        return "", toast_payload(
            f"保存成功。预测 {predicted} kg，实际 {actual_total:.2f} kg，误差 {error_pct:.1f}%",
        )
    return "", toast_payload(
        f"保存成功。实际总产量 {actual_total:.2f} kg（约 {per_tree:.2f} kg/棵）",
    )


def save_system_params_ui(rate_pct, weight_g, risk_threshold):
    params = {
        "flower_fruit_rate_pct": float(rate_pct),
        "avg_weight_g": float(weight_g),
        "risk_warning_threshold": float(risk_threshold),
    }
    save_system_params(params)
    return "系统参数已保存"


def create_ui():
    if gr is None:
        raise RuntimeError("Gradio 未安装")

    params = load_system_params()
    save_system_params(params)

    with gr.Blocks(title="柑橘果园智能产量预测系统", fill_width=True) as demo:
        gr.HTML("""
        <div class="page-header">
            <h1>柑橘果园智能产量预测系统</h1>
            <p>基于计算机视觉的分阶段产量预测与风险预警</p>
        </div>
        """)
        prediction_state = gr.State("")
        toast_trigger = gr.Textbox(
            visible=False,
            container=False,
            elem_id="toast_trigger",
            elem_classes=["toast-trigger"],
        )

        with gr.Tab("产量预测"):
            with gr.Row(elem_classes=["row-compact", "layout-full"]):
                with gr.Column(scale=1, elem_classes=["app-card", "form-stack"]):
                    gr.HTML('<div class="card-title">图片/视频上传</div>')
                    field_label("上传图片或视频")
                    media_input = gr.File(
                        file_count="single",
                        file_types=MEDIA_FILE_TYPES,
                        type="filepath",
                        height=120,
                        show_label=False,
                        container=False,
                        elem_classes=["media-upload-box"],
                    )
                    with gr.Row(elem_classes=["media-clear-row"]):
                        clear_media_btn = gr.Button("清除并重新上传", variant="secondary", size="sm")
                    media_preview_placeholder = gr.HTML(
                        MEDIA_PREVIEW_PLACEHOLDER,
                        elem_classes=["media-preview-wrap"],
                    )
                    image_preview = gr.Image(
                        show_label=False, container=False, height=240,
                        type="filepath", interactive=False, visible=False,
                        elem_classes=["media-preview-wrap"],
                    )
                    video_preview = gr.Video(
                        show_label=False, container=False, height=240,
                        interactive=False, visible=False,
                        elem_classes=["media-preview-wrap"],
                    )
                    gr.HTML('<p class="hint-text">支持 JPG、PNG、WEBP 图片或 MP4、AVI、MOV 视频；可清除后重新选择</p>')

                with gr.Column(scale=1, elem_classes=["app-card", "form-stack"]):
                    gr.HTML('<div class="card-title">预测参数设置</div>')
                    field_label("所属果园")
                    orchard_name = gr.Dropdown(
                        choices=get_orchard_list(), value=default_orchard_name(),
                        allow_custom_value=True, **dropdown_cls("field-input"),
                    )
                    field_label("果树棵数")
                    tree_count = gr.Number(value=1, minimum=1, step=1, **input_cls("field-input"))
                    field_label("生长阶段")
                    stage_choice = gr.Radio(
                        choices=STAGE_UI_OPTIONS,
                        value=STAGE_UI_OPTIONS[0],
                        **input_cls("stage-choice"),
                    )
                    field_label("树冠可见占比")
                    canopy_ratio_pct = gr.Number(
                        value=12, minimum=5, maximum=40, step=1, **input_cls("field-input"),
                    )
                    gr.HTML('<p class="hint-text">图片可见树冠比例，用于整树数量换算</p>')
                    with gr.Row(elem_classes=["btn-full"]):
                        predict_btn = gr.Button("开始预测", variant="primary")

            with gr.Column(elem_classes=["app-card", "form-stack", "layout-full"]):
                gr.HTML('<div class="card-title">预测结果</div>')
                gr.HTML('<p class="hint-text" id="result-placeholder">提交预测后，标注图与产量结果将显示在下方</p>')
                with gr.Row(elem_classes=["row-compact", "layout-full"], equal_height=True):
                    with gr.Column(scale=2, elem_classes=["app-card"]):
                        gr.HTML('<div class="card-title">目标识别标注图</div>')
                        annotated_output = gr.Image(
                            show_label=False, container=False, buttons=None, height=420,
                            elem_classes=["predict-result-image"],
                        )
                        detection_stats = gr.HTML("")
                    with gr.Column(scale=1, elem_classes=["app-card", "form-stack"]):
                        gr.HTML('<div class="card-title">产量测算结果</div>')
                        result_info = gr.HTML("")
                        yield_value = gr.HTML("")
                        yield_formula = gr.HTML("")
                        yield_range = gr.HTML("")
                        risk_block = gr.HTML(visible=False)
                        with gr.Row(elem_classes=["btn-row"]):
                            save_btn = gr.Button("保存记录", variant="secondary", scale=1)
                            export_btn = gr.Button("导出", variant="secondary", scale=1)
                        export_file = gr.File(label="下载", visible=False, container=False)

            media_input.upload(
                on_media_upload,
                inputs=[media_input],
                outputs=[media_input, media_preview_placeholder, image_preview, video_preview],
                queue=False,
                show_progress="hidden",
            )
            media_input.change(
                on_media_upload,
                inputs=[media_input],
                outputs=[media_input, media_preview_placeholder, image_preview, video_preview],
                queue=False,
                show_progress="hidden",
            )
            clear_media_btn.click(
                clear_media,
                outputs=[media_input, media_preview_placeholder, image_preview, video_preview],
                queue=False,
                show_progress="hidden",
            )
            media_input.clear(
                clear_media,
                outputs=[media_input, media_preview_placeholder, image_preview, video_preview],
                queue=False,
                show_progress="hidden",
            )

            predict_btn.click(
                run_prediction,
                inputs=[media_input, orchard_name, tree_count, stage_choice, canopy_ratio_pct],
                outputs=[
                    annotated_output, detection_stats,
                    result_info, yield_value, yield_formula, yield_range,
                    risk_block, prediction_state, toast_trigger,
                ],
                show_progress="full",
                show_progress_on=annotated_output,
            )
            save_btn.click(
                save_record_confirm,
                inputs=prediction_state,
                outputs=[prediction_state, toast_trigger],
                queue=False,
                show_progress="hidden",
            )
            export_btn.click(export_current_record, inputs=prediction_state, outputs=export_file)

        with gr.Tab("历史数据"):
            with gr.Column(elem_classes=["app-card", "form-stack"]):
                gr.HTML('<div class="card-title">筛选条件</div>')
                with gr.Row(elem_classes=["history-filter-bar", "layout-full"]):
                    with gr.Column(scale=3, elem_classes=["form-stack"]):
                        field_label("果园")
                        hist_orchard = gr.Dropdown(
                            choices=get_orchard_list(), value=default_orchard_name(), **dropdown_cls("field-input"),
                        )
                    with gr.Column(scale=2, elem_classes=["form-stack"]):
                        field_label("阶段")
                        hist_stage = gr.Dropdown(
                            choices=["全部阶段", "花期", "成熟期"], value="全部阶段", **dropdown_cls("field-input"),
                        )
                    with gr.Column(scale=2, elem_classes=["form-stack"]):
                        field_label("统计周期")
                        hist_period = gr.Dropdown(
                            choices=["近3个月", "近6个月", "近1年", "全部"], value="近1年", **dropdown_cls("field-input"),
                        )
                    with gr.Column(scale=1, min_width=120, elem_classes=["form-stack"]):
                        gr.HTML('<div class="field-label">&nbsp;</div>')
                        hist_query_btn = gr.Button("查询数据", variant="primary")
                hist_filter_summary = gr.HTML("")

            with gr.Column(elem_classes=["app-card", "layout-full"]):
                trend_title = gr.Markdown("产量趋势图", elem_classes=["trend-title"])
                trend_output = gr.Image(
                    show_label=False, container=False, buttons=None, height=420,
                    elem_classes=["predict-chart-image"],
                )

            with gr.Column(elem_classes=["app-card", "form-stack", "history-table-host"]):
                gr.HTML('<div class="card-title">历史预测明细</div>')
                batch_export_btn = gr.DownloadButton("批量导出", variant="secondary")
                history_table_html = gr.HTML(HISTORY_TABLE_PLACEHOLDER)
                delete_record_id = gr.Textbox(
                    visible=False, container=False,
                    elem_id="hist_delete_id",
                    elem_classes=["hist-delete-id-input"],
                )
                delete_record_submit = gr.Button(
                    "删除", visible=False,
                    elem_id="hist_delete_submit",
                    elem_classes=["hist-delete-submit"],
                )

            hist_filter_inputs = [hist_orchard, hist_stage, hist_period]
            hist_query_outputs = [trend_title, trend_output, hist_filter_summary, history_table_html]

            hist_query_btn.click(
                apply_history_filters,
                inputs=hist_filter_inputs,
                outputs=hist_query_outputs,
                show_progress="full",
                show_progress_on=trend_output,
            )
            for _hist_filter in (hist_orchard, hist_stage, hist_period):
                _hist_filter.change(
                    apply_history_filters,
                    inputs=hist_filter_inputs,
                    outputs=hist_query_outputs,
                    queue=False,
                    show_progress="full",
                    show_progress_on=trend_output,
                )
            batch_export_btn.click(
                export_history_batch,
                inputs=hist_filter_inputs,
                outputs=batch_export_btn,
            )
            delete_record_submit.click(
                handle_table_delete,
                inputs=[delete_record_id, hist_orchard, hist_stage, hist_period],
                outputs=hist_query_outputs + [toast_trigger],
                queue=False,
                show_progress="hidden",
            )

        with gr.Tab("数据配置"):
            with gr.Tabs():
                with gr.Tab("实际产量录入"):
                    with gr.Column(elem_classes=["layout-full", "form-stack"]):
                        with gr.Column(elem_classes=["app-card", "form-stack", "config-panel"]):
                            field_label("关联历史预测记录")
                            record_option = gr.Dropdown(
                                choices=get_prediction_options(default_orchard_name()),
                                value="manual",
                                **record_select_cls(),
                            )
                            gr.HTML('<p class="hint-text">选择后将自动填充果园、日期信息</p>')
                            auto_fill_block = gr.HTML(visible=False)
                            with gr.Column(visible=True, elem_classes=["form-stack"]) as manual_block:
                                field_label("所属果园")
                                manual_orchard = gr.Dropdown(
                                    choices=get_orchard_list(), value=default_orchard_name(), **dropdown_cls("field-input"),
                                )
                                field_label("采收日期")
                                harvest_date = gr.Textbox(
                                    placeholder="YYYY-MM-DD",
                                    value=datetime.now().strftime("%Y-%m-%d"),
                                    **input_cls("field-input"),
                                )
                            field_label("果园实际采收总产量（kg）")
                            total_yield_input = gr.Number(minimum=0, step=0.1, **input_cls("field-input"))
                            gr.HTML("""
                            <p class="hint-text">填写整园总产量即可，无需逐棵统计；系统会按果园棵数自动换算单棵均值。</p>
                            <div class="error-calc-block">
                                提交后将根据关联预测记录计算预测值与实际值的相对误差；
                                若无关联记录，仅保存实际产量数据供后续分析。
                            </div>
                            """)
                            with gr.Row(elem_classes=["btn-full"]):
                                ay_submit_btn = gr.Button("提交保存", variant="primary")
                            ay_result = gr.HTML("")
                            hidden_predicted = gr.Textbox(visible=False, container=False)
                            hidden_stage = gr.Textbox(visible=False, container=False)

                        record_option.change(
                            on_prediction_record_select,
                            inputs=record_option,
                            outputs=[
                                auto_fill_block, manual_block,
                                manual_orchard, harvest_date,
                                hidden_stage, hidden_predicted,
                            ],
                        )
                        manual_orchard.change(
                            refresh_prediction_record_options,
                            inputs=[manual_orchard, record_option],
                            outputs=[record_option],
                            queue=False,
                        )
                        ay_submit_btn.click(
                            submit_actual_yield,
                            inputs=[record_option, manual_orchard, harvest_date, total_yield_input, hidden_predicted],
                            outputs=[ay_result, toast_trigger],
                            queue=False,
                            show_progress="hidden",
                        )

                with gr.Tab("果园信息管理"):
                    with gr.Column(elem_classes=["app-card", "form-stack"]):
                        gr.HTML('<div class="card-title">新增果园</div>')
                        with gr.Row(elem_classes=["row-compact"]):
                            with gr.Column(scale=3, elem_classes=["form-stack"]):
                                field_label("果园名称")
                                new_orchard_name = gr.Textbox(**input_cls("field-input"))
                            with gr.Column(scale=2, elem_classes=["form-stack"]):
                                field_label("果树总量")
                                new_tree_count = gr.Number(value=100, minimum=1, step=1, **input_cls("field-input"))
                            with gr.Column(scale=1, elem_classes=["form-stack"]):
                                gr.HTML('<div class="field-label">&nbsp;</div>')
                                add_orchard_btn = gr.Button("新增果园", variant="primary")
                        orchard_msg = gr.HTML(visible=False)

                        gr.HTML('<div class="card-title" style="margin-top:8px">果园列表</div>')
                        orchard_list_html = gr.HTML(
                            build_orchard_table_html(), elem_classes=["history-table-host"],
                        )

                        gr.HTML('<div class="card-title" style="margin-top:8px">编辑果园</div>')
                        _choices = get_orchard_dropdown_choices()
                        _default_id = _choices[0][1] if _choices else None
                        _default_orchard = get_db().get_orchard(_default_id) if _default_id else None
                        field_label("选择果园")
                        orchard_select = gr.Dropdown(
                            choices=_choices,
                            value=_default_id,
                            **dropdown_cls("field-input"),
                        )
                        field_label("果园名称")
                        edit_orchard_name = gr.Textbox(
                            value=_default_orchard["name"] if _default_orchard else "",
                            **input_cls("field-input"),
                        )
                        field_label("果树总量")
                        edit_orchard_trees = gr.Number(
                            value=_default_orchard.get("tree_count", 1) if _default_orchard else 100,
                            minimum=1, step=1, **input_cls("field-input"),
                        )
                        with gr.Row(elem_classes=["btn-row"]):
                            save_orchard_btn = gr.Button("保存修改", variant="primary")
                            delete_orchard_btn = gr.Button("删除", variant="secondary")

                    def on_orchard_select(orchard_id):
                        if orchard_id is None:
                            return "", 100
                        orchard = get_db().get_orchard(int(orchard_id))
                        if orchard is None:
                            return "", 100
                        return orchard["name"], orchard.get("tree_count", 1)

                    def add_orchard_handler(name, tree_count):
                        msg = add_orchard_row(name, tree_count)
                        ok = "已新增" in msg
                        oid = get_orchard_id(str(name).strip()) if ok else None
                        pack = orchard_ui_pack(selected_id=oid, msg=msg, ok=ok)
                        return (*pack, "" if ok else name)

                    def save_orchard_handler(orchard_id, name, trees):
                        msg = update_orchard_by_id(orchard_id, name, trees)
                        ok = "已更新" in msg
                        return orchard_ui_pack(selected_id=orchard_id, msg=msg, ok=ok)

                    def delete_orchard_handler(orchard_id):
                        if orchard_id is None:
                            return orchard_ui_pack(msg="请先选择果园", ok=False)
                        delete_orchard_by_id(int(orchard_id))
                        return orchard_ui_pack(msg="已删除果园", ok=True)

                    orchard_select.change(
                        on_orchard_select,
                        inputs=[orchard_select],
                        outputs=[edit_orchard_name, edit_orchard_trees],
                    )
                    add_orchard_btn.click(
                        add_orchard_handler,
                        inputs=[new_orchard_name, new_tree_count],
                        outputs=[
                            orchard_list_html, orchard_select,
                            edit_orchard_name, edit_orchard_trees,
                            orchard_msg, new_orchard_name,
                        ],
                        queue=False,
                    )
                    save_orchard_btn.click(
                        save_orchard_handler,
                        inputs=[orchard_select, edit_orchard_name, edit_orchard_trees],
                        outputs=[
                            orchard_list_html, orchard_select,
                            edit_orchard_name, edit_orchard_trees, orchard_msg,
                        ],
                        queue=False,
                    )
                    delete_orchard_btn.click(
                        delete_orchard_handler,
                        inputs=[orchard_select],
                        outputs=[
                            orchard_list_html, orchard_select,
                            edit_orchard_name, edit_orchard_trees, orchard_msg,
                        ],
                        queue=False,
                    )

                with gr.Tab("预测参数配置"):
                    with gr.Column(elem_classes=["layout-full", "form-stack"]):
                        with gr.Column(elem_classes=["app-card", "form-stack", "config-panel"]):
                            field_label("平均坐果率")
                            param_rate = gr.Number(value=params["flower_fruit_rate_pct"], **input_cls("field-input"))
                            gr.HTML('<p class="hint-text">常规柑橘参考 2.0 ~ 3.0%</p>')
                            field_label("单果平均重量")
                            param_weight = gr.Number(value=params["avg_weight_g"], **input_cls("field-input"))
                            gr.HTML('<p class="hint-text">普通柑橘参考 120 ~ 180g</p>')
                            field_label("低产预警阈值")
                            param_risk = gr.Number(value=params["risk_warning_threshold"], **input_cls("field-input"))
                            gr.HTML('<p class="hint-text">低于同期均值该比例自动触发预警</p>')
                            with gr.Row(elem_classes=["btn-full"]):
                                param_save_btn = gr.Button("保存系统参数", variant="primary")
                            param_result = gr.HTML(visible=False)

                        def save_params_with_msg(rate_pct, weight_g, risk_threshold):
                            msg = save_system_params_ui(rate_pct, weight_g, risk_threshold)
                            return gr.update(value=f'<p class="success-text">{msg}</p>', visible=True)

                        param_save_btn.click(
                            save_params_with_msg,
                            inputs=[param_rate, param_weight, param_risk],
                            outputs=param_result,
                            queue=False,
                        )

        with gr.Tab("系统说明"):
            with gr.Column(elem_classes=["layout-full"]):
                gr.HTML("""
                <div class="app-card about-content" style="max-width:1100px">
                    <div class="card-title">系统说明</div>
                    <h2>项目背景</h2>
                    <p>本系统面向重庆地区柑橘种植场景，通过计算机视觉识别果树图片或视频中的花朵与果实，
                    结合生长阶段与历史数据，实现分阶段产量预测与低产风险预警。</p>
                    <h2>使用流程</h2>
                    <ol>
                        <li>在产量预测页上传果树图片或视频，设置果园、棵数、生长阶段及树冠可见占比。</li>
                        <li>点击开始AI预测，查看标注结果与产量测算数据，必要时保存或导出记录。</li>
                        <li>在历史数据页按果园、阶段与周期查询趋势图及明细，支持批量导出。</li>
                        <li>在数据配置页录入实际产量、管理果园信息并调整预测参数。</li>
                    </ol>
                    <h2>技术实现</h2>
                    <p>系统采用 YOLO 目标检测识别花朵与果实，依据生长阶段选用不同产量估算公式，
                    结合可见冠幅比例外推整树数量，并与历史同期数据对比触发低产预警。
                    后端使用 Python、PyTorch、SQLite，前端基于 Gradio 构建。</p>
                    <h2>开发团队和版权信息</h2>
                    <p>智能系统综合实践小组 · 柑橘果园智能产量预测系统 v1.0</p>
                </div>
                """)

    return demo


def main():
    if gr is None:
        print("错误: Gradio 未安装，无法启动Web界面")
        print("请运行: pip install gradio")
        return

    _ = get_db()
    demo = create_ui()
    demo.queue(default_concurrency_limit=8)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=GLOBAL_CSS,
        theme=build_theme(),
        js=HIST_DELETE_JS,
    )


if __name__ == "__main__":
    main()
