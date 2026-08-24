with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_api.py", "r", encoding="utf-8") as f:
    text = f.read()

new_logic = """def fetch_live_odds(league: str, api_key: str = None) -> list:
    sport_key = SPORT_KEYS.get(league)
    if not sport_key:
        print(f"League {league} not supported for live odds.")
        return []

    cache = load_cache()
    current_time = time.time()
    if sport_key in cache:
        # If API key is missing, ignore expiry and just return cache
        if api_key is None and not os.environ.get("ODDS_API_KEY"):
            print(f"Using offline cache for {league} because API key is missing.")
            return cache[sport_key]["data"]
            
        cached_time = cache[sport_key].get("timestamp", 0)
        if current_time - cached_time < CACHE_EXPIRY_SECONDS:
            return cache[sport_key]["data"]

    if api_key is None:
        api_key = os.environ.get("ODDS_API_KEY")
        
    if not api_key:
        print("\\nERROR: ODDS_API_KEY environment variable is not set.")
        return []
"""

import re
text = re.sub(r'def fetch_live_odds\(league: str, api_key: str = None\) -> list:.*?return \[\]\n\n    sport_key = SPORT_KEYS\.get\(league\)\n    if not sport_key:\n        print\(f"League \{league\} not supported for live odds\."\)\n        return \[\]\n\n    cache = load_cache\(\)\n    current_time = time\.time\(\)\n', new_logic, text, flags=re.DOTALL)

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_api.py", "w", encoding="utf-8") as f:
    f.write(text)
