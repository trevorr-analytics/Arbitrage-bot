import pandas as pd
import numpy as np
import re

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dixon_coles.py", "r", encoding="utf-8") as f:
    text = f.read()

# We need to inject the Elo calculation at the beginning of fit()
elo_injection = """
        # --- Elo Engine Blending ---
        # Calculate sequential Elo to create dynamic form inputs for the Poisson regression
        elo_dict = {t: 1500.0 for t in self.teams_}
        home_elo_before = np.zeros(len(data_fit))
        away_elo_before = np.zeros(len(data_fit))
        
        K = 20.0
        for i, row in enumerate(data_fit.itertuples()):
            h_team = row.HomeTeam
            a_team = row.AwayTeam
            h_goals = row.FTHG
            a_goals = row.FTAG
            
            h_elo = elo_dict[h_team]
            a_elo = elo_dict[a_team]
            
            home_elo_before[i] = h_elo
            away_elo_before[i] = a_elo
            
            # Standard Elo update
            expected_h = 1.0 / (1.0 + 10.0 ** ((a_elo - (h_elo + 65.0)) / 400.0))
            if h_goals > a_goals: actual_h = 1.0
            elif h_goals < a_goals: actual_h = 0.0
            else: actual_h = 0.5
            
            # Goal difference multiplier
            gd = abs(h_goals - a_goals)
            elo_diff = (h_elo + 65.0 - a_elo) if h_goals > a_goals else (a_elo - h_elo - 65.0)
            mult = np.log(gd + 1.0) * (2.2 / (elo_diff * 0.001 + 2.2)) if gd > 0 else 1.0
            
            shift = K * mult * (actual_h - expected_h)
            elo_dict[h_team] += shift
            elo_dict[a_team] -= shift
            
        data_fit["Home_Elo_Before"] = home_elo_before
        data_fit["Away_Elo_Before"] = away_elo_before
        self.current_elos_ = elo_dict
        
        home_elo_diff = (home_elo_before - away_elo_before) / 400.0
        away_elo_diff = (away_elo_before - home_elo_before) / 400.0
        # ---------------------------
"""

text = re.sub(r'        for team in self.teams_:.*?weights = self._compute_weights\(data_fit\)', 
              """        for team in self.teams_:
            team_games = data_fit[(data_fit["HomeTeam"] == team) | (data_fit["AwayTeam"] == team)]
            if not team_games.empty:
                self.last_match_dates_[team] = team_games["Date"].max()
            else:
                self.last_match_dates_[team] = pd.Timestamp("2000-01-01")
""" + elo_injection + """        weights = self._compute_weights(data_fit)""", text, flags=re.DOTALL)


# Now update initial params to include elo_coef (x0[-3] will be home_adv, x0[-2] rho, x0[-1] elo_coef)
param_init = """
        # Initial params: attack=0, defence=0, home_adv=0.3, rho=-0.1, elo_coef=0.0
        x0 = np.zeros(2 * n_teams + 3)
        x0[-3] = 0.3   # home advantage
        x0[-2] = -0.1  # rho
        x0[-1] = 0.0   # elo coefficient
"""
text = re.sub(r'        # Initial params:.*?x0\[-1\] = -0\.1  # rho', param_init, text, flags=re.DOTALL)

# Update neg_log_likelihood to use elo_coef
ll_func = """
        def neg_log_likelihood(params):
            attack = params[:n_teams]
            defence = params[n_teams:2*n_teams]
            home_adv = params[-3]
            rho = params[-2]
            elo_coef = params[-1]

            # Vectorized: compute all lambdas and mus at once
            lam = np.exp(attack[home_idx] - defence[away_idx] + home_adv + elo_coef * home_elo_diff)
            mu  = np.exp(attack[away_idx] - defence[home_idx] + elo_coef * away_elo_diff)
"""
text = re.sub(r'        def neg_log_likelihood\(params\):.*?mu  = np\.exp\(attack\[away_idx\] - defence\[home_idx\]\)', ll_func, text, flags=re.DOTALL)

# Update _get_lam_mu
lam_mu_func = """
    def _get_lam_mu(self, home_team: str, away_team: str, match_date: pd.Timestamp = None):
        \"\"\"Compute expected goals for home and away teams.\"\"\"
        n = len(self.teams_)
        attack  = self.params_[:n]
        defence = self.params_[n:2*n]
        home_adv = self.params_[-3]
        elo_coef = self.params_[-1]

        hi = self._team_idx.get(home_team)
        ai = self._team_idx.get(away_team)
        if hi is None or ai is None:
            raise ValueError(f"Unknown team(s): {home_team}, {away_team}")
            
        h_elo = self.current_elos_.get(home_team, 1500.0)
        a_elo = self.current_elos_.get(away_team, 1500.0)
        h_diff = (h_elo - a_elo) / 400.0
        a_diff = (a_elo - h_elo) / 400.0

        lam = np.exp(attack[hi] - defence[ai] + home_adv + elo_coef * h_diff)  # home xG
        mu  = np.exp(attack[ai] - defence[hi] + elo_coef * a_diff)              # away xG
                
        return lam, mu
"""
text = re.sub(r'    def _get_lam_mu\(self, home_team: str, away_team: str, match_date: pd\.Timestamp = None\):.*?return lam, mu', lam_mu_func, text, flags=re.DOTALL)

# Also fix the rho fetch in predict() because it shifted from -1 to -2
text = text.replace("rho = self.params_[-1]", "rho = self.params_[-2]")

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dixon_coles.py", "w", encoding="utf-8") as f:
    f.write(text)
