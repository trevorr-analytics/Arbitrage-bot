import sys
import os
import pandas as pd

sys.path.append(os.path.abspath('sports_model'))
sys.path.append(os.path.abspath('core'))

from dixon_coles import DixonColesModel, load_league_data
from simulation import simulate_match

def run_simulate_match():
    data = load_league_data('EPL', min_seasons=2)
    model = DixonColesModel()
    model.fit(data)
    
    home = 'Man City'
    away = 'Bournemouth'
    
    home_xg, away_xg = model._get_lam_mu(home, away)
    rho = model.params_[-1] if model.params_ is not None else None
    
    n_sims = 50_000
    seed = 420
    
    res = simulate_match(home_xg=home_xg, away_xg=away_xg, n_sims=n_sims, dixon_coles_rho=rho, seed=seed)
    
    sim_prob = res.home_win_pct
    
    import math
    se = math.sqrt((sim_prob * (1 - sim_prob)) / n_sims)
    
    market_odds = 1.15
    ev = (sim_prob * (market_odds - 1)) - (1 - sim_prob)
    
    print(f"MATCH: {home} vs {away}, Upcoming")
    print(f"MARKET: Match winner")
    print(f"n_sims: {n_sims}          seed: {seed}")
    print(f"Simulated probability: {sim_prob:.4f}  (SE: ±{se:.4f})")
    print(f"Market odds: {market_odds:.2f}          Implied probability: {1/market_odds:.4f}")
    print(f"EV: {ev:.4f}")
    print(f"Dixon-Coles rho applied: {'yes' if rho is not None else 'no'}")
    
if __name__ == "__main__":
    run_simulate_match()
