import json

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(path, "r", encoding="utf-8") as f:
    cache = json.load(f)

for event in cache["soccer_france_ligue_one"]["data"]:
    if "Paris Saint Germain" in event["home_team"] or "Paris Saint Germain" in event["away_team"]:
        print(f"home_team: '{event['home_team']}'")
        print(f"away_team: '{event['away_team']}'")
        for b in event['bookmakers']:
            for m in b['markets']:
                if m['key'] == 'h2h':
                    for o in m['outcomes']:
                        print(f"outcome name: '{o['name']}'")
