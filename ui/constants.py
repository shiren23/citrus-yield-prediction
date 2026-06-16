"""App-wide constants."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import DATA_DIR

# 支持花期早期估产与成熟期产量校正两种模式
STAGE_UI_OPTIONS = ["花期（早期估产）", "成熟期（产量校正）"]
STAGE_UI_MAP = {
    "花期（早期估产）": "flowering",
    "成熟期（产量校正）": "mature",
}
STAGE_DISPLAY = {
    "flowering": "花期",
    "immature": "幼果期",
    "mature": "成熟期",
    "mixed": "混合期",
    "unknown": "未知",
}
MANUAL_RECORD_OPTION = "无对应预测记录，手动录入"
MEDIA_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"}
MEDIA_FILE_TYPES = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".mp4", ".avi", ".mov", ".mkv", ".wmv"]
MEDIA_PREVIEW_PLACEHOLDER = '<div class="media-preview-placeholder">上传后将在此预览</div>'
SYSTEM_PARAMS_PATH = os.path.join(DATA_DIR, "system_params.json")
DEFAULT_SYSTEM_PARAMS = {
    "flower_fruit_rate_pct": 2.5,
    "avg_weight_g": 150,
    "risk_warning_threshold": 80,
}

HISTORY_TABLE_PLACEHOLDER = (
    '<p class="hint-text" style="padding:12px;border:1px solid #e2e8f0;border-radius:6px">'
    '请设置筛选条件后，点击「查询数据」查看明细</p>'
)
