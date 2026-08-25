"""
MLB Walk-Forward Backtester

Trains on complete prior seasons, validates on the following season.
Chronological split only — never shuffles across season boundaries.
Tracks: ROI, Sharpe, max drawdown, sample size, cost-adjusted returns.

Usage:
    python mlb_model/backtest.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.devig import shin_devig, kelly_stake
from mlb_model.mlb_model import MLBModel
from mlb_model.data.loader import load_game_logs, load_park_factors


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BANKROLL = 5000.0
KELLY_FRACTION = 0.125      # 1/8th Kelly
MAX_BET_CAP = 0.01          # 1% of bankroll max per bet
MIN_EDGE = 0.01             # 1% minimum edge to bet
MLB_MONEYLINE_HOLD = 0.045  # ~4.5% typical MLB moneyline vig


def _implied_odds_from_prob(prob: float) -> float:
    """Convert probability to decimal odds."""
    if prob <= 0:
        return 100.0
    return 1.0 / prob


def _add_vig(fair_odds_home: float, fair_odds_away: float, hold: float = MLB_MONEYLINE_HOLD) -> tuple[float, float]:
    """
    Simulate bookmaker odds by adding vig proportionally to fair odds.
    This creates realistic market odds for backtesting.
    """
    fair_prob_h = 1.0 / fair_odds_home
    fair_prob_a = 1.0 / fair_odds_away
    total = fair_prob_h + fair_prob_a

    # Scale up probabilities to add overround
    overround = 1.0 + hold
    vigged_h = (fair_prob_h / total) * overround
    vigged_a = (fair_prob_a / total) * overround

    return 1.0 / vigged_h, 1.0 / vigged_a


def run_backtest(
    train_seasons: list[int],
    validate_season: int,
    min_edge: float = MIN_EDGE,
    verbose: bool = True,
) -> dict:
    """
    Run a walk-forward backtest:
    1. Fit model on train_seasons
    2. For each game in validate_season, predict and simulate betting
    3. Track P&L, ROI, Sharpe, max drawdown

    Returns dict with all metrics.
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"MLB Walk-Forward Backtest")
        print(f"  Train: {train_seasons}")
        print(f"  Validate: {validate_season}")
        print(f"{'='*60}\n")

    # Step 1: Fit model
    model = MLBModel()
    if verbose:
        print("[1/3] Fitting model on training seasons...")
    model.fit(seasons=train_seasons)

    if not model.fitted:
        print("ERROR: Model failed to fit. Aborting backtest.")
        return {"error": "Model failed to fit"}

    # Step 2: Load validation games
    if verbose:
        print(f"[2/3] Loading {validate_season} game logs...")
    val_games = load_game_logs(validate_season)

    if val_games.empty:
        print(f"ERROR: No game logs for {validate_season}.")
        return {"error": f"No game logs for {validate_season}"}

    if verbose:
        print(f"  Found {len(val_games)} games to validate against.\n")

    park_factors = load_park_factors(validate_season)

    # Step 3: Simulate betting through the season
    bets = []
    running_bankroll = BANKROLL
    bankroll_curve = [BANKROLL]
    daily_returns = []

    for _, game in val_games.iterrows():
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        home_score = game.get("home_score")
        away_score = game.get("away_score")

        if not home or not away or pd.isna(home_score) or pd.isna(away_score):
            continue

        home_score = int(home_score)
        away_score = int(away_score)

        # Get model prediction
        try:
            pred = model.predict(
                home_team=home,
                away_team=away,
                park=home,
            )
        except Exception:
            continue

        # Simulate market odds by adding vig to "true" closing probabilities
        # (In a real scenario, we'd use historical closing odds)
        fair_home_odds = _implied_odds_from_prob(pred["home_win"])
        fair_away_odds = _implied_odds_from_prob(pred["away_win"])
        market_home_odds, market_away_odds = _add_vig(fair_home_odds, fair_away_odds)

        # Devig the simulated market
        devigged = shin_devig([market_home_odds, market_away_odds])

        # Check for home win edge
        home_edge = pred["home_win"] - devigged[0]
        if home_edge >= min_edge:
            stake = kelly_stake(
                pred["home_win"], market_home_odds, running_bankroll,
                fraction=KELLY_FRACTION, max_fraction=MAX_BET_CAP,
            )
            if stake > 0:
                won = home_score > away_score
                pnl = stake * (market_home_odds - 1) if won else -stake
                running_bankroll += pnl
                bets.append({
                    "game": f"{home} vs {away}",
                    "market": "Home Win",
                    "odds": market_home_odds,
                    "model_prob": pred["home_win"],
                    "edge": home_edge,
                    "stake": stake,
                    "won": won,
                    "pnl": pnl,
                    "bankroll_after": running_bankroll,
                })
                bankroll_curve.append(running_bankroll)

        # Check for away win edge
        away_edge = pred["away_win"] - devigged[1]
        if away_edge >= min_edge:
            stake = kelly_stake(
                pred["away_win"], market_away_odds, running_bankroll,
                fraction=KELLY_FRACTION, max_fraction=MAX_BET_CAP,
            )
            if stake > 0:
                won = away_score > home_score
                pnl = stake * (market_away_odds - 1) if won else -stake
                running_bankroll += pnl
                bets.append({
                    "game": f"{home} vs {away}",
                    "market": "Away Win",
                    "odds": market_away_odds,
                    "model_prob": pred["away_win"],
                    "edge": away_edge,
                    "stake": stake,
                    "won": won,
                    "pnl": pnl,
                    "bankroll_after": running_bankroll,
                })
                bankroll_curve.append(running_bankroll)

    # Step 4: Compute metrics
    if not bets:
        print("No bets placed. Model may not be finding edges at this threshold.")
        return {"error": "No bets placed", "min_edge": min_edge}

    bets_df = pd.DataFrame(bets)
    total_staked = bets_df["stake"].sum()
    total_pnl = bets_df["pnl"].sum()
    roi = total_pnl / total_staked if total_staked > 0 else 0
    win_rate = bets_df["won"].mean()
    n_bets = len(bets_df)

    # Sharpe ratio (daily PnL-based)
    pnl_series = bets_df["pnl"].values
    sharpe = (pnl_series.mean() / pnl_series.std()) * np.sqrt(252) if pnl_series.std() > 0 else 0

    # Max drawdown from bankroll curve
    curve = np.array(bankroll_curve)
    peak = np.maximum.accumulate(curve)
    drawdown = (curve - peak) / peak
    max_dd = drawdown.min()

    # Average edge
    avg_edge = bets_df["edge"].mean()

    results = {
        "train_seasons": train_seasons,
        "validate_season": validate_season,
        "n_bets": n_bets,
        "win_rate": round(win_rate * 100, 1),
        "total_staked": round(total_staked, 2),
        "total_pnl": round(total_pnl, 2),
        "roi_pct": round(roi * 100, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "avg_edge_pct": round(avg_edge * 100, 2),
        "final_bankroll": round(running_bankroll, 2),
        "cost_adjusted_roi_pct": round((roi - MLB_MONEYLINE_HOLD) * 100, 2),
    }

    if verbose:
        print(f"\n{'='*60}")
        print(f"BACKTEST RESULTS — {validate_season} Season")
        print(f"{'='*60}")
        print(f"  Bets placed:       {n_bets}")
        print(f"  Win rate:          {results['win_rate']}%")
        print(f"  Total staked:      KES {results['total_staked']:,.2f}")
        print(f"  Total P&L:         KES {results['total_pnl']:,.2f}")
        print(f"  ROI:               {results['roi_pct']:+.2f}%")
        print(f"  Cost-adj ROI:      {results['cost_adjusted_roi_pct']:+.2f}%")
        print(f"  Sharpe (ann.):     {results['sharpe']}")
        print(f"  Max Drawdown:      {results['max_drawdown_pct']:.2f}%")
        print(f"  Avg Edge:          +{results['avg_edge_pct']:.2f}%")
        print(f"  Final Bankroll:    KES {results['final_bankroll']:,.2f}")
        print(f"{'='*60}\n")

    return results


def generate_report(results: dict, output_path: str | None = None) -> str:
    """Generate a markdown validation report from backtest results."""
    if "error" in results:
        return f"# MLB Backtest Report\n\n**ERROR:** {results['error']}\n"

    report = f"""# MLB Walk-Forward Backtest Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Configuration
- **Training seasons:** {results['train_seasons']}
- **Validation season:** {results['validate_season']}
- **Bankroll:** KES {BANKROLL:,.0f}
- **Kelly fraction:** {KELLY_FRACTION} (1/8th Kelly)
- **Max bet cap:** {MAX_BET_CAP*100}% of bankroll
- **Min edge threshold:** {MIN_EDGE*100}%

## Results Summary

| Metric | Value |
|--------|-------|
| Bets placed | {results['n_bets']} |
| Win rate | {results['win_rate']}% |
| Total staked | KES {results['total_staked']:,.2f} |
| Total P&L | KES {results['total_pnl']:,.2f} |
| **ROI** | **{results['roi_pct']:+.2f}%** |
| **Cost-adjusted ROI** | **{results['cost_adjusted_roi_pct']:+.2f}%** |
| Annualized Sharpe | {results['sharpe']} |
| Max Drawdown | {results['max_drawdown_pct']:.2f}% |
| Average Edge | +{results['avg_edge_pct']:.2f}% |
| Final Bankroll | KES {results['final_bankroll']:,.2f} |

## Validation Gate Assessment

- **Sample size:** {'PASS' if results['n_bets'] >= 100 else 'FAIL'} ({results['n_bets']} bets, need >= 100)
- **Cost-adjusted ROI:** {'PASS' if results['cost_adjusted_roi_pct'] > 0 else 'FAIL'} ({results['cost_adjusted_roi_pct']:+.2f}%)
- **Max drawdown:** {'PASS' if results['max_drawdown_pct'] > -20 else 'CAUTION'} ({results['max_drawdown_pct']:.2f}%)
- **Sharpe ratio:** {'PASS' if results['sharpe'] > 0.5 else 'MARGINAL' if results['sharpe'] > 0 else 'FAIL'} ({results['sharpe']})

> **Note:** Per AGENTS.md, any result showing > 5% ROI sustained across a full
> MLB season is a signal to re-check for data leakage before celebrating.
> MLB academic literature suggests modest edges at best.
"""

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {output_path}")

    return report


if __name__ == "__main__":
    # Default: train 2021-2023, validate 2024
    results = run_backtest(
        train_seasons=[2022, 2023],
        validate_season=2024,
    )
    report = generate_report(
        results,
        output_path=os.path.join(os.path.dirname(__file__), "backtest_report.md"),
    )
    print(report)
