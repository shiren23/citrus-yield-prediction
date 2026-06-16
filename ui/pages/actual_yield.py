"""实际产量录入页。"""
import gradio as gr

from ui.components import dropdown_cls, field_label, input_cls, toast_output, status_html
from ui.handlers.orchard_data import get_orchard_id, get_orchard_list, default_orchard_name, register_orchard_dropdown
from data.database import get_db


def _detection_choices(orchard_name):
    orchard_id = get_orchard_id(orchard_name)
    if orchard_id is None:
        return []
    rows = get_db().get_detections(orchard_id, limit=200)
    choices = []
    for r in rows:
        label = f"{str(r.get('detected_at', ''))[:10]}｜{r.get('stage', '')}｜预测{r.get('predicted_yield', 0)}kg"
        choices.append((label, str(r['id'])))
    return choices


def _refresh_detection_choices(orchard_name):
    choices = _detection_choices(orchard_name)
    return gr.update(choices=choices, value=(choices[0][1] if choices else None))


def _save_actual_yield(orchard_name, detection_id, actual_yield, harvest_date):
    orchard_id = get_orchard_id(orchard_name)
    if orchard_id is None:
        msg = "请先选择果园"
        return toast_output(msg, False), status_html(msg, False)
    if not detection_id:
        msg = "请选择对应预测记录"
        return toast_output(msg, False), status_html(msg, False)
    if actual_yield is None or str(actual_yield).strip() == "":
        msg = "请输入实际产量"
        return toast_output(msg, False), status_html(msg, False)
    det = get_db().get_detection(int(detection_id))
    if not det:
        msg = "预测记录不存在"
        return toast_output(msg, False), status_html(msg, False)
    date = str(harvest_date or "")[:10]
    year = int(date[:4]) if len(date) >= 4 and date[:4].isdigit() else 0
    if not year:
        from datetime import datetime
        year = datetime.now().year
    tree_count = (get_db().get_orchard(orchard_id) or {}).get("tree_count") or 1
    per_tree = float(actual_yield) / max(1, int(tree_count))
    get_db().add_history_yield(
        orchard_id=orchard_id,
        year=year,
        season=str(det.get("stage", "")),
        actual_yield=float(actual_yield),
        detection_id=int(detection_id),
        harvest_date=date,
        per_tree_yield=per_tree,
    )
    msg = "实际产量已录入"
    return toast_output(msg, True), status_html(msg, True)


def render_actual_yield_tab(app_toast):
    with gr.Tab("实际产量录入") as actual_tab:
        with gr.Column(elem_classes=["app-card", "form-stack"]):
            gr.HTML('<div class="card-title">实际产量录入</div>')
            gr.HTML('<p class="hint-text">录入收获后的实际产量，并关联一条预测记录；历史数据会自动显示实际产量和误差率。</p>')
            orchard = register_orchard_dropdown(gr.Dropdown(
                choices=get_orchard_list(),
                value=default_orchard_name(),
                **dropdown_cls("果园", filterable=False),
            ))
            detection = gr.Dropdown(
                choices=_detection_choices(default_orchard_name()),
                value=None,
                **dropdown_cls("预测记录", filterable=False),
            )
            field_label("实际总产量（kg）")
            actual = gr.Number(value=None, minimum=0, step=0.01, **input_cls("field-input"))
            field_label("收获日期（YYYY-MM-DD）")
            harvest_date = gr.Textbox(value="", placeholder="例如 2026-06-16", **input_cls("field-input"))
            save_btn = gr.Button("保存实际产量", variant="primary")
            save_status = gr.HTML(value="", visible=True)

        orchard.change(_refresh_detection_choices, inputs=[orchard], outputs=[detection], queue=False, show_progress="hidden")
        save_btn.click(_save_actual_yield, inputs=[orchard, detection, actual, harvest_date], outputs=[app_toast, save_status], queue=False, show_progress="hidden")

        # 避免在标签切换时强制刷新果园下拉，防止某些 Gradio 版本在
        # 连续切换「历史数据 -> 产量预测 -> 实际产量录入」时出现卡顿。

