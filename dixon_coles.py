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

    def __init__(self, half_life_days: float = 90.0):
        self.half_life_days = half_life_days
        self.params_ = None
        self.teams_ = None
        self.league_name_ = None

    def _compute_weights(self, data: pd.DataFrame) -> np.ndarray:
        """Exponential time-decay weights relative to most recent match."""
        max_date = data["Date"].max()
        days_ago = (max_date - data["Date"]).dt.days.values
        return np.exp(-np.log(2) * days_ago / self.half_life_days)

    def fit(self, data: pd.DataFrame, league_name: str = ""):
        self.league_name_ = league_name
        self.teams_ = sorted(set(data["HomeTeam"]) | set(data["AwayTeam"]))
        n_teams = len(self.teams_)
        team_idx = {t: i for i, t in enumerate(self.teams_)}

        weights = self._compute_weights(data)
        home_goals = data["FTHG"].values
        away_goals = data["FTAG"].values
        home_idx = np.array([team_idx[t] for t in data["HomeTeam"]])
        away_idx = np.array([team_idx[t] for t in data["AwayTeam"]])

        # Initial params: attack=0, defence=0, home_adv=0.3, rho=-0.1
        x0 = np.zeros(2 * n_teams + 2)
        x0[-2] = 0.3   # home advantage
        x0[-1] = -0.1  # rho

        from scipy.special import gammaln
        # Precompute log(k!) for all observed goal counts — called once, not per iteration
        log_fact_home = gammaln(home_goals + 1)
        log_fact_away = gammaln(away_goals + 1)

        def neg_log_likelihood(params):
            attack = params[:n_teams]
            defence = params[n_teams:2*n_teams]
            home_adv = params[-2]
            rho = params[-1]

            # Vectorized: compute all lambdas and mus at once
            lam = np.exp(attack[home_idx] - defence[away_idx] + home_adv)
            mu  = np.exp(attack[away_idx] - defence[home_idx])

            # Vectorized Poisson log-PMF using precomputed log-factorials
            log_p_home = home_goals * np.log(lam) - lam - log_fact_home
            log_p_away = away_goals * np.log(mu)  - mu  - log_fact_away


            # Dixon-Coles tau correction (vectorized per case)
            tau = np.ones(len(home_goals))
            mask_00 = (home_goals == 0) & (away_goals == 0)
            mask_01 = (home_goals == 0) & (away_goals == 1)
            mask_10 = (home_goals == 1) & (away_goals == 0)
            mask_11 = (home_goals == 1) & (away_goals == 1)
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

    def _get_lam_mu(self, home_team: str, away_team: str):
        """Compute expected goals for home and away teams."""
        n = len(self.teams_)
        attack  = self.params_[:n]
        defence = self.params_[n:2*n]
        home_adv = self.params_[-2]

        hi = self._team_idx.get(home_team)
        ai = self._team_idx.get(away_team)
        if hi is None or ai is None:
            raise ValueError(f"Unknown team(s): {home_team}, {away_team}")

        lam = np.exp(attack[hi] - defence[ai] + home_adv)  # home xG
        mu  = np.exp(attack[ai] - defence[hi])              # away xG
        return lam, mu

    def predict(self, home_team: str, away_team: str, max_goals: int = 8) -> dict:
        """
        Returns a dict with probabilities for 1X2, Over/Under 2.5, BTTS.
        """
        lam, mu = self._get_lam_mu(home_team, away_team)
        rho = self.params_[-1]

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
