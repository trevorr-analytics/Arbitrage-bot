import sys
sys.path.insert(0, r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot")

from dixon_coles import DixonColesModel, load_league_data

print("Evaluating PSV vs Groningen (Eredivisie)...")
df_ere = load_league_data("Eredivisie")
model_ere = DixonColesModel()
model_ere.fit(df_ere)

psv = next((t for t in model_ere.teams_ if "psv" in t.lower()), None)
groningen = next((t for t in model_ere.teams_ if "groningen" in t.lower()), None)

print(f"Mapped Teams: {psv} vs {groningen}")

if psv and groningen:
    pred = model_ere.predict(psv, groningen)
    
    print("\n--- Match Prediction ---")
    print(f"Home ({psv}) Win Prob: {pred['home_win']:.2%}")
    print(f"Draw Prob: {pred['draw']:.2%}")
    print(f"Away ({groningen}) Win Prob: {pred['away_win']:.2%}")
    print(f"Over 2.5 Goals Prob: {pred['over_2_5']:.2%}")
    print(f"Under 2.5 Goals Prob: {pred['under_2_5']:.2%}")
    print(f"BTTS Yes Prob: {pred['btts_yes']:.2%}")
    print(f"BTTS No Prob: {pred['btts_no']:.2%}")
    
    print("\n--- Fair Odds (Model CLV) ---")
    print(f"Home Win: {1/pred['home_win']:.2f}")
    print(f"Draw: {1/pred['draw']:.2f}")
    print(f"Away Win: {1/pred['away_win']:.2f}")
    print(f"Over 2.5: {1/pred['over_2_5']:.2f}")
    print(f"Under 2.5: {1/pred['under_2_5']:.2f}")
    print(f"BTTS Yes: {1/pred['btts_yes']:.2f}")
    print(f"BTTS No: {1/pred['btts_no']:.2f}")
else:
    print("Could not map PSV/Groningen.")
