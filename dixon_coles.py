"""
Dixon-Coles Bivariate Poisson Model
Derives 1X2, Over/Under 2.5, and BTTS probabilities for any fixture
given historical results data.
"""
import numpy as np
import pandas as pd
from scipy.stats import poisson
from scipy.optimize import minimize
import os
import glob
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = os.path.join(os.path.dirname(__file__), "football_data")


def load_league_data(league_name: str, min_seasons: int = 3) -> pd.DataFrame:
    """Load and concatenate all CSV files for a league."""
    pattern = os.path.join(DATA_DIR, league_name, "*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No data found for {league_name} at {pattern}")

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding="latin-1", low_memory=False)
            # Standardise column names
            df.columns = [c.strip() for c in df.columns]
            frames.append(df)
        except Exception:
            pass

    data = pd.concat(frames, ignore_index=True)

    # Require at minimum: Date, HomeTeam, AwayTeam, FTHG, FTAG
    required = ["HomeTeam", "AwayTeam", "FTHG", "FTAG"]
    data = data.dropna(subset=required)
    data["FTHG"] = pd.to_numeric(data["FTHG"], errors="coerce")
    data["FTAG"] = pd.to_numeric(data["FTAG"], errors="coerce")
    data = data.dropna(subset=["FTHG", "FTAG"])
    
    # Calculate Expected Goals proxy from Shots on Target (if available)
    if "HST" in data.columns and "AST" in data.columns:
        data["HST"] = pd.to_numeric(data["HST"], errors="coerce").fillna(data["FTHG"] / 0.33)
        data["AST"] = pd.to_numeric(data["AST"], errors="coerce").fillna(data["FTAG"] / 0.33)
        # 1 Shot on Target is roughly 0.33 Expected Goals
        data["HxG"] = data["HST"] * 0.33
        data["AxG"] = data["AST"] * 0.33
        # Blend 70% Actual Goals and 30% xG to smooth out variance
        data["FTHG_Blended"] = (data["FTHG"] * 0.7) + (data["HxG"] * 0.3)
        data["FTAG_Blended"] = (data["FTAG"] * 0.7) + (data["AxG"] * 0.3)
    else:
        data["FTHG_Blended"] = data["FTHG"]
        data["FTAG_Blended"] = data["FTAG"]
        
    data["FTHG"] = data["FTHG"].astype(int)
    data["FTAG"] = data["FTAG"].astype(int)

    # Parse date
    for fmt in ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"]:
        try:
            data["Date"] = pd.to_datetime(data["Date"], format=fmt)
            break
        except Exception:
            pass

    data = data.sort_values("Date").reset_index(drop=True)
    return data


def dixon_coles_tau(home_g: int, away_g: int, lam: float, mu: float, rho: float) -> float:
    """Dixon-Coles correction factor for low-scoring scorelines."""
    if home_g == 0 and away_g == 0:
        return 1.0 - lam * mu * rho
    elif home_g == 0 and away_g == 1:
        return 1.0 + lam * rho
    elif home_g == 1 and away_g == 0:
        return 1.0 + mu * rho
    elif home_g == 1 and away_g == 1:
        return 1.0 - rho
    else:
        return 1.0


