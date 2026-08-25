from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import numpy as np


@dataclass
class SimulationResult:
    home_xg: float
    away_xg: float
    n_sims: int
    home_goals: np.ndarray
    away_goals: np.ndarray

    @property
    def home_win_pct(self) -> float:
        return float(np.mean(self.home_goals > self.away_goals))

    @property
    def draw_pct(self) -> float:
        return float(np.mean(self.home_goals == self.away_goals))

    @property
    def away_win_pct(self) -> float:
        return float(np.mean(self.home_goals < self.away_goals))

    @property
    def most_likely_scoreline(self) -> tuple[tuple[int, int], float]:
        """Returns ((home_goals, away_goals), probability) for the modal scoreline."""
        pairs = list(zip(self.home_goals.tolist(), self.away_goals.tolist()))
        counts = Counter(pairs)
        top_score, top_count = counts.most_common(1)[0]
        return top_score, top_count / self.n_sims

    def scoreline_table(self, max_goals: int = 5) -> dict[tuple[int, int], float]:
        """Probability table for every scoreline up to max_goals-max_goals."""
        pairs = list(zip(self.home_goals.tolist(), self.away_goals.tolist()))
        counts = Counter(pairs)
        table = {}
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                table[(h, a)] = counts.get((h, a), 0) / self.n_sims
        return table

    def over_under(self, line: float = 2.5) -> dict[str, float]:
        total_goals = self.home_goals + self.away_goals
        return {
            f"over_{line}": float(np.mean(total_goals > line)),
            f"under_{line}": float(np.mean(total_goals < line)),
        }

    def btts(self) -> dict[str, float]:
        """Both teams to score."""
        yes = np.mean((self.home_goals > 0) & (self.away_goals > 0))
        return {"btts_yes": float(yes), "btts_no": float(1 - yes)}

    def summary(self, max_goals: int = 5, top_n_scores: int = 5) -> str:
        score, prob = self.most_likely_scoreline
        table = self.scoreline_table(max_goals=max_goals)
        top_scores = sorted(table.items(), key=lambda kv: kv[1], reverse=True)[:top_n_scores]

        lines = [
            f"Simulated {self.n_sims:,} matches (home xG={self.home_xg}, away xG={self.away_xg})",
            f"  Home win: {self.home_win_pct:.1%}   Draw: {self.draw_pct:.1%}   Away win: {self.away_win_pct:.1%}",
            f"  Most likely scoreline: {score[0]}-{score[1]}  ({prob:.1%} of simulations)",
            f"  Top {top_n_scores} scorelines:",
        ]
        for (h, a), p in top_scores:
            lines.append(f"    {h}-{a}: {p:.1%}")
        return "\n".join(lines)


def simulate_match(
    home_xg: float,
    away_xg: float,
    n_sims: int = 50_000,
    dixon_coles_rho: float | None = None,
    seed: int | None = None,
) -> SimulationResult:
    rng = np.random.default_rng(seed)

    home_goals = rng.poisson(lam=home_xg, size=n_sims)
    away_goals = rng.poisson(lam=away_xg, size=n_sims)

    if dixon_coles_rho is not None:
        home_goals, away_goals = _apply_dixon_coles_adjustment(
            home_goals, away_goals, home_xg, away_xg, dixon_coles_rho, rng
        )

    return SimulationResult(
        home_xg=home_xg,
        away_xg=away_xg,
        n_sims=n_sims,
        home_goals=home_goals,
        away_goals=away_goals,
    )


def _apply_dixon_coles_adjustment(
    home_goals: np.ndarray,
    away_goals: np.ndarray,
    home_xg: float,
    away_xg: float,
    rho: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    def tau(x: int, y: int) -> float:
        if x == 0 and y == 0:
            return 1 - (home_xg * away_xg * rho)
        elif x == 0 and y == 1:
            return 1 + (home_xg * rho)
        elif x == 1 and y == 0:
            return 1 + (away_xg * rho)
        elif x == 1 and y == 1:
            return 1 - rho
        return 1.0

    low_score_mask = (home_goals <= 1) & (away_goals <= 1)
    idx = np.where(low_score_mask)[0]
    for i in idx:
        h, a = int(home_goals[i]), int(away_goals[i])
        weight = max(tau(h, a), 0.0)
        if rng.random() > weight:
            while True:
                new_h = rng.poisson(lam=home_xg)
                new_a = rng.poisson(lam=away_xg)
                if not (new_h <= 1 and new_a <= 1):
                    home_goals[i], away_goals[i] = new_h, new_a
                    break
                if rng.random() <= max(tau(new_h, new_a), 0.0):
                    home_goals[i], away_goals[i] = new_h, new_a
                    break
    return home_goals, away_goals


if __name__ == "__main__":
    result = simulate_match(home_xg=1.8, away_xg=0.7, n_sims=50_000, seed=42)
    print(result.summary())
    print()
    print("Over/Under 2.5:", result.over_under(2.5))
    print("BTTS:", result.btts())
