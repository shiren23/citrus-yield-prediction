"""One-time helper: split app.py into ui/ package. Run from project root."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
UI = ROOT / "ui"

SECTIONS = {
    "constants.py": (59, 82),  # approximate - will use markers instead
}

MARKERS = [
    ("constants", r"^detector: Optional", r"^INPUT_KW"),
    ("components_start", r"^INPUT_KW", r"^GLOBAL_CSS"),
    ("styles", r"^GLOBAL_CSS = ", r"^\"\"\"\s*$", None),  # tricky
]

def extract_between(src: str, start_pat: str, end_pat: str) -> str:
    lines = src.splitlines(keepends=True)
    start_i = end_i = None
    for i, line in enumerate(lines):
        if start_i is None and re.match(start_pat, line):
            start_i = i
        elif start_i is not None and re.match(end_pat, line):
            end_i = i
            break
    if start_i is None:
        raise ValueError(f"start not found: {start_pat}")
    if end_i is None:
        end_i = len(lines)
    return "".join(lines[start_i:end_i])

if __name__ == "__main__":
    src = APP.read_text(encoding="utf-8")
    print("lines", len(src.splitlines()))
