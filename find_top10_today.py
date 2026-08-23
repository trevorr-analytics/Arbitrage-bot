import json
import os
import sys
sys.path.insert(0, r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot")

from dixon_coles import DixonColesModel, load_league_data
from odds_api import _parse_odds_data

# Map sports keys to our LEAGUES
SPORT_MAP = {
    "soccer_epl": "EPL",
    "soccer_germany_bundesliga": "Bundesliga",
    "soccer_spain_la_liga": "LaLiga",
    "soccer_italy_serie_a": "SerieA",
    "soccer_france_ligue_one": "Ligue1",
    "soccer_netherlands_eredivisie": "Eredivisie"
}

# Load Models
models = {}
for sport_key, league_name in SPORT_MAP.items():
    try:
        df = load_league_data(league_name)
        m = DixonColesModel()
        m.fit(df)
        models[sport_key] = (league_name, m)
    except Exception as e:
        print(f"Skipping {league_name}: {e}")

# Load Cache
cache_path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_cache.json"
with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

import difflib

def fuzzy_team(name, known_teams):
    for k in known_teams:
        if k.lower() == name.lower(): return k
    matches = difflib.get_close_matches(name, known_teams, n=1, cutoff=0.55)
    if matches:
        return matches[0]
    generic = {"fc", "real", "united", "city", "athletic", "club", "de", "cf", "and", "hove", "albion"}
    name_clean = " ".join([w for w in name.lower().split() if w not in generic])
    if len(name_clean) > 3:
        for k in known_teams:
            k_clean = " ".join([w for w in k.lower().split() if w not in generic])
            if name_clean in k_clean or (len(k_clean)>3 and k_clean in name_clean):
                return k
    return name if not known_teams else None

edges = []

for sport_key, data in cache.items():
    if sport_key not in models:
        continue
        
    league_name, model = models[sport_key]
    fixtures = _parse_odds_data(data.get("data", []))
    
    for fix in fixtures:
        home, away, o_h, o_d, o_a, o_ov, o_un, point_line, commence_time = fix[:9]
        if "2026-08-23" not in commence_time:
            continue
            
        h_match = fuzzy_team(home, model.teams_)
        a_match = fuzzy_team(away, model.teams_)
        
        if not h_match or not a_match:
            continue
            
        pred = model.predict(h_match, a_match)
        
        # Calculate edges
        # Edge = (Offered_Odds * True_Prob) - 1
        markets = {
            "Home Win": (pred["home_win"], o_h),
            "Draw": (pred["draw"], o_d),
            "Away Win": (pred["away_win"], o_a),
            "Over 2.5": (pred["over_2_5"], o_ov),
            "Under 2.5": (pred["under_2_5"], o_un)
        }
        
        for mkt_name, (true_prob, odds) in markets.items():
            if odds <= 1.0: continue
            edge = (odds * true_prob) - 1
            if edge > 0.01: # At least 1% edge
                edges.append({
                    "match": f"{h_match} vs {a_match}",
                    "league": league_name,
                    "time": commence_time.replace('T', ' ')[:16],
                    "market": mkt_name,
                    "offered_odds": odds,
                    "true_prob": true_prob,
                    "fair_odds": 1/true_prob if true_prob > 0 else 0,
                    "edge": edge
                })

# Sort and print Top 10
edges.sort(key=lambda x: x["edge"], reverse=True)

print("\n--- TOP 10 +EV BETS FOR TODAY ---")
for i, e in enumerate(edges[:10]):
    print(f"{i+1}. [{e['league']}] {e['match']} @ {e['time']}")
    print(f"   Market: {e['market']}")
    print(f"   Offered Odds: {e['offered_odds']} (Fair Odds: {e['fair_odds']:.2f})")
    print(f"   Edge: +{e['edge']*100:.2f}% (True Prob: {e['true_prob']*100:.1f}%)")
    print()

