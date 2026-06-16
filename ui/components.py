"""UI component helpers."""
import html
import time

try:
    import gradio as gr
except ImportError:
    gr = None

from ui.styles import GLOBAL_CSS  # noqa: F401 - re-export for factory

INPUT_KW = {"show_label": False, "container": False}


def input_cls(*classes):
    kw = dict(INPUT_KW)
    kw["elem_classes"] = list(classes)
    return kw


def dropdown_cls(label="", *, filterable=True, allow_custom_value=False):
    """Gradio Dropdown 配置。"""
    kw = {
        "label": label,
        "show_label": bool(label),
        "container": bool(label),
        "filterable": filterable,
        "elem_classes": ["dropdown-field"],
    }
    if allow_custom_value:
        kw["allow_custom_value"] = True
    return kw


def record_select_cls():
    return {
        "show_label": False,
        "container": False,
        "elem_classes": ["field-input", "dropdown-field", "record-select"],
    }


def toast_html(message: str, ok: bool = True) -> str:
    """返回居中 toast 的 HTML 内容。"""
    if ok:
        bg, color, border = "#f0fdf4", "#15803d", "#bbf7d0"
    else:
        bg, color, border = "#fef2f2", "#b91c1c", "#fecaca"
    safe = html.escape(str(message))
    nonce = time.time_ns()
    style = (
        "position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);"
        "padding:16px 30px;border-radius:12px;font-size:16px;font-weight:700;"
        "line-height:1.45;text-align:center;pointer-events:none;z-index:9999;"
        f"background:{bg};color:{color};border:1px solid {border};"
        "box-shadow:0 18px 46px rgba(15,23,42,0.22);"
        "max-width:min(420px,calc(100vw - 32px));"
        "animation:citrus-toast-auto-hide 2s ease forwards;"
    )
    kind = "citrus-toast-success" if ok else "citrus-toast-error"
    return (
        f'<div class="citrus-toast-inline {kind}" style="{style}" '
        f'data-toast-ts="{nonce}" data-toast-nonce="{nonce}" role="status">{safe}</div>'
    )


def toast_output(message: str, ok: bool = True):
    """写入 toast 组件的标准返回值（预测/保存/删除等统一使用）。"""
    if gr is None:
        return toast_html(message, ok)
    return gr.update(value=toast_html(message, ok))


def toast_overlay():
    """统一的 gr.HTML toast 容器。"""
    return gr.HTML(
        value="",
        show_label=False,
        container=False,
        elem_id="app_toast",
        elem_classes=["citrus-toast-overlay"],
    )


def status_html(message: str, ok: bool = True) -> str:
    """按钮旁可见的状态提示（不依赖居中 toast 动画）。"""
    cls = "success-text" if ok else "fail-text"
    return f'<p class="{cls}">{html.escape(str(message))}</p>'


def toast_payload(message: str, ok: bool = True) -> str:
    return toast_html(message, ok)


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
