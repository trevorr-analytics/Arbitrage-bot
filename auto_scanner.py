import os
import sys
import requests
import time
from datetime import datetime

# ==================== CONFIGURATION ====================
# Pulling keys securely from environment variables (GitHub Secrets)
API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")

# Fallback/Safety check: Ensure credentials exist before running
if not all([API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID]):
    print("[-] Error: Missing required environment secrets. Please check GitHub Secrets configuration.")
    sys.exit(1)

REGION = "eu"
MARKET = "h2h"

# League Lists
DOMESTIC_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one"
]
CHAMPIONS_LEAGUE = ["soccer_uefa_champs_league"]

# ==================== HELPERS ====================

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("[+] Alert sent successfully.")
        else:
            print(f"[-] Telegram failed to send: {response.text}")
    except Exception as e:
        print(f"[-] Telegram Connection Error: {e}")

def fetch_live_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "markets": MARKET,
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[-] API Error {response.status_code} on {sport_key}: {response.text[:100]}")
    except Exception as e:
        print(f"[-] Fetch Error on {sport_key}: {e}")
    return []

def scan_and_post(leagues_to_scan):
    print(f"[*] Scanning leagues: {leagues_to_scan}")
    total_arbs_found = 0
    
    for league in leagues_to_scan:
        matches = fetch_live_odds(league)
        if not matches:
            continue
            
        for match in matches:
            home_team = match["home_team"]
            away_team = match["away_team"]
            match_name = f"{home_team} vs {away_team}"
            
            best_odds = {"home": 0.0, "draw": 0.0, "away": 0.0}
            best_bookies = {"home": "", "draw": "", "away": ""}
            
            for bookmaker in match.get("bookmakers", []):
                bookie_name = bookmaker["title"]
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market.get("outcomes", []):
                            name = outcome["name"]
                            price = float(outcome["price"])
                            
                            if name == home_team and price > best_odds["home"]:
                                best_odds["home"] = price
                                best_bookies["home"] = bookie_name
                            elif name == away_team and price > best_odds["away"]:
                                best_odds["away"] = price
                                best_bookies["away"] = bookie_name
                            elif name == "Draw" and price > best_odds["draw"]:
                                best_odds["draw"] = price
                                best_bookies["draw"] = bookie_name
            
            # Mathematical Arbitrage Validation
            if best_odds["home"] > 0 and best_odds["draw"] > 0 and best_odds["away"] > 0:
                arb_sum = (1 / best_odds["home"]) + (1 / best_odds["draw"]) + (1 / best_odds["away"])
                
                # If sum is less than 1.0 (100%), arbitrage exists
                if arb_sum < 1.0:
                    profit_margin = (1 - arb_sum) * 100
                    total_arbs_found += 1
                    
                    # Clean visual card layout for Telegram members
                    alert_msg = (
                        f"?? *SPORTARB PRO ALERT* ??\n"
                        f"?????????????????????\n"
                        f"?? *Match:* `{match_name}`\n"
                        f"?? *Guaranteed ROI:* `{profit_margin:.2f}%`\n"
                        f"?????????????????????\n"
                        f"?? *Execution Strategy (1X2):*\n"
                        f"?? **Home ({home_team}):** `{best_odds['home']:.2f}` @ *{best_bookies['home']}*\n"
                        f"?? **Draw:** `{best_odds['draw']:.2f}` @ *{best_bookies['draw']}*\n"
                        f"?? **Away ({away_team}):** `{best_odds['away']:.2f}` @ *{best_bookies['away']}*\n"
                        f"?????????????????????\n"
                        f"?? _Calculate your optimal split staking via the dashboard._\n"
                        f"?? _Hedge immediately. Odds move quickly!_"
                    )
                    
                    print(f"[+] Arbitrage found: {match_name} ({profit_margin:.2f}% ROI)")
                    send_telegram_alert(alert_msg)
        
        # 1-second delay between requests to respect API rate limits
        time.sleep(1)
        
    print(f"[*] Scan completed. Total opportunities posted: {total_arbs_found}")

# ==================== SCHEDULER CONTROLLER ====================

def main():
    # 0 = Monday, 1 = Tuesday, 2 = Wednesday, ..., 6 = Sunday
    today_weekday = datetime.today().weekday()
    print(f"[*] Engine triggered. Day Index: {today_weekday} ({datetime.today().strftime('%A')})")
    
    leagues_to_scan = []
    
    # Monday Execution: Core Domestic Leagues + Champions League
    if today_weekday == 0:
        leagues_to_scan = DOMESTIC_LEAGUES + CHAMPIONS_LEAGUE
        print("[+] Monday protocol activated: Scanning Domestic + Champions Leagues.")
        
    # Wednesday Execution: Core Domestic Leagues Only
    elif today_weekday == 2:
        leagues_to_scan = DOMESTIC_LEAGUES
        print("[+] Wednesday protocol activated: Scanning Domestic Leagues.")
        
    else:
        print("[-] Off-schedule day. No API credits consumed. Exiting gracefully.")
        return

    if leagues_to_scan:
        scan_and_post(leagues_to_scan)

if __name__ == "__main__":
    main()