class DixonColesModel:
    """
    Dixon-Coles bivariate Poisson with time-decay weighting.
    Estimates attack/defence strengths for each team + home advantage + rho correction.
    """

    def __init__(self, half_life_days: float = 90.0, use_xg: bool = True, xg_weight: float = 0.5, use_fatigue: bool = False):
        self.half_life_days = half_life_days
        self.use_xg = use_xg
        self.xg_weight = xg_weight
        self.use_fatigue = use_fatigue
        self.params_ = None
        self.teams_ = None
        self.league_name_ = None

    def _compute_weights(self, data: pd.DataFrame) -> np.ndarray:
        """Exponential time-decay weights relative to most recent match."""
        max_date = data["Date"].max()
        days_ago = (max_date - data["Date"]).dt.days.values
        return np.exp(-np.log(2) * days_ago / self.half_life_days)

    def fit(self, data: pd.DataFrame, league_name: str = ""):
        # Pre-process xG blending based on toggles
        if self.use_xg and "HST" in data.columns and "AST" in data.columns:
            data_fit = data.copy()
            data_fit["HST"] = pd.to_numeric(data_fit["HST"], errors="coerce").fillna(data_fit["FTHG"] / 0.33)
            data_fit["AST"] = pd.to_numeric(data_fit["AST"], errors="coerce").fillna(data_fit["FTAG"] / 0.33)
            hxG = data_fit["HST"] * 0.33
            axG = data_fit["AST"] * 0.33
            data_fit["FTHG_Blended"] = (data_fit["FTHG"] * (1 - self.xg_weight)) + (hxG * self.xg_weight)
            data_fit["FTAG_Blended"] = (data_fit["FTAG"] * (1 - self.xg_weight)) + (axG * self.xg_weight)
        else:
            data_fit = data.copy()
            data_fit["FTHG_Blended"] = data_fit["FTHG"]
            data_fit["FTAG_Blended"] = data_fit["FTAG"]
            
        self.league_name_ = league_name
        self.teams_ = sorted(set(data_fit["HomeTeam"]) | set(data_fit["AwayTeam"]))
        n_teams = len(self.teams_)
        team_idx = {t: i for i, t in enumerate(self.teams_)}
        self._team_idx = team_idx

        # Track last match date for fatigue penalty
        self.last_match_dates_ = {}
        # Ensure date is parsed properly
        if not pd.api.types.is_datetime64_any_dtype(data_fit['Date']):
            data_fit['Date'] = pd.to_datetime(data_fit['Date'], dayfirst=True, errors='coerce')
            
        for team in self.teams_:
            team_games = data_fit[(data_fit["HomeTeam"] == team) | (data_fit["AwayTeam"] == team)]
            if not team_games.empty:
                self.last_match_dates_[team] = team_games["Date"].max()
            else:
                self.last_match_dates_[team] = pd.Timestamp("2000-01-01")

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
        weights = self._compute_weights(data_fit)
        home_goals = data_fit["FTHG_Blended"].values
        away_goals = data_fit["FTAG_Blended"].values
        home_idx = np.array([team_idx[t] for t in data_fit["HomeTeam"]])
        away_idx = np.array([team_idx[t] for t in data_fit["AwayTeam"]])

        actual_hg = data_fit["FTHG"].values
        actual_ag = data_fit["FTAG"].values


        # Initial params: attack=0, defence=0, home_adv=0.3, rho=-0.1, elo_coef=0.0
        x0 = np.zeros(2 * n_teams + 3)
        x0[-3] = 0.3   # home advantage
        x0[-2] = -0.1  # rho
        x0[-1] = 0.0   # elo coefficient


        from scipy.special import gammaln
        log_fact_home = gammaln(home_goals + 1)
        log_fact_away = gammaln(away_goals + 1)
        

        def neg_log_likelihood(params):
            attack = params[:n_teams]
            defence = params[n_teams:2*n_teams]
            home_adv = params[-3]
            rho = params[-2]
            elo_coef = params[-1]

            # Vectorized: compute all lambdas and mus at once
            lam = np.exp(attack[home_idx] - defence[away_idx] + home_adv + elo_coef * home_elo_diff)
            mu  = np.exp(attack[away_idx] - defence[home_idx] + elo_coef * away_elo_diff)


            # Vectorized Poisson log-PMF using precomputed log-factorials
            log_p_home = home_goals * np.log(lam) - lam - log_fact_home
            log_p_away = away_goals * np.log(mu)  - mu  - log_fact_away

            # Dixon-Coles tau correction (vectorized per case)
            tau = np.ones(len(home_goals))
            # Use actual integer goals to apply the low-score correlation fix
            mask_00 = (actual_hg == 0) & (actual_ag == 0)
            mask_01 = (actual_hg == 0) & (actual_ag == 1)
            mask_10 = (actual_hg == 1) & (actual_ag == 0)
            mask_11 = (actual_hg == 1) & (actual_ag == 1)
            tau[mask_00] = 1.0 - lam[mask_00] * mu[mask_00] * rho
            tau[mask_01] = 1.0 + lam[mask_01] * rho
            tau[mask_10] = 1.0 + mu[mask_10] * rho
            tau[mask_11] = 1.0 - rho

            tau = np.maximum(tau, 1e-10)
            log_tau = np.log(tau)

            ll = np.sum(weights * (log_tau + log_p_home + log_p_away))
            return -ll

        # Constraint: sum of attack params = 0 (identifiability)
        constraints = {"type": "eq",
                       "fun": lambda p: np.sum(p[:n_teams])}

        result = minimize(
            neg_log_likelihood,
            x0,
            method="L-BFGS-B",
            options={"maxiter": 500, "ftol": 1e-8},
        )

        self.params_ = result.x
        self._team_idx = team_idx
        return self


    def _get_lam_mu(self, home_team: str, away_team: str, match_date: pd.Timestamp = None):
        """Compute expected goals for home and away teams."""
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


    def predict(self, home_team: str, away_team: str, max_goals: int = 8, match_date: pd.Timestamp = None) -> dict:
        """
        Returns probabilities for 1X2, BTTS, and O/U 2.5
        """
        lam, mu = self._get_lam_mu(home_team, away_team, match_date)
        rho = self.params_[-2]

        # Build scoreline probability matrix
        matrix = np.zeros((max_goals + 1, max_goals + 1))
        for hg in range(max_goals + 1):
            for ag in range(max_goals + 1):
                tau = dixon_coles_tau(hg, ag, lam, mu, rho)
                matrix[hg, ag] = tau * poisson.pmf(hg, lam) * poisson.pmf(ag, mu)

        matrix /= matrix.sum()  # Normalise to sum to 1.0

        home_win = float(np.sum(np.tril(matrix, -1)))   # hg > ag
        draw     = float(np.trace(matrix))               # hg == ag
        away_win = float(np.sum(np.triu(matrix, 1)))    # ag > hg

        over_2_5  = float(np.sum([matrix[h, a] for h in range(max_goals + 1)
                                   for a in range(max_goals + 1) if h + a > 2]))
        under_2_5 = 1.0 - over_2_5

        btts_yes = float(np.sum([matrix[h, a] for h in range(1, max_goals + 1)
                                  for a in range(1, max_goals + 1)]))
        btts_no  = 1.0 - btts_yes

        return {
            "home_xg": round(lam, 3),
            "away_xg": round(mu, 3),
            "home_win": round(home_win, 4),
            "draw":     round(draw, 4),
            "away_win": round(away_win, 4),
            "over_2_5": round(over_2_5, 4),
            "under_2_5": round(under_2_5, 4),
            "btts_yes": round(btts_yes, 4),
            "btts_no":  round(btts_no, 4),
        }

    def known_teams(self) -> list:
        return list(self.teams_)

