import json
import numpy as np

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(path, "r", encoding="utf-8") as f:
    cache = json.load(f)

for event in cache["soccer_spain_la_liga"]["data"]:
    if "Real Madrid" in event["home_team"] or "Real Madrid" in event["away_team"]:
        home = event["home_team"]
        away = event["away_team"]
        home_prices = []
        away_prices = []
        for b in event['bookmakers']:
            for m in b['markets']:
                if m['key'] == 'h2h':
                    for o in m['outcomes']:
                        if o['name'] == home:
                            home_prices.append(o['price'])
                        elif o['name'] == away:
                            away_prices.append(o['price'])
        
        print(f"Match: {home} vs {away}")
        print(f"Home Prices: {home_prices} (Median: {np.median(home_prices)})")
        print(f"Away Prices: {away_prices} (Median: {np.median(away_prices)})")
