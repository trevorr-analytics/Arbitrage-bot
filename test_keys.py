import json
path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\acca_tracker.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

if data and len(data) > 0 and len(data[0].get("legs", [])) > 0:
    print(data[0]["legs"][0].keys())
