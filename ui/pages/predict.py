"""产量预测页"""
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


def render_prediction_tab(prediction_state, app_toast):
    with gr.Tab("产量预测"):
        with gr.Row(elem_classes=["row-compact", "layout-full"]):
            with gr.Column(scale=1, elem_classes=["app-card", "form-stack"]):
                gr.HTML('<div class="card-title">图片/视频上传</div>')
                field_label("上传图片或视频")
                media_path_state = gr.State(value=None)
                media_input = gr.File(
                    file_count="single",
                    file_types=MEDIA_FILE_TYPES,
                    type="filepath",
                    height=120,
                    show_label=False,
                    container=False,
                    elem_id="citrus_media_input",
                    elem_classes=["media-upload-box"],
                    preserved_by_key=None,
                )
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
                with gr.Row(elem_classes=["media-clear-row"]):
                    clear_media_btn = gr.ClearButton(
                        [media_input, image_preview, video_preview],
                        value="清除并重新上传",
                        variant="secondary",
                        size="sm",
                        elem_id="citrus_clear_media",
                        elem_classes=["media-clear-trigger"],
                    )
                gr.HTML('<p class="hint-text">支持 JPG、PNG、WEBP 图片或 MP4、AVI、MOV 视频；可清除后重新选择</p>')

            with gr.Column(scale=1, elem_classes=["app-card", "form-stack"]):
                gr.HTML('<div class="card-title">预测参数设置</div>')
                orchard_name = gr.Dropdown(
                    choices=get_orchard_list(),
                    value=default_orchard_name(),
                    **dropdown_cls("所属果园", allow_custom_value=True),
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

        with gr.Column(
            visible=False,
            elem_classes=["app-card", "form-stack", "layout-full", "predict-result-panel"],
        ) as result_block:
            gr.HTML('<div class="card-title">预测结果</div>')
            with gr.Row(elem_classes=["row-compact", "layout-full"], equal_height=True):
                with gr.Column(scale=2, elem_classes=["app-card"]):
                    gr.HTML('<div class="card-title">目标识别标注图</div>')
                    annotated_output = gr.Image(
                        show_label=False, container=False, buttons=[], height=420,
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
                    save_status = gr.HTML("")
                    export_file = gr.File(label="下载", visible=False, container=False)

        preview_outputs = [media_path_state, media_preview_placeholder, image_preview, video_preview]

        media_input.upload(
            sync_media_upload,
            inputs=[media_input],
            outputs=preview_outputs,
            queue=False,
            show_progress="hidden",
        )
        media_input.change(
            sync_media_upload,
            inputs=[media_input],
            outputs=preview_outputs,
            queue=False,
            show_progress="hidden",
        )
        clear_media_btn.click(
            clear_media_all,
            outputs=[media_input, media_path_state, media_preview_placeholder, image_preview, video_preview],
            queue=False,
            show_progress="hidden",
        )
        media_input.clear(
            on_media_cleared,
            inputs=[],
            outputs=[media_path_state, media_preview_placeholder, image_preview, video_preview],
            queue=False,
            show_progress="hidden",
        )
        media_input.delete(
            on_media_cleared,
            inputs=[],
            outputs=[media_path_state, media_preview_placeholder, image_preview, video_preview],
            queue=False,
            show_progress="hidden",
        )

        predict_outputs = [
            result_block,
            annotated_output, detection_stats,
            result_info, yield_value, yield_formula, yield_range,
            risk_block, prediction_state, app_toast,
        ]
        predict_btn.click(
            show_predict_result_panel,
            outputs=[result_block],
            queue=False,
            show_progress="hidden",
        ).then(
            run_prediction,
            inputs=[media_path_state, orchard_name, tree_count, stage_choice, canopy_ratio_pct],
            outputs=predict_outputs,
            show_progress="full",
            show_progress_on=annotated_output,
        )
        save_btn.click(
            save_record_full,
            inputs=prediction_state,
            outputs=[prediction_state, app_toast, save_status],
            show_progress="hidden",
        )
        export_btn.click(export_current_record, inputs=prediction_state, outputs=export_file)
