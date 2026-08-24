import json
from datetime import datetime, timezone

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

now = datetime.now(timezone.utc)
legs = []
for acca in data:
    for leg in acca.get("legs", []):
        legs.append(leg)

safe_legs = [l for l in legs if l.get("model_prob", 0) >= 0.65 and l.get("edge", 0) > 0]
future_safe = []
for l in safe_legs:
    try:
        dt_str = l.get("date")
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) if dt_str.endswith("Z") else datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        if dt >= now:
            future_safe.append(l)
    except:
        pass

for l in future_safe:
    print(f"[{l.get('league')}] {l.get('home')} vs {l.get('away')} @ {l.get('date')} (Prob: {l.get('model_prob')})")
