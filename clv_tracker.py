import json
import os
import requests
from datetime import datetime, timedelta
import time
from odds_api import SPORT_KEYS

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "acca_tracker.json")

def track_closing_lines():
    if not os.path.exists(TRACKER_FILE):
        return
        
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        print("Missing ODDS_API_KEY")
        return

    with open(TRACKER_FILE, "r") as f:
        tracker = json.load(f)
        
    now = datetime.utcnow()
    updated = False
    
    # We only want to ping leagues that actually have matches starting within 45 mins
    leagues_to_fetch = set()
    
    for acca in tracker:
        if acca.get("status") != "PENDING":
            continue
            
        for leg in acca.get("legs", []):
            if leg.get("status") != "PENDING" or "closing_odds" in leg:
                continue
                
            commence_str = leg.get("date")
            if not commence_str:
                continue
                
            try:
                # "2026-08-22T14:00:00Z"
                match_time = datetime.strptime(commence_str, "%Y-%m-%dT%H:%M:%SZ")
                time_diff = match_time - now
                
                # If match starts within the next 45 minutes, queue it for closing line check
                if timedelta(minutes=-120) <= time_diff <= timedelta(minutes=45):
                    leagues_to_fetch.add(leg["league"])
            except Exception as e:
                pass
                
    if not leagues_to_fetch:
        print("No matches starting within 45 minutes. Exiting.")
        return
        
    print(f"Fetching sharp closing lines for: {leagues_to_fetch}")
    
    # Cache fetched odds to avoid redundant API calls
    sharp_odds_cache = {}
    
    for league in leagues_to_fetch:
        sport_key = SPORT_KEYS.get(league)
        if not sport_key:
            continue
            
        # We target pinnacle, but fallback to betfair or draftkings if pinnacle is missing
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        params = {
            "apiKey": api_key,
            "regions": "eu,uk,us",
            "markets": "h2h,totals",
            "oddsFormat": "decimal",
            "bookmakers": "pinnacle,betfair,draftkings"
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            sharp_odds_cache[league] = resp.json()
        except Exception as e:
            print(f"Failed to fetch closing line for {league}: {e}")
            
    # Now update the tracker
    for acca in tracker:
        if acca.get("status") != "PENDING":
            continue
            
        for leg in acca.get("legs", []):
            if leg.get("status") != "PENDING" or "closing_odds" in leg or leg["league"] not in sharp_odds_cache:
                continue
                
            # Find the match
            match_data = None
            for event in sharp_odds_cache[leg["league"]]:
                if event["home_team"] == leg["home"] and event["away_team"] == leg["away"]:
                    match_data = event
                    break
                    
            if not match_data:
                continue
                
            # Extract the sharpest available odds
            sharpest_odds = 0.0
            
            for bookie in match_data.get("bookmakers", []):
                # We prefer Pinnacle
                for market in bookie.get("markets", []):
                    # Check H2H
                    if leg["market"] in ["Home Win", "Away Win", "Draw"] and market["key"] == "h2h":
                        target_name = leg["home"] if leg["market"] == "Home Win" else (leg["away"] if leg["market"] == "Away Win" else "Draw")
                        for outcome in market["outcomes"]:
                            if outcome["name"] == target_name:
                                sharpest_odds = max(sharpest_odds, outcome["price"])
                    # Check Totals
                    elif ("Over" in leg["market"] or "Under" in leg["market"]) and market["key"] == "totals":
                        target_name = "Over" if "Over" in leg["market"] else "Under"
                        for outcome in market["outcomes"]:
                            if outcome["name"] == target_name:
                                sharpest_odds = max(sharpest_odds, outcome["price"])
                                
            if sharpest_odds > 0:
                print(f"[{leg['league']}] {leg['home']} vs {leg['away']} | Tracked Closing Line: {sharpest_odds}")
                leg["closing_odds"] = sharpest_odds
                updated = True
                
    if updated:
        with open(TRACKER_FILE, "w") as f:
            json.dump(tracker, f, indent=4)
        print("Updated acca_tracker.json with closing lines.")
        
if __name__ == "__main__":
    track_closing_lines()
