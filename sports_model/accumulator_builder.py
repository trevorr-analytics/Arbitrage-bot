import os
import sys
import math
import itertools
import pandas as pd
from typing import List, Dict

sys.path.insert(0, os.path.dirname(__file__))
from dixon_coles import DixonColesModel, load_league_data
from odds_api import fetch_live_odds
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.devig import shin_devig

from basketball_model import BasketballModel
from telegram_notifier import send_telegram_message

BANKROLL_KES = 5000.0
MIN_SINGLE_EDGE = 0.01  
KELLY_FRACTION = 0.125  
MAX_BET_CAP = 0.01      
TARGET_MIN_ODDS = 1.5
TARGET_MAX_ODDS = 2.05

LEAGUES = ["EPL", "Bundesliga", "LaLiga", "SerieA", "Ligue1", "Eredivisie", "NBA", "EuroLeague", "NCAAB", "WNBA"]

def safe_devig(odds_list):
    if any(o <= 1.0 for o in odds_list):
        return [0.0] * len(odds_list)
    try:
        return shin_devig(odds_list)
    except Exception:
        return [0.0] * len(odds_list)

import difflib

def fuzzy_team(name: str, known: list) -> str:
    for k in known:
        if k.lower() == name.lower(): return k
    matches = difflib.get_close_matches(name, known, n=1, cutoff=0.55)
    if matches:
        return matches[0]
    generic = {"fc", "real", "united", "city", "athletic", "club", "de", "cf", "and", "hove", "albion"}
    name_clean = " ".join([w for w in name.lower().split() if w not in generic])
    if len(name_clean) > 3:
        for k in known:
            k_clean = " ".join([w for w in k.lower().split() if w not in generic])
            if name_clean in k_clean or (len(k_clean)>3 and k_clean in name_clean):
                return k
    return name if not known else None

def get_all_ev_legs() -> List[Dict]:
    from weather_api import get_league_weather
    
    ev_legs = []
    for league in LEAGUES:
        # Load weather conditions for the league region
        weather = get_league_weather(league)
        is_extreme_weather = weather.get("is_extreme", False)
        if is_extreme_weather:
            print(f"[{league}] Extreme weather detected (Wind: {weather['wind_speed_kmh']}km/h, Rain: {weather['precipitation_mm']}mm). Applying Under total bump.")
            
        # Load Data & Model based on sport
        if league in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            model = BasketballModel()
            if league == "EuroLeague" and os.path.exists("basketball_data/euroleague_2023_boxscore.csv"):
                model.fit("basketball_data/euroleague_2023_boxscore.csv", league_name=league)
            else:
                model.fit() # Stub fit for others
            known = model.known_teams()

        else:
            try:
                data = load_league_data(league)
                cutoff = data["Date"].max() - pd.Timedelta(days=3 * 365)
                data = data[data["Date"] >= cutoff]
            except Exception:
                continue
            
            model = DixonColesModel(half_life_days=90.0)
            model.fit(data, league_name=league)
            known = model.known_teams()
        
        # Fetch Live Odds
        fixtures = fetch_live_odds(league)
        for fix in fixtures:
            # Unpack handles dynamic lengths (soccer vs basketball)
            home, away, o_h, o_d, o_a, o_ov, o_un, point_line, commence_time = fix[:9]
            h_match = fuzzy_team(home, known)
            a_match = fuzzy_team(away, known)
            if not (h_match and a_match): continue
            
            if league in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
                pred = model.predict(h_match, a_match, over_under_line=point_line if point_line > 0 else 225.5, league=league)
            else:
                pred = model.predict(h_match, a_match)
                # Map soccer outputs to uniform keys
                pred["over_total"] = pred["over_2_5"]
                pred["under_total"] = pred["under_2_5"]
                
                # Apply Weather Metric Adjustment
                if is_extreme_weather:
                    pred["under_total"] = min(0.99, pred["under_total"] + 0.03)
                    pred["over_total"] = max(0.01, pred["over_total"] - 0.03)
            
            # Devig
            if league in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
                # NBA moneylines are usually 2-way
                dv_h, dv_a = safe_devig([o_h, o_a])[:2]
                dv_d = 0.0
            else:
                dv_h, dv_d, dv_a = safe_devig([o_h, o_d, o_a])
                
            dv_ov, dv_un = safe_devig([o_ov, o_un])
            
            match_id = f"{league}_{home}_{away}"
            
            mkt_str = f"Over {point_line}" if league in ["NBA", "EuroLeague", "NCAAB", "WNBA"] and point_line > 0 else "Over 2.5"
            umkt_str = f"Under {point_line}" if league in ["NBA", "EuroLeague", "NCAAB", "WNBA"] and point_line > 0 else "Under 2.5"
            
            markets = [
                ("Home Win", o_h, dv_h, pred["home_win"]),
                ("Draw", o_d, dv_d, pred.get("draw", 0.0)),
                ("Away Win", o_a, dv_a, pred["away_win"]),
                (mkt_str, o_ov, dv_ov, pred["over_total"]),
                (umkt_str, o_un, dv_un, pred["under_total"])
            ]
            
            for mkt_name, odds, dv_prob, mod_prob in markets:
                if odds > 1.0 and dv_prob > 0:
                    edge = mod_prob - dv_prob
                    if edge >= MIN_SINGLE_EDGE:
                        ev_legs.append({
                            "match_id": match_id,
                            "league": league,
                            "date": commence_time,
                            "home": home,
                            "away": away,
                            "market": mkt_name,
                            "odds": odds,
                            "devig_prob": dv_prob,
                            "model_prob": mod_prob,
                            "edge": edge
                        })
    return ev_legs

