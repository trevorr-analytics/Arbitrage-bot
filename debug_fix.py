import json
path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(path, "r", encoding="utf-8") as f:
    cache = json.load(f)

for event in cache["soccer_france_ligue_one"]["data"]:
    if "Paris Saint Germain" in event["home_team"] or "Paris Saint Germain" in event["away_team"]:
        print("Home:", event["home_team"], "Away:", event["away_team"])
