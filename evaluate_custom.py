import sys
import os
import numpy as np
sys.path.insert(0, r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot")

from dixon_coles import DixonColesModel, load_league_data, dixon_coles_tau
from scipy.stats import poisson

print("Evaluating Elche vs Barcelona (LaLiga)...")
df_la = load_league_data("LaLiga")
model_la = DixonColesModel()
model_la.fit(df_la)

elche = next((t for t in model_la.teams_ if "elche" in t.lower()), None)
barca = next((t for t in model_la.teams_ if "barca" in t.lower() or "barcelona" in t.lower()), None)

if elche and barca:
    lam, mu = model_la._get_lam_mu(elche, barca)
    rho = model_la.params_[-2]

    # Prob(Away Win & Over 1.5)
    # Away Win: j > i
    # Over 1.5: i + j >= 2
    prob_away_over_1_5 = 0.0
    for i in range(10): # Home goals
        for j in range(10): # Away goals
            if j > i and (i + j) >= 2:
                tau = dixon_coles_tau(i, j, lam, mu, rho)
                prob = tau * poisson.pmf(i, lam) * poisson.pmf(j, mu)
                prob_away_over_1_5 += prob
                
    print(f"LaLiga - Prob (Barcelona Win & Match Over 1.5): {prob_away_over_1_5:.4f} (Fair Odds: {1/prob_away_over_1_5:.2f})")
    
    # Check baseline Away Win to compare
    pred_la = model_la.predict(elche, barca)
    print(f"Baseline Barcelona Win: {pred_la['away_win']:.4f} (Fair Odds: {1/pred_la['away_win']:.2f})")
else:
    print("Could not map Elche/Barcelona.")

print("\nEvaluating Rennes vs PSG (Ligue 1)...")
df_fr = load_league_data("Ligue1")
model_fr = DixonColesModel()
model_fr.fit(df_fr)

rennes = next((t for t in model_fr.teams_ if "rennes" in t.lower() or "rennais" in t.lower()), None)
psg = next((t for t in model_fr.teams_ if "psg" in t.lower() or "paris" in t.lower()), None)

if rennes and psg:
    pred_fr = model_fr.predict(rennes, psg)
    over_2_5 = pred_fr["over_2_5"]
    print(f"Ligue 1 - Prob (Rennes vs PSG Over 2.5 Goals): {over_2_5:.4f} (Fair Odds: {1/over_2_5:.2f})")
else:
    print("Could not map Rennes/PSG.")

