import json
from datetime import datetime, timedelta, timezone
import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\sports_model\acca_tracker.json"
with open(path, "r") as f:
    data = json.load(f)

now = datetime.now(timezone.utc)
end_of_week = now + timedelta(days=7)

def parse_date(date_str):
    if not date_str:
        return None
    try:
        if date_str.endswith("Z"):
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None

valid_accas = []
for acca in reversed(data):
    has_past_leg = False
    out_of_week = False
    for leg in acca.get("legs", []):
        dt = parse_date(leg.get("date", ""))
        
        # FIX: If leg has no date, fall back to the acca's creation timestamp
        if dt is None:
            dt = parse_date(acca.get("timestamp", ""))
            
        if dt is not None:
            if dt < now:
                has_past_leg = True
            elif dt > end_of_week:
                out_of_week = True
    
    if not has_past_leg and not out_of_week:
        valid_accas.append(acca)

psv_count = 0
for a in valid_accas:
    for leg in a.get('legs', []):
        if leg.get('home') == 'PSV Eindhoven':
            psv_count += 1
print(f"PSV count with fix: {psv_count}")
