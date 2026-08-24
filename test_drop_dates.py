import json
from datetime import datetime, timezone, timedelta

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

now = datetime.now(timezone.utc)
end_of_week = now + timedelta(days=7)

def parse_date(date_str):
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        if date_str.endswith("Z"):
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

valid_accas = []
raw_all_legs = []

for acca in reversed(data):
    for leg in acca.get("legs", []):
        dt = parse_date(leg.get("date", ""))
        if now <= dt <= end_of_week:
            leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
            if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in raw_all_legs):
                raw_all_legs.append(leg)
                
    has_past_leg = False
    out_of_week = False
    for leg in acca.get("legs", []):
        dt = parse_date(leg.get("date", ""))
        if dt < now:
            has_past_leg = True
        elif dt > end_of_week:
            out_of_week = True
    
    if not has_past_leg and not out_of_week:
        valid_accas.append(acca)
        
for l in raw_all_legs:
    dt = parse_date(l.get("date"))
    print((dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT"))
