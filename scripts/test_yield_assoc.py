import sys
sys.path.append(r'E:\campus\智能系统\柑橘\citrus-yield-prediction-master\citrus-yield-prediction-fixUI\citrus-yield-prediction-fixUI')
from ui.handlers.yield_entry import submit_actual_yield, parse_prediction_option, get_prediction_options
from data.database import get_db

print('loading db')
db = get_db()
dets = db.get_detections(None, limit=10)
print('detections count:', len(dets))
if not dets:
    print('no detections found')
    sys.exit(0)
first = dets[0]
opt = str(first['id'])
print('using detection id:', opt)
# submit an actual yield associated with this detection
res = submit_actual_yield(opt, '', '2025-10-01', '123.45', '')
print('submit result:', res)
# verify history_yield entries for orchard
orchard_id = first['orchard_id']
hists = db.get_history_yields(orchard_id)
print('history yields count:', len(hists))
for h in hists[:10]:
    print(h)
print('done')

