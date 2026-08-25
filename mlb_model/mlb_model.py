from __future__ import annotations

from typing import Any

from core.simulation import simulate_match
from mlb_model import features


class MLBModel:
    def __init__(self):
        self.team_batting = None
        self.team_pitching = None
        self.starter_stats = None
        self.game_logs = None
        self.park_factors = None
        self.overdispersion_r = 6.0
        self.fitted = False
    
    def fit(self, seasons: list[int]):
        """Load and aggregate data for the given training seasons.
        Compute the global overdispersion parameter from game logs."""
        pass
    
    def predict(self, home_team: str, away_team: str,
                home_starter: str | None = None,
                away_starter: str | None = None,
                park: str | None = None,
                weather: dict | None = None,
                n_sims: int = 50_000) -> dict[str, Any]:
        """Returns:
        - home_win: float (probability)
        - away_win: float (probability)  
        - home_run_exp: float
        - away_run_exp: float
        - over_under: dict with lines 7.5, 8.5, 9.5
        - top_scores: list of ((h, a), prob) top 5 most likely scores
        - overdispersion_r: float
        """
        home_xg, away_xg = features.compute_matchup_features(
            home_team=home_team,
            away_team=away_team,
            home_starter=home_starter,
            away_starter=away_starter,
            park=park,
            weather=weather,
            model=self
        )
        
        sim_result = simulate_match(
            home_xg=home_xg,
            away_xg=away_xg,
            n_sims=n_sims,
            distribution='negative_binomial',
            overdispersion=self.overdispersion_r,
            resolve_ties=True
        )
        
        over_under_dict = {
            7.5: sim_result.over_under(7.5),
            8.5: sim_result.over_under(8.5),
            9.5: sim_result.over_under(9.5),
        }
        
        score_table = sim_result.scoreline_table(max_goals=15)
        top_scores = sorted(score_table.items(), key=lambda kv: kv[1], reverse=True)[:5]
        
        return {
            "home_win": sim_result.home_win_pct,
            "away_win": sim_result.away_win_pct,
            "home_run_exp": home_xg,
            "away_run_exp": away_xg,
            "over_under": over_under_dict,
            "top_scores": top_scores,
            "overdispersion_r": self.overdispersion_r
        }
