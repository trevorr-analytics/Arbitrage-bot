import os
import json
import requests
import pandas as pd
from datetime import datetime
from odds_api import SPORT_KEYS

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "acca_tracker.json")
BASE_DIR = os.path.dirname(__file__)

def get_scores(league: str) -> list:
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        print("Missing ODDS_API_KEY")
        return []
        
    sport_key = SPORT_KEYS.get(league)
    if not sport_key:
        return []
        
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/"
    params = {"apiKey": api_key, "daysFrom": 3}
    
    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error fetching scores for {league}: {e}")
    return []

def grade_leg(leg: dict, match_data: dict) -> str:
    """ Grades a specific leg based on actual match scores """
    if not match_data.get("completed", False):
        return "PENDING"
        
    scores = match_data.get("scores", [])
    if not scores:
        return "PENDING"
        
    h_score = 0
    a_score = 0
    for s in scores:
        if s["name"] == leg["home"]: h_score = int(s.get("score", 0) or 0)
        elif s["name"] == leg["away"]: a_score = int(s.get("score", 0) or 0)
        
    market = leg["market"]
    
    if market == "Home Win":
        return "WON" if h_score > a_score else "LOST"
    elif market == "Away Win":
        return "WON" if a_score > h_score else "LOST"
    elif market == "Draw":
        return "WON" if h_score == a_score else "LOST"
    elif "Over" in market:
        line = float(market.replace("Over ", ""))
        return "WON" if (h_score + a_score) > line else "LOST"
    elif "Under" in market:
        line = float(market.replace("Under ", ""))
        return "WON" if (h_score + a_score) < line else "LOST"
        
    return "PENDING"

def append_to_historical_data(league, home, away, h_score, a_score, date_str):
    """
    The Retraining Mechanism: Appends the actual result to the historical CSVs.
    The next time `accumulator_builder.py` runs, `DixonColesModel.fit()` will ingest
    this new row, mathematically adjusting the Poisson parameters to reflect the loss/win.
    """
    if league == "NBA":
        # NBA Elo model automatically updates via 538 sync in production
        return
        
    csv_path = os.path.join(BASE_DIR, f"football_data/{league}/2324.csv")
    if not os.path.exists(csv_path):
        return
        
    df = pd.read_csv(csv_path)
    
    # Check if we already appended this match
    if not df[(df['HomeTeam'] == home) & (df['AwayTeam'] == away) & (df['Date'] == date_str)].empty:
        return
        
    new_row = pd.DataFrame([{
        "Date": date_str,
        "HomeTeam": home,
        "AwayTeam": away,
        "FTHG": h_score,
        "FTAG": a_score,
        "FTR": "H" if h_score > a_score else ("A" if a_score > h_score else "D")
    }])
    
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(csv_path, index=False)
    print(f"[Retraining] Ingested new result into {league} dataset: {home} {h_score}-{a_score} {away}")

def resolve_and_retrain():
    if not os.path.exists(TRACKER_FILE):
        print("No active bets to resolve.")
        return
        
    with open(TRACKER_FILE, "r") as f:
        tracker = json.load(f)
        
    # Find all leagues with pending bets
    pending_leagues = set()
    for acca in tracker:
        if acca["status"] == "PENDING":
            for leg in acca["legs"]:
                if leg["status"] == "PENDING":
                    pending_leagues.add(leg["league"])
                    
    # Fetch scores for those leagues
    scores_cache = {}
    for league in pending_leagues:
        print(f"Fetching completed scores for {league}...")
        scores_cache[league] = get_scores(league)
        
    # Resolve bets
    updated_count = 0
    for acca in tracker:
        if acca["status"] != "PENDING":
            continue
            
        all_won = True
        any_lost = False
        
        for leg in acca["legs"]:
            if leg["status"] != "PENDING":
                if leg["status"] == "LOST": any_lost = True
                continue
                
            league_scores = scores_cache.get(leg["league"], [])
            
            # Find the match in the API response
            match_data = None
            for s in league_scores:
                if s["home_team"] == leg["home"] and s["away_team"] == leg["away"]:
                    match_data = s
                    break
                    
            if match_data and match_data.get("completed"):
                result = grade_leg(leg, match_data)
                leg["status"] = result
                
                # Extract scores for retraining
                h_s, a_s = 0, 0
                for score_obj in match_data.get("scores", []):
                    if score_obj["name"] == leg["home"]: h_s = int(score_obj.get("score", 0) or 0)
                    elif score_obj["name"] == leg["away"]: a_s = int(score_obj.get("score", 0) or 0)
                
                date_str = datetime.utcnow().strftime("%d/%m/%Y")
                append_to_historical_data(leg["league"], leg["home"], leg["away"], h_s, a_s, date_str)
                updated_count += 1
                
            if leg["status"] == "PENDING":
                all_won = False
            elif leg["status"] == "LOST":
                any_lost = True
                
        # Grade Acca
        if any_lost:
            acca["status"] = "LOST"
        elif all_won:
            acca["status"] = "WON"
            
    with open(TRACKER_FILE, "w") as f:
        json.dump(tracker, f, indent=4)
        
    print(f"\n[Resolution Complete] Resolved {updated_count} individual legs.")
    print("Models are now naturally updated with the latest scores. Future accumulators will reflect these mathematical adjustments.")

if __name__ == "__main__":
    resolve_and_retrain()
