import json
path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

legs = []
for acca in data:
    for leg in acca.get("legs", []):
        legs.append(leg)

high_prob = [l for l in legs if l.get("model_prob", 0) > 0.65]
print(f"Total legs in acca_tracker: {len(legs)}")
print(f"High prob (>65%) legs: {len(high_prob)}")

for l in high_prob:
    print(f"[{l.get('league')}] {l.get('home')} vs {l.get('away')} | {l.get('market')} | Edge: {l.get('edge')}")
