import csv
import io
import json
import os
import tempfile
import traceback
from datetime import datetime
from typing import List, Optional, Tuple

from core.config import RISK_THRESHOLDS, get_fruit_count
from core.count_scaler import scale_counts_to_tree
from core.risk_alert import RiskAlerter
from core.stage_classifier import StageClassifier
from core.yield_estimator import YieldEstimator
from data.database import get_db

from ui.charts import MATPLOTLIB_OK, MaxNLocator, mdates, plt, setup_matplotlib_chinese
from ui.components import status_html, toast_output
from ui.constants import (
    DEFAULT_SYSTEM_PARAMS,
    MANUAL_RECORD_OPTION,
    MEDIA_PREVIEW_PLACEHOLDER,
    MEDIA_VIDEO_EXTENSIONS,
    STAGE_DISPLAY,
    STAGE_UI_MAP,
    SYSTEM_PARAMS_PATH,
)
from ui.detector_state import set_detector_model
from ui.handlers.orchard_data import (
    apply_system_params_to_estimator,
    get_orchard_id,
    get_orchard_variety,
    load_system_params,
    format_risk_label,
)

try:
    import gradio as gr
except ImportError:
    gr = None

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
    if isinstance(media_file, list):
        if not media_file:
            return None
        media_file = media_file[0]
    if hasattr(media_file, "path"):
        path = str(media_file.path)
        return path if path and os.path.isfile(path) else None
    if isinstance(media_file, str):
        path = media_file.strip()
        return path if path and os.path.isfile(path) else None
    if isinstance(media_file, dict):
        path = media_file.get("path") or media_file.get("name")
        return path if path and os.path.isfile(str(path)) else None
    path = getattr(media_file, "name", None) or getattr(media_file, "path", None)
    if path and os.path.isfile(str(path)):
        return str(path)
    return None


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
    """仅重置预览区（不写回 File，避免与 Gradio 内部状态冲突）。"""
    return clear_preview_outputs()


def clear_media_all():
    """清空上传组件、路径 state 与预览。"""
    return (
        None,
        None,
        *clear_preview_outputs(),
    )


def sync_media_upload(media_file):
    """上传后只更新 state 与预览，不把值写回 File（否则清除易失效）。"""
    path = resolve_media_path(media_file)
    if not path:
        return (None, *clear_preview_outputs())
    return (path, *preview_media(media_file))


def on_media_cleared():
    """用户点击 File 自带删除钮时，同步 state 与预览。"""
    return (None, *clear_preview_outputs())


def show_predict_result_panel():
    """点击开始预测后立即展示结果区（用于显示加载状态）。"""
    return gr.update(visible=True)


def _prediction_fail(toast_msg: str, ok: bool = False):
    """预测失败时隐藏结果区，避免空白占位界面。"""
    return (
        gr.update(visible=False),
        None, "", "", "", "", "",
        gr.update(visible=False, value=""),
        "",
        toast_output(toast_msg, ok),
    )


