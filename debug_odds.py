import json
path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(path, "r", encoding="utf-8") as f:
    cache = json.load(f)

for sport, data in cache.items():
    for event in data.get("data", []):
        if "Real Madrid" in event['home_team'] or "Real Madrid" in event['away_team']:
            print(f"Match: {event['home_team']} vs {event['away_team']}")
            for bookie in event.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    if market['key'] == 'h2h':
                        print("H2H Market Outcomes:", market['outcomes'])
        if "Paris Saint Germain" in event['home_team'] or "Paris Saint Germain" in event['away_team']:
            print(f"Match: {event['home_team']} vs {event['away_team']}")
            for bookie in event.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    if market['key'] == 'h2h':
                        print("H2H Market Outcomes:", market['outcomes'])
