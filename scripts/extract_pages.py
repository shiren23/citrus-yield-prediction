# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTORY = ROOT / "ui" / "factory.py"
PAGES = ROOT / "ui" / "pages"

PAGE_IMPORTS = '''"""{title}"""
from datetime import datetime

import gradio as gr

from data.database import get_db
from ui.components import dropdown_cls, field_label, input_cls, record_select_cls
from ui.constants import (
    HISTORY_TABLE_PLACEHOLDER,
    MEDIA_FILE_TYPES,
    MEDIA_PREVIEW_PLACEHOLDER,
    STAGE_UI_OPTIONS,
)
from ui.handlers import *
'''


def reindent(lines: list) -> str:
    out = []
    for line in lines:
        if line.startswith("        "):
            out.append("    " + line[8:])
        elif line.strip() == "":
            out.append("\n")
        else:
            out.append("    " + line)
    return "".join(out)


def make_page(name: str, title: str, slice_range: tuple, sig: str):
    lines = FACTORY.read_text(encoding="utf-8").splitlines(keepends=True)
    a, b = slice_range
    body = reindent(lines[a - 1 : b])
    return (
        PAGE_IMPORTS.format(title=title)
        + f"\n\ndef {name}({sig}):\n"
        + body
    )


def main():
    PAGES.mkdir(exist_ok=True)
    (PAGES / "predict.py").write_text(
        make_page("render_prediction_tab", "产量预测页", (45, 169), "prediction_state, toast_trigger"),
        encoding="utf-8",
    )
    (PAGES / "history.py").write_text(
        make_page("render_history_tab", "历史数据页", (170, 247), "prediction_state, toast_trigger"),
        encoding="utf-8",
    )
    (PAGES / "config.py").write_text(
        make_page("render_config_tab", "数据配置页", (248, 440), "prediction_state, toast_trigger, params"),
        encoding="utf-8",
    )
    (PAGES / "about.py").write_text(
        make_page("render_about_tab", "系统说明页", (441, 464), "prediction_state, toast_trigger"),
        encoding="utf-8",
    )

    FACTORY.write_text(
        '''"""Assemble Gradio application."""
from data.database import get_db

try:
    import gradio as gr
except ImportError:
    gr = None

from ui.client_js import APP_JS
from ui.components import GLOBAL_CSS, build_theme
from ui.handlers import load_system_params, save_system_params
from ui.pages.about import render_about_tab
from ui.pages.config import render_config_tab
from ui.pages.history import render_history_tab
from ui.pages.predict import render_prediction_tab


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

        render_prediction_tab(prediction_state, toast_trigger)
        render_history_tab(prediction_state, toast_trigger)
        render_config_tab(prediction_state, toast_trigger, params)
        render_about_tab(prediction_state, toast_trigger)

    return demo


def launch_app():
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
        js=APP_JS,
    )
''',
        encoding="utf-8",
    )
    print("Done.")


if __name__ == "__main__":
    main()