def run_prediction(media_path, orchard_name, tree_count, stage_choice, canopy_ratio_pct, model_name):
    keep_panel = gr.update(visible=True)
    path = media_path if media_path and os.path.isfile(str(media_path)) else None
    if not path or not os.path.isfile(path):
        return _prediction_fail("请先上传图片或视频", False)

    dt = set_detector_model(model_name)
    if dt is None:
        return _prediction_fail("模型加载失败，请检查依赖安装", False)

    try:
        params = load_system_params()
        variety = get_orchard_variety(orchard_name)

        video_meta = None
        if is_video_path(path):
            video_result = dt.detect_video(path)
            if not video_result.get("success"):
                return _prediction_fail(
                    f"视频处理失败: {video_result.get('error', '未知错误')}",
                    False,
                )
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
        raw_counts = scale_info["raw"]
        used_canopy_ratio = scale_info.get("canopy_ratio", ratio)

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

        # 构造逐步计算过程展示（展示输入、使用参数、中间步骤与最终结果）
        factors = yield_result.get("factors", {}) or {}
        try:
            if stage == "flowering":
                raw_flower = int(raw_counts.get("flower", 0))
                flower_cnt = int(factors.get("flower_count", flower_total))
                rate = float(factors.get("flower_fruit_rate", 0))
                expected_fruits = round(flower_cnt * rate, 2)
                avg_w_kg = float(factors.get("avg_weight_kg", 0))
                avg_w_g = int(round(avg_w_kg * 1000))
                calc_html = f"""
                <div class="calc-card">
                  <div class="info-row"><strong>图片检测到花朵：</strong>{raw_flower} 朵</div>
                  <div class="info-row"><strong>树冠可见占比：</strong>{used_canopy_ratio*100:.0f}%</div>
                  <div class="info-row"><strong>整树估算花朵：</strong>{flower_cnt} 朵</div>
                  <div class="info-row"><strong>使用坐果率：</strong>{rate:.3f} ({rate*100:.2f}%)</div>
                  <div class="info-row"><strong>预计果实数：</strong>{flower_cnt} × {rate} = {expected_fruits} 个</div>
                  <div class="info-row"><strong>平均单果重量：</strong>{avg_w_g} g</div>
                  <div class="info-row"><strong>单棵产量：</strong>{per_tree} kg/棵</div>
                  <div class="info-row"><strong>最终预测产量：</strong>{total_kg} kg（{int(tree_count or 1)} 棵）</div>
                </div>
                """
            elif stage == "immature":
                raw_imm = int(raw_counts.get("immature_fruit", 0))
                imm_cnt = int(factors.get("immature_count", counts.get("immature_fruit", 0)))
                surv = float(factors.get("survival_rate", 0))
                expected_fruits = round(imm_cnt * surv, 2)
                avg_w_kg = float(factors.get("avg_weight_kg", 0))
                avg_w_g = int(round(avg_w_kg * 1000))
                calc_html = f"""
                <div class="calc-card">
                  <div class="info-row"><strong>图片检测到幼果：</strong>{raw_imm} 个</div>
                  <div class="info-row"><strong>树冠可见占比：</strong>{used_canopy_ratio*100:.0f}%</div>
                  <div class="info-row"><strong>整树估算幼果：</strong>{imm_cnt} 个</div>
                  <div class="info-row"><strong>使用成活率：</strong>{surv:.3f} ({surv*100:.2f}%)</div>
                  <div class="info-row"><strong>预计成活果数：</strong>{imm_cnt} × {surv} = {expected_fruits} 个</div>
                  <div class="info-row"><strong>平均单果重量：</strong>{avg_w_g} g</div>
                  <div class="info-row"><strong>最终预测产量：</strong>{total_kg} kg（{int(tree_count or 1)} 棵）</div>
                </div>
                """
            elif stage == "mature":
                raw_fruit = int(get_fruit_count(raw_counts))
                fruit_cnt = int(factors.get("fruit_count", fruit_total))
                avg_w_kg = float(factors.get("avg_weight_kg", 0))
                drop = float(factors.get("mature_drop_rate", 0))
                harvested = round(fruit_cnt * (1 - drop), 2)
                avg_w_g = int(round(avg_w_kg * 1000))
                calc_html = f"""
                <div class="calc-card">
                  <div class="info-row"><strong>图片检测到果实：</strong>{raw_fruit} 个</div>
                  <div class="info-row"><strong>树冠可见占比：</strong>{used_canopy_ratio*100:.0f}%</div>
                  <div class="info-row"><strong>整树估算果实：</strong>{fruit_cnt} 个</div>
                  <div class="info-row"><strong>预计留果数：</strong>{fruit_cnt} × (1 - {drop}) = {harvested} 个</div>
                  <div class="info-row"><strong>平均单果重量：</strong>{avg_w_g} g</div>
                  <div class="info-row"><strong>最终预测产量：</strong>{total_kg} kg（{int(tree_count or 1)} 棵）</div>
                </div>
                """
            elif stage == "mixed":
                # 混合期展示各期贡献
                fc = factors.get("flower_contrib")
                ic = factors.get("immature_contrib")
                rc = factors.get("fruit_contrib")
                weights = factors.get("weights", {})
                calc_html = "<div class=\"calc-card\"><div class=\"info-row\"><strong>混合期分期贡献（kg）：</strong></div>"
                if fc is not None:
                    calc_html += f"<div class=\"info-row\">花期贡献：{fc} kg（权重 {weights.get('flower', '')}）</div>"
                if ic is not None:
                    calc_html += f"<div class=\"info-row\">幼果期贡献：{ic} kg（权重 {weights.get('immature', '')}）</div>"
                if rc is not None:
                    calc_html += f"<div class=\"info-row\">果实期贡献：{rc} kg（权重 {weights.get('mature', '')}）</div>"
                calc_html += f"<div class=\"info-row\"><strong>最终预测产量：</strong>{total_kg} kg（{int(tree_count or 1)} 棵）</div></div>"
            else:
                calc_html = f"<div class=\"calc-card\"><div class=\"info-row\">无法生成计算过程：{yield_result.get('formula')}</div></div>"
        except Exception:
            # 兜底，避免因格式问题导致整个预测失败
            calc_html = f"<div class=\"calc-card\"><div class=\"info-row\">无法生成计算过程</div></div>"

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
            "raw_counts": raw_counts,
            "canopy_ratio": used_canopy_ratio,
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
            keep_panel,
            annotated_img,
            stats_text,
            info_html,
            yield_html,
            formula_html,
            calc_html,
            range_html,
            gr.update(visible=show_risk, value=risk_html),
            state,
            toast_output("预测完成，可点击「保存记录」写入历史"),
        )
    except Exception as e:
        traceback.print_exc()
        return _prediction_fail(f"处理出错: {str(e)}", False)