def build_accumulators(ev_legs: List[Dict], max_odds: float = 25.0):
    valid_accas = []
    search_count = 0
    
    # 2-leg and 3-leg combinations
    for r in [2, 3]:
        for combo in itertools.combinations(ev_legs, r):
            search_count += 1
            
            # 1. Strict Correlation Check: Reject if multiple legs share the same match.
            # We assume matches across different games are independent.
            combo_matches = set()
            valid = True
            for leg in combo:
                match_id = f"{leg['league']}_{leg['home']}_{leg['away']}"
                if match_id in combo_matches:
                    valid = False
                    break
                combo_matches.add(match_id)
                
            if not valid:
                continue
                
            combined_odds = math.prod(leg["odds"] for leg in combo)
            
            # 2. Target Range Check
            if TARGET_MIN_ODDS <= combined_odds <= max_odds:
                combined_devig = math.prod(leg["devig_prob"] for leg in combo)
                combined_model = math.prod(leg["model_prob"] for leg in combo)
                
                combined_implied = 1.0 / combined_odds
                combined_edge = combined_model - combined_devig
                effective_vig = combined_implied - combined_devig
                
                # 3. Combined Edge Check: Must maintain a positive combined edge
                if combined_edge > 0:
                    # Staking: Eighth-Kelly, bounded
                    b = combined_odds - 1
                    p = combined_model
                    q = 1 - p
                    k_fraction = (p * b - q) / b if (p * b - q) > 0 else 0
                    stake = BANKROLL_KES * k_fraction * KELLY_FRACTION
                    stake = min(stake, BANKROLL_KES * MAX_BET_CAP)
                    
                    if stake > 0:
                        valid_accas.append({
                            "legs": combo,
                            "odds": combined_odds,
                            "implied_prob": combined_implied,
                            "devig_prob": combined_devig,
                            "model_prob": combined_model,
                            "edge": combined_edge,
                            "vig": effective_vig,
                            "stake": stake
                        })
                    
    return valid_accas, search_count

