import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from dixon_coles import DixonColesModel

def brier_score(predictions, outcomes):
    """
    Calculate Brier Score: Mean squared difference between predicted probability and actual outcome (0 or 1).
    Lower is better. Perfect = 0.0. Worst = 1.0.
    """
    return np.mean((np.array(predictions) - np.array(outcomes))**2)

def evaluate_soccer_calibration():
    print("Loading Soccer Data (EPL) for Calibration Test...")
    base_dir = r"C:\Users\hp\.gemini\antigravity\brain\c85e50ee-7a95-4650-94b3-2f337830cce5\scratch\betting"
    try:
        epl_22 = pd.read_csv(os.path.join(base_dir, 'football_data/EPL/2223.csv'))
        epl_23 = pd.read_csv(os.path.join(base_dir, 'football_data/EPL/2324.csv'))
        epl = pd.concat([epl_22, epl_23], ignore_index=True)
    except FileNotFoundError:
        print("EPL data not found. Skipping soccer evaluation.")
        return [], []

    # Prepare data
    epl['Date'] = pd.to_datetime(epl['Date'], format='%d/%m/%Y', errors='coerce')
    epl = epl.dropna(subset=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']).sort_values('Date')
    
    # We will simulate "walking forward"
    model = DixonColesModel(half_life_days=90.0)
    
    # Train on first 100 matches
    train_data = epl.iloc[:100]
    test_data = epl.iloc[100:]
    
    model.fit(train_data, league_name="EPL")
    known_teams = model.known_teams()
    
    predictions = []
    outcomes = []
    
    rolling_brier = []
    matches_processed = []
    
    print("Running sequential Soccer evaluation...")
    for idx, row in test_data.iterrows():
        if row['HomeTeam'] not in known_teams or row['AwayTeam'] not in known_teams:
            continue
            
        pred = model.predict(row['HomeTeam'], row['AwayTeam'])
        
        actual_home_win = 1 if row['FTHG'] > row['FTAG'] else 0
        
        predictions.append(pred['home_win'])
        outcomes.append(actual_home_win)
        
        if len(predictions) >= 50:
            recent_preds = predictions[-50:]
            recent_outs = outcomes[-50:]
            bs = brier_score(recent_preds, recent_outs)
            rolling_brier.append(bs)
            matches_processed.append(len(predictions))
            
    return matches_processed, rolling_brier

def evaluate_nba_calibration():
    print("Fetching NBA Data (FiveThirtyEight Historical) for Calibration Test...")
    try:
        nba = pd.read_csv("https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv")
        nba = nba[(nba['year_id'] >= 2013) & (nba['year_id'] <= 2015)].sort_values('date_game')
    except Exception as e:
        print(f"Could not load NBA data: {e}")
        return [], []
        
    predictions = []
    outcomes = []
    rolling_brier = []
    matches_processed = []
    
    print("Running sequential NBA evaluation...")
    for idx, row in nba.iterrows():
        # 538 already gives us their pre-game Elo win prob (elo_prob1)
        # We will use this to test how fast Elo calibrates in NBA
        pred_home_win = row['elo_prob1']
        actual_home_win = 1 if row['score1'] > row['score2'] else 0
        
        if pd.isna(pred_home_win) or pd.isna(actual_home_win):
            continue
            
        predictions.append(pred_home_win)
        outcomes.append(actual_home_win)
        
        if len(predictions) >= 50:
            recent_preds = predictions[-50:]
            recent_outs = outcomes[-50:]
            bs = brier_score(recent_preds, recent_outs)
            rolling_brier.append(bs)
            matches_processed.append(len(predictions))
            
    return matches_processed, rolling_brier

def main():
    print("=== HYPOTHESIS TEST: NBA vs SOCCER CALIBRATION ===\n")
    
    soc_matches, soc_brier = evaluate_soccer_calibration()
    nba_matches, nba_brier = evaluate_nba_calibration()
    
    if not soc_brier or not nba_brier:
        print("Missing data. Cannot compute comparison.")
        return
        
    # Analyze Convergence
    # We define "stable" as rolling variance over 100 matches dropping below 0.005
    soc_var = pd.Series(soc_brier).rolling(100).var()
    nba_var = pd.Series(nba_brier).rolling(100).var()
    
    soc_convergence = soc_var[soc_var < 0.005].first_valid_index()
    nba_convergence = nba_var[nba_var < 0.005].first_valid_index()
    
    print("\n=== RESULTS ===")
    print(f"Soccer (EPL) Average Brier Score: {np.mean(soc_brier):.4f}")
    print(f"Basketball (NBA) Average Brier Score: {np.mean(nba_brier):.4f}")
    
    print(f"\nMatches required for Brier Score Variance to stabilize (<0.005):")
    
    if soc_convergence:
        print(f"Soccer: ~{soc_matches[soc_convergence]} matches")
    else:
        print("Soccer: Did not mathematically stabilize within the test sample.")
        
    if nba_convergence:
        print(f"Basketball: ~{nba_matches[nba_convergence]} matches")
    else:
        print("Basketball: Did not mathematically stabilize within the test sample.")
        
    # Conclusion
    print("\nCONCLUSION:")
    if nba_convergence and soc_convergence and (nba_convergence < soc_convergence):
        print("Hypothesis SUPPORTED: The NBA model reached calibration stability significantly faster than the Soccer model.")
        print("The high density of possessions (~100 per game) effectively accelerates the law of large numbers, reducing the single-event variance that plagues low-scoring sports like soccer.")
    else:
        print("Hypothesis INCONCLUSIVE or REJECTED: NBA did not stabilize significantly faster in this sample.")
        
if __name__ == "__main__":
    main()
