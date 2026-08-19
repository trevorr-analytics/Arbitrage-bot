import os
import sys
import math
import itertools
import pandas as pd
from typing import List, Dict

sys.path.insert(0, os.path.dirname(__file__))
from dixon_coles import DixonColesModel, load_league_data
from odds_api import fetch_live_odds
from devig import shin_devig

from nba_model import NBAModel
from telegram_notifier import send_telegram_message, format_accas_for_telegram

BANKROLL_KES = 5000.0
MIN_SINGLE_EDGE = 0.01  
KELLY_FRACTION = 0.125  
MAX_BET_CAP = 0.01      
TARGET_MIN_ODDS = 1.8
TARGET_MAX_ODDS = 2.4

LEAGUES = ["EPL", "Bundesliga", "LaLiga", "SerieA", "Ligue1", "Eredivisie", "NBA"]

def safe_devig(odds_list):
    if any(o <= 1.0 for o in odds_list):
        return [0.0] * len(odds_list)
    try:
        return shin_devig(odds_list)
    except Exception:
        return [0.0] * len(odds_list)

def fuzzy_team(name: str, known: list) -> str:
    name_lower = name.lower()
    for k in known:
        if k.lower() == name_lower: return k
    for k in known:
        if name_lower in k.lower() or k.lower() in name_lower: return k
    name_tokens = set(name_lower.split())
    for k in known:
        if name_tokens & set(k.lower().split()): return k
    return None

def get_all_ev_legs() -> List[Dict]:
    ev_legs = []
    for league in LEAGUES:
        # Load Data & Model based on sport
        if league == "NBA":
            model = NBAModel()
            model.fit() # Stub fit for now, later replaced with full 538 history
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
            home, away, o_h, o_d, o_a, o_ov, o_un, point_line = fix[:8]
            h_match = fuzzy_team(home, known)
            a_match = fuzzy_team(away, known)
            if not (h_match and a_match): continue
            
            if league == "NBA":
                pred = model.predict(h_match, a_match, over_under_line=point_line if point_line > 0 else 225.5)
            else:
                pred = model.predict(h_match, a_match)
                # Map soccer outputs to uniform keys
                pred["over_total"] = pred["over_2_5"]
                pred["under_total"] = pred["under_2_5"]
            
            # Devig
            if league == "NBA":
                # NBA moneylines are usually 2-way
                dv_h, dv_a = safe_devig([o_h, o_a])[:2]
                dv_d = 0.0
            else:
                dv_h, dv_d, dv_a = safe_devig([o_h, o_d, o_a])
                
            dv_ov, dv_un = safe_devig([o_ov, o_un])
            
            match_id = f"{league}_{home}_{away}"
            
            mkt_str = f"Over {point_line}" if league == "NBA" and point_line > 0 else "Over 2.5"
            umkt_str = f"Under {point_line}" if league == "NBA" and point_line > 0 else "Under 2.5"
            
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
                            "home": home,
                            "away": away,
                            "market": mkt_name,
                            "odds": odds,
                            "devig_prob": dv_prob,
                            "model_prob": mod_prob,
                            "edge": edge
                        })
    return ev_legs

def build_accumulators(ev_legs: List[Dict]):
    valid_accas = []
    search_count = 0
    
    # 2-leg and 3-leg combinations
    for r in [2, 3]:
        for combo in itertools.combinations(ev_legs, r):
            search_count += 1
            
            # 1. Strict Correlation Check: Reject if multiple legs share the same match.
            # We assume matches across different games are independent.
            match_ids = [leg["match_id"] for leg in combo]
            if len(set(match_ids)) != len(combo):
                continue
                
            combined_odds = math.prod(leg["odds"] for leg in combo)
            
            # 2. Target Range Check
            if TARGET_MIN_ODDS <= combined_odds <= TARGET_MAX_ODDS:
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
    print("Scouring live odds for +EV singles across 6 leagues...")
    legs = get_all_ev_legs()
    print(f"\nFound {len(legs)} individual legs with strictly positive edge (>1%).")
    
    print("\nBuilding independent 2-leg and 3-leg accumulators (Target Odds: 1.8 - 2.4)...")
    accas, search_count = build_accumulators(legs)
    
    # Sort strictly by combined edge, not raw odds
    accas.sort(key=lambda x: x["edge"], reverse=True)
    
    print(f"Total combinations evaluated: {search_count:,}")
    print(f"Total mathematically valid +EV accumulators found: {len(accas)}")
    
    print("\n" + "="*90)
    print("  TOP ACCUMULATORS BY COMBINED EDGE")
    print("  Correlation guard: NO same-game legs permitted.")
    print("  Staking guard: 1/8th Kelly, Max 1% Bankroll (KES 50)")
    print("="*90)
    
    for i, acca in enumerate(accas[:10]):
        print(f"\n[Acca #{i+1}]  Combined Odds: {acca['odds']:.2f}")
        print(f"  Implied Prob: {acca['implied_prob']*100:.1f}%  |  Devigged Prob: {acca['devig_prob']*100:.1f}%  |  Model Prob: {acca['model_prob']*100:.1f}%")
        print(f"  Combined Edge: +{acca['edge']*100:.2f}%  |  Effective Combined Vig: {acca['vig']*100:.2f}%")
        print(f"  Suggested Stake: KES {acca['stake']:.0f}")
        print("  Legs:")
        for leg in acca['legs']:
            print(f"    -> [{leg['league']}] {leg['home']} vs {leg['away']} | {leg['market']} @ {leg['odds']:.2f} (Single Edge: +{leg['edge']*100:.1f}%)")
    # Save to Tracker Log for Post-Match Resolution & Retraining
    import json
    import os
    from datetime import datetime
    
    tracker_file = os.path.join(os.path.dirname(__file__), "acca_tracker.json")
    tracked_data = []
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r") as f:
                tracked_data = json.load(f)
        except Exception:
            pass
            
    timestamp = datetime.utcnow().isoformat()
    for acca in accas[:10]:
        acca_record = {
            "timestamp": timestamp,
            "status": "PENDING",
            "combined_odds": acca["odds"],
            "combined_edge": acca["edge"],
            "stake": acca["stake"],
            "legs": []
        }
        for leg in acca["legs"]:
            acca_record["legs"].append({
                "match_id": leg["match_id"],
                "league": leg["league"],
                "home": leg["home"],
                "away": leg["away"],
                "market": leg["market"],
                "odds": leg["odds"],
                "edge": leg["edge"],
                "status": "PENDING"
            })
        tracked_data.append(acca_record)
        
    with open(tracker_file, "w") as f:
        json.dump(tracked_data, f, indent=4)
        
    # Send to Telegram
    if accas:
        tg_message = format_accas_for_telegram(accas, top_n=10)
        send_telegram_message(tg_message)
