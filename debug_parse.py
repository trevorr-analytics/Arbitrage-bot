import json
import sys
sys.path.insert(0, r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot")
from odds_api import _parse_odds_data

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(path, "r", encoding="utf-8") as f:
    cache = json.load(f)

for fix in _parse_odds_data(cache["soccer_france_ligue_one"]["data"]):
    if "Paris Saint Germain" in fix[1] or "Paris Saint Germain" in fix[0]:
        print(f"Home: {fix[0]}, Away: {fix[1]}")
        print(f"o_h: {fix[2]}, o_d: {fix[3]}, o_a: {fix[4]}")