def export_current_record(state_json: str):
    if not state_json:
        # 无可导出的预测状态
        if gr is not None:
            raise gr.Error("暂无预测记录可导出")
        return None
    data = json.loads(state_json)
    db = get_db()

    # 优先使用已保存记录的数据（若存在 record_id），否则使用当前 state 中的 counts
    if data.get("record_id"):
        rec = db.get_detection(int(data.get("record_id")))
    else:
        rec = None

    if rec:
        date_str = str(rec.get("detected_at", ""))[:10]
        stage_label = STAGE_DISPLAY.get(rec.get("stage", ""), rec.get("stage", ""))
        flowers = rec.get("flower_count", 0)
        fruit = get_fruit_count({
            "fruit": 0,
            "mature_fruit": rec.get("mature_count", 0),
            "immature_fruit": rec.get("immature_count", 0),
        }) + rec.get("immature_count", 0)
        predicted = rec.get("predicted_yield", 0)
        risk = format_risk_label(rec.get("risk_level", "normal"))
    else:
        # 从 state 中提取
        date_str = datetime.now().strftime("%Y-%m-%d")
        stage_label = data.get("stage_name", data.get("stage", ""))
        counts = data.get("counts", {}) or {}
        flowers = counts.get("flower", 0)
        fruit = get_fruit_count({
            "fruit": 0,
            "mature_fruit": counts.get("mature_fruit", 0),
            "immature_fruit": counts.get("immature_fruit", 0),
        }) + counts.get("immature_fruit", 0)
        predicted = data.get("predicted_yield", data.get("yield_kg", 0))
        risk = format_risk_label(data.get("risk_level", "normal"))

    content = io.StringIO()
    writer = csv.writer(content)
    # 使用与历史批量导出相同的表头
    writer.writerow(["日期", "生长阶段", "花朵数", "果实数", "预测产量(kg)", "风险"])
    writer.writerow([
        date_str,
        stage_label,
        flowers,
        fruit,
        predicted,
        risk,
    ])
    suffix = data.get("record_id", "export")
    tmp = os.path.join(tempfile.gettempdir(), f"prediction_{suffix}.csv")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(content.getvalue())
    return tmp


def save_record_core(state_json: str):
    """保存记录，返回 state 与 toast 元数据（toast 由 .then 写入，与预测完成同机制）。"""
    if not state_json:
        return state_json, ("暂无预测记录可保存", False)
    data = json.loads(state_json)
    if data.get("saved"):
        return state_json, ("该记录已保存过", True)
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
    return json.dumps(data, ensure_ascii=False), ("记录已保存", True)


def save_record_full(state_json: str):
    """保存并返回 state、居中 toast、按钮旁状态（与预测完成同一套输出方式）。"""
    state, meta = save_record_core(state_json)
    msg, ok = meta if meta else ("操作完成", True)
    if gr is not None:
        if ok:
            gr.Info(str(msg), duration=2, title="")
        else:
            gr.Warning(str(msg), duration=3, title="")
    return state, toast_output(str(msg), bool(ok)), status_html(str(msg), bool(ok))


def on_model_change(model_name: str):
    """切换检测模型，返回状态提示。"""
    try:
        dt = set_detector_model(model_name)
        if dt is None:
            return status_html(f"模型加载失败：{model_name}", False)
        return status_html(f"已切换模型：{model_name}", True)
    except Exception as e:
        return status_html(f"切换模型失败：{e}", False)


def toast_from_meta(meta):
    if not meta:
        return toast_output("操作完成", True)
    msg, ok = meta
    return toast_output(str(msg), bool(ok))


def save_record_confirm(state_json: str):
    """兼容旧调用：一步返回 state + toast。"""
    state, toast, _status = save_record_full(state_json)
    return state, toast

