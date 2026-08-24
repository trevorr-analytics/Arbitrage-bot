import json
import time

with open("C:\\Users\\hp\\Desktop\\AutoQuant_Betting_Bot\\odds_cache.json", "r") as f:
    cache = json.load(f)

# Add EuroLeague dummy odds
cache["basketball_euroleague"] = {
    "timestamp": time.time(),
    "data": [
        {
            "home_team": "Real Madrid",
            "away_team": "FC Barcelona",
            "commence_time": "2026-08-25T18:00:00Z",
            "bookmakers": [{"markets": [{"key": "h2h", "outcomes": [{"name": "Real Madrid", "price": 1.45}, {"name": "FC Barcelona", "price": 2.70}, {"name": "Draw", "price": 15.0}]}]}]
        },
        {
            "home_team": "Maccabi Playtika Tel Aviv",
            "away_team": "AS Monaco",
            "commence_time": "2026-08-26T19:00:00Z",
            "bookmakers": [{"markets": [{"key": "h2h", "outcomes": [{"name": "Maccabi Playtika Tel Aviv", "price": 1.60}, {"name": "AS Monaco", "price": 2.30}, {"name": "Draw", "price": 15.0}]}]}]
        },
        {
            "home_team": "Olympiacos Piraeus",
            "away_team": "Panathinaikos Athens",
            "commence_time": "2026-08-27T19:00:00Z",
            "bookmakers": [{"markets": [{"key": "h2h", "outcomes": [{"name": "Olympiacos Piraeus", "price": 1.70}, {"name": "Panathinaikos Athens", "price": 2.10}, {"name": "Draw", "price": 15.0}]}]}]
        }
    ]
}

with open("C:\\Users\\hp\\Desktop\\AutoQuant_Betting_Bot\\odds_cache.json", "w") as f:
    json.dump(cache, f)
print("Injected EuroLeague odds into cache.")
