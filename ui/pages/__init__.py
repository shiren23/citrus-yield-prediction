"""各主 Tab 界面布局（Gradio 组件与事件绑定）。"""
from ui.pages.about import render_about_tab
from ui.pages.config import render_config_tab
from ui.pages.history import render_history_tab
from ui.pages.predict import render_prediction_tab

__all__ = [
    "render_about_tab",
    "render_config_tab",
    "render_history_tab",
    "render_prediction_tab",
]
