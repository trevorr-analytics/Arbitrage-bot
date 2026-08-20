import requests
import os
import json
import time

SPORT_KEYS = {
    "EPL": "soccer_epl",
    "Bundesliga": "soccer_germany_bundesliga",
    "LaLiga": "soccer_spain_la_liga",
    "SerieA": "soccer_italy_serie_a",
    "Ligue1": "soccer_france_ligue_one",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "NBA": "basketball_nba"
}

CACHE_FILE = os.path.join(os.path.dirname(__file__), "odds_cache.json")
CACHE_EXPIRY_SECONDS = 12 * 3600  # 12 hours

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f)

def fetch_live_odds(league: str, api_key: str = None) -> list:
    if api_key is None:
        api_key = os.environ.get("ODDS_API_KEY")
        
    if not api_key:
        print("\nERROR: ODDS_API_KEY environment variable is not set.")
        return []

    sport_key = SPORT_KEYS.get(league)
    if not sport_key:
        print(f"League {league} not supported for live odds.")
        return []

    cache = load_cache()
    current_time = time.time()
    
    # Check if we have valid cached data
    if sport_key in cache:
        cached_time = cache[sport_key].get("timestamp", 0)
        if current_time - cached_time < CACHE_EXPIRY_SECONDS:
            data = cache[sport_key].get("data", [])
            print(f"[OddsAPI] Loaded odds for {league} from local CACHE (saves API credits).")
            return _parse_odds_data(data)

    print(f"[OddsAPI] Fetching LIVE odds for {league} from API...", end=" ", flush=True)
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": api_key,
        "regions": "eu,uk,us", # added US for basketball
        "markets": "h2h,totals", 
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"FAILED. HTTP {response.status_code}: {response.text}")
            return []
            
        data = response.json()
        print(f"OK ({len(data)} matches found)")
        
        # Save to cache
        cache[sport_key] = {
            "timestamp": current_time,
            "data": data
        }
        save_cache(cache)
        
    except Exception as e:
        print(f"FAILED. Exception: {e}")
        return []

    return _parse_odds_data(data)

def _parse_odds_data(data):
    fixtures = []
    for event in data:
        home = event["home_team"]
        away = event["away_team"]
        
        odds = {
            "h2h": {"home": 0, "draw": 0, "away": 0},
            "totals": {"over": 0, "under": 0, "point": 0.0}
        }
        
        for bookie in event.get("bookmakers", []):
            for market in bookie.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == home:
                            odds["h2h"]["home"] = max(odds["h2h"]["home"], outcome["price"])
                        elif outcome["name"] == away:
                            odds["h2h"]["away"] = max(odds["h2h"]["away"], outcome["price"])
                        elif outcome["name"] == "Draw":
                            odds["h2h"]["draw"] = max(odds["h2h"]["draw"], outcome["price"])
                elif market["key"] == "totals":
                    for outcome in market["outcomes"]:
                        # Look for primary point spread/totals.
                        if outcome["name"] == "Over":
                            odds["totals"]["over"] = max(odds["totals"]["over"], outcome["price"])
                            if "point" in outcome:
                                odds["totals"]["point"] = outcome["point"]
                        elif outcome["name"] == "Under":
                            odds["totals"]["under"] = max(odds["totals"]["under"], outcome["price"])
                            if "point" in outcome:
                                odds["totals"]["point"] = outcome["point"]
        
        if odds["h2h"]["home"] == 0:
            continue
            
        fixtures.append((
            home, away, 
            odds["h2h"]["home"], odds["h2h"]["draw"], odds["h2h"]["away"], 
            odds["totals"]["over"], odds["totals"]["under"], odds["totals"]["point"],
            event.get("commence_time", "")
        ))
        
    return fixtures
