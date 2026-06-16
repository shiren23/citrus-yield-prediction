"""系统设置（原：数据配置页）"""
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
from ui.handlers.orchard_data import (
    ORCHARD_DROPDOWNS,
    refresh_all_orchard_dropdowns,
    register_orchard_dropdown,
)


def render_config_tab(demo, prediction_state, params, app_toast):
    with gr.Tab("系统设置"):
        with gr.Tabs():
            with gr.Tab("实际产量录入") as ayield_tab:
                gr.Markdown("实际产量录入 placeholder")

            with gr.Tab("果园信息管理") as orchard_mgmt_tab:
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
                    orchard_select = gr.Dropdown(
                        choices=_choices,
                        value=_default_id,
                        **dropdown_cls("选择果园", filterable=False),
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
                        *ORCHARD_DROPDOWNS,
                    ],
                    queue=False,
                )
                save_orchard_btn.click(
                    save_orchard_handler,
                    inputs=[orchard_select, edit_orchard_name, edit_orchard_trees],
                    outputs=[
                        orchard_list_html, orchard_select,
                        edit_orchard_name, edit_orchard_trees, orchard_msg,
                        *ORCHARD_DROPDOWNS,
                    ],
                    queue=False,
                )
                delete_orchard_btn.click(
                    delete_orchard_handler,
                    inputs=[orchard_select],
                    outputs=[
                        orchard_list_html, orchard_select,
                        edit_orchard_name, edit_orchard_trees, orchard_msg,
                        *ORCHARD_DROPDOWNS,
                    ],
                    queue=False,
                )


            with gr.Tab("预测参数配置"):
                with gr.Column(elem_classes=["layout-full", "form-stack"]):
                    with gr.Column(elem_classes=["app-card", "form-stack", "config-panel"]):
                        field_label("平均坐果率")
                        param_rate = gr.Number(value=params["flower_fruit_rate_pct"], **input_cls("field-input"))
                        gr.HTML('<p class="hint-text">常规柑橘参考 2.0 ~ 3.0%</p>')
                        gr.HTML(
                            '<div class="param-desc">'
                            '<div><strong>含义：</strong>用于花期预测，表示每100朵花预计形成多少个成熟果（例如 2.5% 表示每100朵花约形成2.5个果）。</div>'
                            '<div><strong>作用：</strong>影响花期产量预测（花量 → 预计果实数）。</div>'
                            '<div><strong>公式：</strong>预计果实 = 花量 × 坐果率</div>'
                            '</div>'
                        )
                        field_label("单果平均重量")
                        param_weight = gr.Number(value=params["avg_weight_g"], **input_cls("field-input"))
                        gr.HTML('<p class="hint-text">普通柑橘参考 120 ~ 180g</p>')
                        gr.HTML(
                            '<div class="param-desc">'
                            '<div><strong>含义：</strong>平均单果重量，单位为克（g）。</div>'
                            '<div><strong>作用：</strong>影响所有阶段的重量计算，最终将果数转换为重量。</div>'
                            '<div><strong>公式：</strong>产量(kg) = 果实数 × 平均单果重量(g) / 1000</div>'
                            '</div>'
                        )
                        field_label("低产预警阈值")
                        param_risk = gr.Number(value=params["risk_warning_threshold"], **input_cls("field-input"))
                        gr.HTML('<p class="hint-text">低于同期均值该比例自动触发预警</p>')
                        gr.HTML(
                            '<div class="param-desc">'
                            '<div><strong>含义：</strong>用于风险评估，表示当前预测/历史均值的比率阈值（例如 0.8 表示低于80%视为低产）。</div>'
                            '<div><strong>作用：</strong>用于触发低产预警，影响风险提示板块。</div>'
                            '<div><strong>公式：</strong>若 当前产量 / 历史均值 &lt; 阈值，则触发预警</div>'
                            '</div>'
                        )
                        with gr.Row(elem_classes=["btn-full"]):
                            param_save_btn = gr.Button("保存系统参数", variant="primary")
                        param_result = gr.HTML(visible=False)

                    def save_params_with_msg(rate_pct, weight_g, risk_threshold):
                        try:
                            msg = save_system_params_ui(rate_pct, weight_g, risk_threshold)
                            # Return updated result HTML and update the input boxes to the saved values
                            return (
                                gr.update(value=f'<p class="success-text">{msg}</p>', visible=True),
                                gr.update(value=float(rate_pct) if rate_pct is not None and str(rate_pct) != '' else None),
                                gr.update(value=float(weight_g) if weight_g is not None and str(weight_g) != '' else None),
                                gr.update(value=float(risk_threshold) if risk_threshold is not None and str(risk_threshold) != '' else None),
                            )
                        except Exception as e:
                            # Avoid raising to Gradio (500). Show error to user and log traceback.
                            import traceback as _tb
                            _tb.print_exc()
                            return (
                                gr.update(value=f'<p class="fail-text">保存失败：{str(e)}</p>', visible=True),
                                gr.update(), gr.update(), gr.update(),
                            )

                    param_save_btn.click(
                        save_params_with_msg,
                        inputs=[param_rate, param_weight, param_risk],
                        outputs=[param_result, param_rate, param_weight, param_risk],
                        queue=False,
                        show_progress="hidden",
                    )

