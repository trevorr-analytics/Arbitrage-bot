import json
import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

all_legs = []
for acca in data:
    for leg in acca.get("legs", []):
        leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
        if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in all_legs):
            all_legs.append(leg)

safe_legs = [leg for leg in all_legs if leg.get('model_prob', 0) >= 0.65 and leg.get('edge', 0) > 0]
safe_legs = sorted(safe_legs, key=lambda x: x.get('model_prob', 0), reverse=True)

print(f"Total safe legs found: {len(safe_legs)}")
for leg in safe_legs:
    print(f"[{leg.get('league')}] {leg.get('home')} vs {leg.get('away')} - {leg.get('market')} (Prob: {leg.get('model_prob', 0)*100:.1f}%)")
