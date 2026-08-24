import json
import os
import time
import requests
import statistics

SPORT_KEYS = {
    "EPL": "soccer_epl",
    "Bundesliga": "soccer_germany_bundesliga",
    "LaLiga": "soccer_spain_la_liga",
    "SerieA": "soccer_italy_serie_a",
    "Ligue1": "soccer_france_ligue_one",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "NBA": "basketball_nba",
    "EuroLeague": "basketball_euroleague",
    "NCAAB": "basketball_ncaab",
    "WNBA": "basketball_wnba"
}

CACHE_FILE = os.path.join(os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "odds_cache.json"))
CACHE_EXPIRY_SECONDS = 3600 * 12 # 12 hours to save credits

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
    sport_key = SPORT_KEYS.get(league)
    if not sport_key:
        print(f"League {league} not supported for live odds.")
        return []

    cache = load_cache()
    current_time = time.time()
    
    if sport_key in cache:
        if api_key is None and not os.environ.get("ODDS_API_KEY"):
            print(f"Using offline cache for {league} because API key is missing.")
            return _parse_odds_data(cache[sport_key]["data"])
            
        cached_time = cache[sport_key].get("timestamp", 0)
        if current_time - cached_time < CACHE_EXPIRY_SECONDS:
            return _parse_odds_data(cache[sport_key]["data"])

    if api_key is None:
        api_key = os.environ.get("ODDS_API_KEY")
        
    if not api_key:
        print("\nERROR: ODDS_API_KEY environment variable is not set.")
        return []
    
    print(f"[OddsAPI] Fetching LIVE odds for {league} from API...", end=" ", flush=True)
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": api_key,
        "regions": "eu,uk,us",
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
        
        # Collect all odds from all bookies to find the median (market average)
        home_odds, draw_odds, away_odds = [], [], []
        over_odds, under_odds, points = [], [], []
        
        for bookie in event.get("bookmakers", []):
            for market in bookie.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == home:
                            home_odds.append(outcome["price"])
                        elif outcome["name"] == away:
                            away_odds.append(outcome["price"])
                        elif outcome["name"] == "Draw":
                            draw_odds.append(outcome["price"])
                elif market["key"] == "totals":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == "Over":
                            over_odds.append(outcome["price"])
                            if "point" in outcome:
                                points.append(outcome["point"])
                        elif outcome["name"] == "Under":
                            under_odds.append(outcome["price"])
                            if "point" in outcome:
                                points.append(outcome["point"])
        
        if not home_odds or not away_odds:
            continue
            
        # Use MEDIAN to prevent a single glitched bookmaker from ruining the accumulator
        h_med = statistics.median(home_odds) if home_odds else 0.0
        d_med = statistics.median(draw_odds) if draw_odds else 0.0
        a_med = statistics.median(away_odds) if away_odds else 0.0
        ov_med = statistics.median(over_odds) if over_odds else 0.0
        un_med = statistics.median(under_odds) if under_odds else 0.0
        pt_med = statistics.median(points) if points else 0.0
        
        fixtures.append((
            home, away, 
            h_med, d_med, a_med, 
            ov_med, un_med, pt_med,
            event.get("commence_time", "")
        ))
        
    return fixtures
