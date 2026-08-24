import json
import numpy as np

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(path, "r", encoding="utf-8") as f:
    cache = json.load(f)

for event in cache["soccer_france_ligue_one"]["data"]:
    if "Paris Saint Germain" in event["home_team"] or "Paris Saint Germain" in event["away_team"]:
        psg_prices = []
        rennes_prices = []
        for b in event['bookmakers']:
            for m in b['markets']:
                if m['key'] == 'h2h':
                    for o in m['outcomes']:
                        if o['name'] == 'Paris Saint Germain':
                            psg_prices.append(o['price'])
                        elif o['name'] == 'Rennes':
                            rennes_prices.append(o['price'])
        
        print(f"PSG Prices: {psg_prices}")
        print(f"PSG Median: {np.median(psg_prices)}")
        print(f"Rennes Median: {np.median(rennes_prices)}")
