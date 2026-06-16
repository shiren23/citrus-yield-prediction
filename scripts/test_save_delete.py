import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.handlers.predict import save_record_core, toast_from_meta
from ui.handlers.history import handle_table_delete, get_filtered_detections
from ui.handlers.orchard_data import default_orchard_name

state = json.dumps({
    "saved": False,
    "orchard_id": 1,
    "counts": {"flower": 1, "immature_fruit": 0, "mature_fruit": 0, "total": 1},
    "stage": "flowering",
    "predicted_yield": 10.0,
    "confidence": 0.8,
    "risk_level": "normal",
    "risk_ratio": 1.0,
    "variety": "test",
})
s, meta = save_record_core(state)
t = toast_from_meta(meta)
print("save meta", meta)
print("toast type", type(t), t)

orchard = default_orchard_name()
recs = get_filtered_detections(orchard, "全部阶段", "全部")
print("records before", len(recs))
if recs:
    rid = str(recs[0]["id"])
    out = handle_table_delete(rid, orchard, "全部阶段", "全部")
    print("delete out count", len(out))
    recs2 = get_filtered_detections(orchard, "全部阶段", "全部")
    print("records after", len(recs2))
