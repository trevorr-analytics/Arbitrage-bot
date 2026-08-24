import json
path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for i, acca in enumerate(data[:5]):
    print(f"Acca {i}: keys: {list(acca.keys())}")
    print(f"  odds: {acca.get('odds')}, edge: {acca.get('edge')}")
