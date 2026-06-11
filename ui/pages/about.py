"""系统说明页"""
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


def render_about_tab(prediction_state):
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

