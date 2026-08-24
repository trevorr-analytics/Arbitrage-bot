with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "r", encoding="utf-8") as f:
    text = f.read()

import re
# Find where if __name__ == "__main__": starts
idx = text.find("if __name__ == \"__main__\":")
new_main = """if __name__ == "__main__":
    from telegram_notifier import send_telegram_message
    
    print("Scouring live odds for +EV singles across 6 leagues...")
    legs = get_all_ev_legs()
    print(f"\\nFound {len(legs)} individual legs with strictly positive edge (>1%).")
    
    # Categorize Legs
    soccer_legs = [leg for leg in legs if leg["league"] not in ["NBA", "EuroLeague", "NCAAB", "WNBA"]]
    nba_legs = [leg for leg in legs if leg["league"] in ["NBA", "EuroLeague", "NCAAB", "WNBA"]]
    
    print("\\nBuilding independent 2-leg and 3-leg accumulators (Target Odds: around 2.0)...")
    
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
    
    total_combinations = c1 + c2
    print(f"Total combinations evaluated: {total_combinations:,}")
    
    # Take the top N required
    top_soccer = accas_soccer[:10]
    top_nba = accas_nba[:10]
    
    # Save to Tracker Log for Post-Match Resolution & Retraining
    import json
    import os
    
    tracker_file = os.path.join(os.path.dirname(__file__), "acca_tracker.json")
    tracked_data = []
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r") as f:
                tracked_data = json.load(f)
        except Exception:
            pass
            
    timestamp = datetime.utcnow().isoformat()
    all_tracked = top_soccer + top_nba
    
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
                    "date": leg.get("date", ""),
                    "status": "PENDING"
                } for leg in acca["legs"]
            ]
        }
        tracked_data.append(acca_record)
        
    with open(tracker_file, "w") as f:
        json.dump(tracked_data, f, indent=4)
        
    # Send to Telegram
    if all_tracked:
        from telegram_notifier import get_telegram_messages_by_category, send_telegram_message
        messages = get_telegram_messages_by_category(top_soccer, top_nba)
        for msg in messages:
            send_telegram_message(msg)
"""
text = text[:idx] + new_main
with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "w", encoding="utf-8") as f:
    f.write(text)
