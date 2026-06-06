# -*- coding: utf-8 -*-
"""Split monolithic app.py into ui/ package."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
UI = ROOT / "ui"


def sl(lines, a, b):
    return "".join(lines[a - 1 : b])


def main():
    lines = APP.read_text(encoding="utf-8").splitlines(keepends=True)
    for d in ("handlers", "pages"):
        (UI / d).mkdir(parents=True, exist_ok=True)

    (UI / "__init__.py").write_text(
        'from ui.factory import create_ui, launch_app\n__all__ = ["create_ui", "launch_app"]\n',
        encoding="utf-8",
    )

    (UI / "constants.py").write_text(
        '"""App-wide constants."""\nimport os\nimport sys\nfrom typing import Optional\n\n'
        "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\n"
        + sl(lines, 59, 90)
        + "\n"
        + sl(lines, 1560, 1563),
        encoding="utf-8",
    )

    (UI / "styles.py").write_text(
        '"""Global CSS."""\n\nGLOBAL_CSS = """\n' + sl(lines, 169, 970) + '"""\n',
        encoding="utf-8",
    )

    (UI / "client_js.py").write_text(
        '"""Client JS."""\n\nAPP_JS = """\n' + sl(lines, 1566, 1641) + '"""\n',
        encoding="utf-8",
    )

    charts = sl(lines, 39, 57).replace("    def setup_matplotlib_chinese", "def setup_matplotlib_chinese")
    (UI / "charts.py").write_text('"""Matplotlib."""\n' + charts, encoding="utf-8")

    (UI / "detector_state.py").write_text(
        '''"""Detector singleton."""
from typing import Optional
from core.detector import CitrusDetector, reset_detector

detector: Optional[CitrusDetector] = None


def ensure_detector():
    global detector
    if detector is None:
        try:
            detector = reset_detector(device="cpu")
        except Exception as e:
            print(f"检测器初始化失败: {e}")
            return None
    return detector
''',
        encoding="utf-8",
    )

    (UI / "components.py").write_text(
        '"""UI component helpers."""\n'
        "try:\n    import gradio as gr\nexcept ImportError:\n    gr = None\n\n"
        "from ui.styles import GLOBAL_CSS  # noqa: F401 - re-export for factory\n\n"
        + sl(lines, 87, 165),
        encoding="utf-8",
    )

    handler_imports = '''"""Handler package."""
from ui.handlers.orchard_data import *
from ui.handlers.yield_entry import *
from ui.handlers.predict import *
from ui.handlers.history import *
from ui.handlers.orchard_admin import *
'''

    (UI / "handlers" / "__init__.py").write_text(handler_imports, encoding="utf-8")

    hdr = '''import csv
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
from ui.components import toast_payload
from ui.constants import (
    DEFAULT_SYSTEM_PARAMS,
    MANUAL_RECORD_OPTION,
    MEDIA_PREVIEW_PLACEHOLDER,
    MEDIA_VIDEO_EXTENSIONS,
    STAGE_DISPLAY,
    STAGE_UI_MAP,
    SYSTEM_PARAMS_PATH,
)
from ui.detector_state import ensure_detector

try:
    import gradio as gr
except ImportError:
    gr = None

'''

    (UI / "handlers" / "orchard_data.py").write_text(
        hdr + sl(lines, 983, 1042),
        encoding="utf-8",
    )
    (UI / "handlers" / "yield_entry.py").write_text(
        hdr
        + sl(lines, 1045, 1130)
        + sl(lines, 1846, 1899),
        encoding="utf-8",
    )
    (UI / "handlers" / "predict.py").write_text(
        hdr + sl(lines, 1132, 1420),
        encoding="utf-8",
    )
    (UI / "handlers" / "history.py").write_text(
        hdr + sl(lines, 1422, 1756),
        encoding="utf-8",
    )
    (UI / "handlers" / "orchard_admin.py").write_text(
        hdr + sl(lines, 1758, 1844) + sl(lines, 1901, 1908),
        encoding="utf-8",
    )

    # create_ui -> factory + pages (extract tab bodies manually in factory for now: import full create_ui from legacy)
    create_ui_body = sl(lines, 1911, 2353)
    create_ui_body = create_ui_body.replace("def create_ui():", "def create_ui():", 1)
    factory = '''"""Assemble Gradio application."""
import os

from data.database import get_db

try:
    import gradio as gr
except ImportError:
    gr = None

from ui.client_js import APP_JS
from ui.components import GLOBAL_CSS, build_theme, field_label, input_cls, dropdown_cls, record_select_cls, toast_payload
from ui.constants import (
    HISTORY_TABLE_PLACEHOLDER,
    MANUAL_RECORD_OPTION,
    MEDIA_FILE_TYPES,
    MEDIA_PREVIEW_PLACEHOLDER,
    STAGE_UI_OPTIONS,
)
from ui.handlers import *


''' + create_ui_body

    # Replace inline tab bodies with page renders - do simpler: keep monolithic create_ui in factory first
    (UI / "factory.py").write_text(factory, encoding="utf-8")

    (UI / "pages" / "__init__.py").write_text(
        '"""Page modules (extract tab layouts here incrementally)."""\n',
        encoding="utf-8",
    )

    new_app = '''"""
柑橘产量预测系统 - 入口
界面与业务逻辑见 ui/ 包。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.factory import create_ui, launch_app


def main():
    launch_app()


if __name__ == "__main__":
    main()
'''
    # Add launch_app to factory
    launch = '''

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
'''
    factory_path = UI / "factory.py"
    text = factory_path.read_text(encoding="utf-8")
    if "def launch_app" not in text:
        factory_path.write_text(text + launch, encoding="utf-8")

    # Backup and replace app.py
    backup = ROOT / "app_legacy.py"
    if not backup.exists():
        backup.write_text(APP.read_text(encoding="utf-8"), encoding="utf-8")
    APP.write_text(new_app, encoding="utf-8")
    print("Done. app_legacy.py backup, app.py is thin entry, ui/ created.")


if __name__ == "__main__":
    main()
