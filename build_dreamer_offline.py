import json
from datetime import datetime, timezone, timedelta
import dateutil.parser

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\sports_model\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Clear old dreamers
data = [a for a in data if not a.get("is_dreamer")]

unique_legs = {}
now = datetime.now(timezone.utc)
end_of_week = now + timedelta(days=7)

for acca in data:
    for leg in acca.get("legs", []):
        if leg.get('status') == 'PENDING' and leg.get('edge', 0) > 0:
            dt_str = leg.get('date', '')
            try:
                dt = dateutil.parser.isoparse(dt_str) if dt_str else None
                if dt and dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except: 
                dt = None
                
            if dt is not None and now < dt <= end_of_week:
                sig = f"{leg.get('home')}_{leg.get('away')}_{leg.get('market')}"
                if sig not in unique_legs:
                    unique_legs[sig] = leg

all_legs = list(unique_legs.values())
sorted_legs = sorted(all_legs, key=lambda x: x.get("edge", 0), reverse=True)

dreamer_legs = []
current_odds = 1.0

for leg in sorted_legs:
    match_sig = f"{leg.get('home')}_{leg.get('away')}"
    if not any(f"{l.get('home')}_{l.get('away')}" == match_sig for l in dreamer_legs):
        dreamer_legs.append(leg)
        current_odds *= leg.get("odds", 1.0)
        if current_odds >= 100.0:
            break

if current_odds >= 100.0:
    dreamer_acca = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING",
        "combined_odds": current_odds,
        "combined_edge": sum(l.get("edge", 0) for l in dreamer_legs) / len(dreamer_legs) if dreamer_legs else 0,
        "stake": 100.0,
        "is_dreamer": True,
        "legs": dreamer_legs
    }
    data.append(dreamer_acca)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Appended Dreamer Parlay with odds {current_odds:.2f} using {len(dreamer_legs)} legs.")
else:
    print(f"Could only reach odds {current_odds:.2f}, not enough legs for 100.")
