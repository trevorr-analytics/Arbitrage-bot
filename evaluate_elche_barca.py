import sys
import os
sys.path.insert(0, r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot")

from dixon_coles import DixonColesModel, load_league_data

df_la = load_league_data("LaLiga")
model_la = DixonColesModel()
model_la.fit(df_la)

elche = next((t for t in model_la.teams_ if "elche" in t.lower()), None)
barca = next((t for t in model_la.teams_ if "barca" in t.lower() or "barcelona" in t.lower()), None)

if elche and barca:
    pred = model_la.predict(elche, barca)
    
    print("\n--- Match Prediction ---")
    print(f"Home ({elche}) Win Prob: {pred['home_win']:.2%}")
    print(f"Draw Prob: {pred['draw']:.2%}")
    print(f"Away ({barca}) Win Prob: {pred['away_win']:.2%}")
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
    print("Could not map Elche/Barcelona.")
