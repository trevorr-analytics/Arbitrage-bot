import json
path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for acca in data[:2]:
    for leg in acca.get("legs", []):
        print(leg)
