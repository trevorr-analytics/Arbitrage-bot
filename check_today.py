import json
import os
from datetime import datetime

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(path, "r", encoding="utf-8") as f:
    cache = json.load(f)

matches_today = []
for sport, data in cache.items():
    for event in data.get("data", []):
        dt_str = event.get("commence_time", "")
        if "2026-08-23" in dt_str:
            matches_today.append(f"[{sport}] {event['home_team']} vs {event['away_team']} @ {dt_str}")

print(f"Found {len(matches_today)} matches today.")
for m in matches_today[:15]:
    print(m)
