import os
import sys
import requests
import time
from datetime import datetime

# ==================== CONFIGURATION ====================
API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")

if not all([API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID]):
    print("[-] Error: Missing required environment secrets. Verify GitHub Secrets.")
    sys.exit(1)

REGION = "eu"
MARKET = "h2h"

# Filtering specifically for bookmakers accessible in Kenya or supporting Crypto
TARGET_BOOKMAKERS = "1xbet,22bet,betway,mozzartbet,pinnacle,unibet"

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
            print("[+] Alert successfully delivered to Telegram.")
        else:
            print(f"[-] Telegram failed: {response.text}")
    except Exception as e:
        print(f"[-] Connection Error: {e}")

def fetch_live_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "bookmakers": TARGET_BOOKMAKERS,  # Restricted to local/crypto bookmakers
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
    print(f"[*] Executing target scan on: {leagues_to_scan}")
    total_arbs = 0
    
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
            
            if best_odds["home"] > 0 and best_odds["draw"] > 0 and best_odds["away"] > 0:
                arb_sum = (1 / best_odds["home"]) + (1 / best_odds["draw"]) + (1 / best_odds["away"])
                
                if arb_sum < 1.0:
                    profit_margin = (1 - arb_sum) * 100
                    total_arbs += 1
                    
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
                        f"?? _Available via M-Pesa & Instant Crypto Bookmakers._\n"
                        f"?? _Calculate stakes via dashboard. Execute quickly!_"
                    )
                    
                    print(f"[+] Arbitrage found: {match_name} ({profit_margin:.2f}% ROI)")
                    send_telegram_alert(alert_msg)
        
        time.sleep(1)
        
    print(f"[*] Scan finished. Total alerts sent: {total_arbs}")

def main():
    today_weekday = datetime.today().weekday()
    print(f"[*] Task Triggered. Weekday Index: {today_weekday}")
    
    leagues_to_scan = []
    if today_weekday == 0:  # Monday
        leagues_to_scan = DOMESTIC_LEAGUES + CHAMPIONS_LEAGUE
    elif today_weekday == 2:  # Wednesday
        leagues_to_scan = DOMESTIC_LEAGUES
    else:
        print("[-] Off-schedule day. Exiting.")
        return

    if leagues_to_scan:
        scan_and_post(leagues_to_scan)

if __name__ == "__main__":
    main()