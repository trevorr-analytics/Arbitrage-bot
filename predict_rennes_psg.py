import sys
import os
sys.path.insert(0, r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot")

from dixon_coles import DixonColesModel, load_league_data

print("Loading Ligue 1 data and fitting model...")
df = load_league_data("Ligue1")
model = DixonColesModel()
model.fit(df)

teams = model.teams_
rennes_name = next((t for t in teams if "rennes" in t.lower() or "rennais" in t.lower()), None)
psg_name = next((t for t in teams if "psg" in t.lower() or "paris" in t.lower()), None)

print(f"Mapped Teams: Rennes -> '{rennes_name}', PSG -> '{psg_name}'")

if rennes_name and psg_name:
    pred = model.predict(rennes_name, psg_name)
    
    print("\n--- Match Prediction ---")
    print(f"Home ({rennes_name}) Win Prob: {pred['home_win']:.2%}")
    print(f"Draw Prob: {pred['draw']:.2%}")
    print(f"Away ({psg_name}) Win Prob: {pred['away_win']:.2%}")
    print(f"Over 2.5 Goals Prob: {pred['over_2_5']:.2%}")
    print(f"Under 2.5 Goals Prob: {pred['under_2_5']:.2%}")
    
    print("\n--- Fair Odds (Model CLV) ---")
    print(f"Home Win: {1/pred['home_win']:.2f}")
    print(f"Draw: {1/pred['draw']:.2f}")
    print(f"Away Win: {1/pred['away_win']:.2f}")
    print(f"Over 2.5: {1/pred['over_2_5']:.2f}")
    print(f"Under 2.5: {1/pred['under_2_5']:.2f}")
else:
    print("Could not map team names.")