if __name__ == "__main__":
    from telegram_notifier import send_telegram_message
    
    print("Scouring live odds for +EV singles across 6 leagues...")
    legs = get_all_ev_legs()
    print(f"\nFound {len(legs)} individual legs with strictly positive edge (>1%).")
    
    # Categorize Legs
    soccer_legs = [leg for leg in legs if leg["league"] not in ["NBA", "EuroLeague", "NCAAB", "WNBA"]]
    nba_legs = [leg for leg in legs if leg["league"] in ["NBA", "EuroLeague", "NCAAB", "WNBA"]]
    
    print("\nBuilding independent 2-leg and 3-leg accumulators (Target Odds: around 2.0)...")
    
    accas_soccer, c1 = build_accumulators(soccer_legs, max_odds=3.5)
    accas_nba, c2 = build_accumulators(nba_legs, max_odds=3.5)
    
    # Bucket by date (this week vs future) and then sort by odds
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    seven_days = now + timedelta(days=7)
    
    def get_max_date(acca):
        max_d = now
        for leg in acca["legs"]:
            try:
                d = datetime.strptime(leg["date"], "%Y-%m-%dT%H:%M:%SZ")
                if d > max_d: max_d = d
            except: pass
        return max_d

    def sort_and_bucket(accas):
        this_week = []
        future = []
        for a in accas:
            if get_max_date(a) <= seven_days:
                this_week.append(a)
            else:
                future.append(a)
        this_week.sort(key=lambda x: abs(x["odds"] - 2.0))
        future.sort(key=lambda x: abs(x["odds"] - 2.0))
        return this_week + future

    accas_soccer = sort_and_bucket(accas_soccer)
    accas_nba = sort_and_bucket(accas_nba)
    
    # === MLB Pipeline (Independent) ===
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mlb_model.mlb_model import MLBModel
    from mlb_model.scanner import scan_mlb_edges
    
    print("\nStarting MLB Pipeline...")
    mlb_model = MLBModel()
    mlb_model.fit(seasons=[2024]) # Use current season for model state
    
    # API keys for OddsAPI rotation
    api_keys = [
        "017cbc1f3724942ba358b77a4b1095fe",
        "2dd91edd9c74fda2e0df435129777d4c",
        "0ecab0bb21f55f88ce50c67b38478c0d",
    ]
    mlb_legs = scan_mlb_edges(mlb_model, api_keys)
    accas_mlb, c3 = build_accumulators(mlb_legs, max_odds=3.5)
    accas_mlb = sort_and_bucket(accas_mlb)
    
    total_combinations = c1 + c2 + c3
    print(f"Total combinations evaluated (all sports): {total_combinations:,}")
    
    # Take the top N required
    top_soccer = accas_soccer[:10]
    top_nba = accas_nba[:10]
    top_mlb = accas_mlb[:10]
    
    # Save to Tracker Log for Post-Match Resolution & Retraining
    import json
    import os
    
    tracker_file = os.path.join(os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "acca_tracker.json"))
    tracked_data = []
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r") as f:
                tracked_data = json.load(f)
        except Exception:
            pass
            
    timestamp = datetime.utcnow().isoformat()
    all_tracked = top_soccer + top_nba + top_mlb
    
    for acca in all_tracked:
        acca_record = {
            "timestamp": timestamp,
            "status": "PENDING",
            "odds": acca["odds"],
            "edge": acca["edge"],
            "stake": acca["stake"],
            "legs": [
                {
                    "league": leg["league"],
                    "home": leg["home"],
                    "away": leg["away"],
                    "market": leg["market"],
                    "odds": leg["odds"],
                    "edge": leg["edge"],
                    "model_prob": leg.get("model_prob", 0),
                    "date": leg.get("date", ""),
                    "status": "PENDING"
                } for leg in acca["legs"]
            ]
        }
        tracked_data.append(acca_record)
        
    with open(tracker_file, "w") as f:
        json.dump(tracked_data, f, indent=4)

    import subprocess
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run(['python', os.path.join(BASE_DIR, 'sports_model', 'enrich_json.py')])
        
    # Send to Telegram
    if all_tracked:
        from telegram_notifier import get_telegram_messages_by_category, send_telegram_message
        messages = get_telegram_messages_by_category(top_soccer, top_nba, top_mlb)
        for msg in messages:
            send_telegram_message(msg)
