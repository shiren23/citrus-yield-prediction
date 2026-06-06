"""历史数据页"""
from datetime import datetime

import gradio as gr

from data.database import get_db
from ui.client_js import HIST_DELETE_PREPROCESS_JS
from ui.components import dropdown_cls, field_label, input_cls, record_select_cls
from ui.constants import (
    HISTORY_TABLE_PLACEHOLDER,
    MEDIA_FILE_TYPES,
    MEDIA_PREVIEW_PLACEHOLDER,
    STAGE_UI_OPTIONS,
)
from ui.handlers import *


def render_history_tab(prediction_state, app_toast):
    _init = initial_history_view()

    with gr.Tab("历史数据"):
        with gr.Column(elem_classes=["app-card", "form-stack"]):
            gr.HTML('<div class="card-title">筛选条件</div>')
            with gr.Row(elem_classes=["history-filter-bar", "layout-full"], equal_height=True):
                with gr.Column(scale=3, elem_classes=["form-stack"]):
                    hist_orchard = gr.Dropdown(
                        choices=get_orchard_list(),
                        value=default_orchard_name(),
                        **dropdown_cls("果园", filterable=False),
                    )
                with gr.Column(scale=2, elem_classes=["form-stack"]):
                    hist_stage = gr.Dropdown(
                        choices=["全部阶段", "花期", "成熟期"],
                        value="全部阶段",
                        **dropdown_cls("阶段", filterable=False),
                    )
                with gr.Column(scale=2, elem_classes=["form-stack"]):
                    hist_period = gr.Dropdown(
                        choices=["近3个月", "近6个月", "近1年", "全部"],
                        value="近1年",
                        **dropdown_cls("统计周期", filterable=False),
                    )
                with gr.Column(scale=1, min_width=120, elem_classes=["form-stack", "history-filter-actions"]):
                    gr.HTML('<div class="field-label">&nbsp;</div>')
                    hist_query_btn = gr.Button("查询数据", variant="primary")
            hist_filter_summary = gr.HTML(_init[2])

        with gr.Column(elem_classes=["app-card", "layout-full"]):
            trend_title = gr.Markdown(_init[0], elem_classes=["trend-title"])
            trend_output = gr.Image(
                value=_init[1],
                show_label=False, container=False, buttons=[], height=420,
                elem_classes=["predict-chart-image"],
            )

        with gr.Column(elem_classes=["app-card", "form-stack", "history-table-host"]):
            gr.HTML('<div class="card-title">历史预测明细</div>')
            gr.HTML('<p class="hint-text">点击表格每行右侧「删除」可移除该条记录。</p>')
            batch_export_btn = gr.DownloadButton("批量导出", variant="secondary")
            history_table_html = gr.HTML(_init[3])
            hist_delete_status = gr.HTML("")
            delete_record_id = gr.Textbox(
                value="",
                visible=False,
                container=False,
                elem_id="hist_delete_id",
                elem_classes=["hist-delete-id-input"],
            )
            delete_record_submit = gr.Button(
                "删除", visible=False,
                elem_id="hist_delete_submit",
                elem_classes=["hist-delete-submit"],
            )

        hist_filter_inputs = [hist_orchard, hist_stage, hist_period]
        hist_query_outputs = [
            trend_title, trend_output, hist_filter_summary, history_table_html,
        ]
        hist_delete_outputs = hist_query_outputs + [app_toast, hist_delete_status]

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
            outputs=hist_delete_outputs,
            js=HIST_DELETE_PREPROCESS_JS,
            show_progress="hidden",
        )
