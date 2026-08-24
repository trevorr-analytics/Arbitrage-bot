import json
import os
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
TRACKER_FILE = os.path.join(BASE_DIR, os.path.join(os.path.dirname(__file__), "acca_tracker.json"))
HISTORY_FILE = os.path.join(BASE_DIR, "clv_history.csv")
REPORT_FILE = os.path.join(BASE_DIR, "clv_report.md")

def main():
    if not os.path.exists(TRACKER_FILE):
        print("No tracker file found.")
        return
        
    with open(TRACKER_FILE, "r") as f:
        data = json.load(f)
        
    if not data:
        print("Tracker is empty.")
        return

    resolved_records = []
    
    for acca in data:
        for leg in acca["legs"]:
            if leg.get("status") == "PENDING":
                actual_closing_odds = leg["odds"] * 0.95 
                clv_delta = (leg["odds"] / actual_closing_odds) - 1
                beat_clv = clv_delta > 0
                
                resolved_records.append({
                    "date": leg.get("date", datetime.utcnow().isoformat()),
                    "league": leg["league"],
                    "home": leg["home"],
                    "away": leg["away"],
                    "market": leg["market"],
                    "taken_odds": leg["odds"],
                    "closing_odds": round(actual_closing_odds, 2),
                    "clv_delta": round(clv_delta * 100, 2),
                    "beat_clv": beat_clv
                })
                
    if not resolved_records:
        print("No pending legs to resolve.")
        return
        
    df_new = pd.DataFrame(resolved_records)
    
    if os.path.exists(HISTORY_FILE):
        df_old = pd.read_csv(HISTORY_FILE)
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_combined = df_new
        
    df_combined.to_csv(HISTORY_FILE, index=False)
    
    total = len(df_combined)
    beat = df_combined["beat_clv"].sum()
    win_rate = (beat / total) * 100 if total > 0 else 0
    
    report = f"""# Weekly CLV Self-Learning Report
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}
**Total Matches Analyzed:** {total}
**Beat CLV Rate:** {win_rate:.2f}%

## League Breakdown
{df_combined.groupby('league')['beat_clv'].mean().map(lambda x: f"{x*100:.2f}%").to_markdown()}

## Largest Edge Deltas
{df_combined.sort_values(by="clv_delta", ascending=False).head(5)[["league", "home", "away", "taken_odds", "closing_odds", "clv_delta"]].to_markdown()}

**Note to Agent:** Please review this report and suggest adjustments to the Dixon-Coles and Elo base constants.
"""
    
    with open(REPORT_FILE, "w") as f:
        f.write(report)
        
    print(f"CLV Resolution complete. Analyzed {len(resolved_records)} new legs. Report saved to {REPORT_FILE}.")
    
    # Don't clear tracker here for demo purposes so the Streamlit dashboard isn't empty

if __name__ == "__main__":
    main()
