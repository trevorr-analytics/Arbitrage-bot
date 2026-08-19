"""
Devigging (overround removal) using Shin's method.
Converts raw bookmaker decimal odds into true implied probabilities
by modelling the bookmaker's vig as an insider-information allowance.
"""
import numpy as np
from scipy.optimize import brentq


def shin_devig(odds: list[float]) -> list[float]:
    """
    Apply Shin's (1993) devigging to a set of decimal odds.
    Returns a list of devigged true probabilities (sum ≈ 1.0).

    Shin's model: the bookmaker prices as if a fraction `z` of bettors
    are insiders who always know the outcome. Solving for z gives us
    better-calibrated probabilities than naive proportional devigging,
    especially for near-even-money markets.
    """
    raw_probs = [1.0 / o for o in odds]
    overround = sum(raw_probs)

    # Degenerate case — already sum to 1
    if abs(overround - 1.0) < 1e-6:
        return raw_probs

    n = len(odds)

    def equation(z):
        # Shin's equation: sum over i of sqrt(z^2 + 4*(1-z)*q_i^2/overround^2) - z - 2*(1-z)/overround = 0
        total = 0.0
        for q in raw_probs:
            inner = z**2 + 4.0 * (1.0 - z) * (q / overround) ** 2
            total += np.sqrt(max(inner, 0.0))
        return total - z - 2.0 * (1.0 - z)

    try:
        z = brentq(equation, 0.0, 0.5, xtol=1e-8)
    except ValueError:
        # Fallback to proportional devigging
        return [p / overround for p in raw_probs]

    true_probs = []
    for q in raw_probs:
        inner = z**2 + 4.0 * (1.0 - z) * (q / overround) ** 2
        p = (np.sqrt(max(inner, 0.0)) - z) / (2.0 * (1.0 - z))
        true_probs.append(p)

    # Normalise to ensure exact sum = 1.0
    total = sum(true_probs)
    return [p / total for p in true_probs]


def fair_odds(prob: float) -> float:
    """Convert true probability to fair decimal odds (no vig)."""
    if prob <= 0:
        return float("inf")
    return round(1.0 / prob, 3)


def kelly_stake(
    model_prob: float,
    decimal_odds: float,
    bankroll: float,
    fraction: float = 0.25,
    max_fraction: float = 0.02,
) -> float:
    """
    Fractional Kelly stake in currency units.
    Returns 0 if Kelly is negative (no edge).
    """
    b = decimal_odds - 1.0
    q = 1.0 - model_prob
    raw_kelly = (b * model_prob - q) / b
    if raw_kelly <= 0:
        return 0.0
    stake_frac = min(raw_kelly * fraction, max_fraction)
    return round(bankroll * stake_frac, 2)


def edge_pct(model_prob: float, devigged_implied_prob: float) -> float:
    """Edge = model probability − devigged market implied probability (as %)."""
    return round((model_prob - devigged_implied_prob) * 100, 2)
