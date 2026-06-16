"""Assemble Gradio application."""
from data.database import get_db

try:
    import gradio as gr
except ImportError:
    gr = None

from ui.charts import setup_matplotlib_chinese
from ui.client_js import APP_JS
from ui.components import GLOBAL_CSS, build_theme, toast_overlay
from ui.handlers import load_system_params, save_system_params
from ui.pages.about import render_about_tab
from ui.pages.actual_yield import render_actual_yield_tab
from ui.pages.config import render_config_tab
from ui.pages.history import render_history_tab
from ui.pages.predict import render_prediction_tab


def create_ui():
    if gr is None:
        raise RuntimeError("Gradio 未安装")

    setup_matplotlib_chinese()

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
        app_toast = toast_overlay()

        # Render history first so prediction tab can refresh it after saving.
        history_tab = render_history_tab(prediction_state, app_toast)
        render_prediction_tab(prediction_state, app_toast, history_tab)
        render_actual_yield_tab(app_toast)
        render_config_tab(demo, prediction_state, params, app_toast)
        render_about_tab(prediction_state)

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
