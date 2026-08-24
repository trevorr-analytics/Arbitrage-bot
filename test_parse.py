import json
from datetime import datetime, timezone

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for acca in data:
    for leg in acca.get("legs", []):
        date_str = leg.get("date")
        print(f"date_str: {repr(date_str)}")
        try:
            if date_str.endswith("Z"):
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            else:
                dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            print("  parsed OK:", dt)
        except Exception as e:
            print("  FAIL:", e)
        break
    break
