"""
MLB odds scanner — pulls live moneyline + totals odds from The Odds API,
devigs them via Shin's method, compares against the MLBModel's predicted
probabilities, and returns +EV legs in the same JSON format used by
the soccer/basketball accumulator builder.

Uses zero additional API keys beyond the existing OddsAPI pool.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

# Add parent to path so we can import sibling packages
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.devig import shin_devig, kelly_stake, edge_pct
from mlb_model.mlb_model import MLBModel


# ---------------------------------------------------------------------------
# Odds API interaction (reuses the existing odds_api.py caching layer)
# ---------------------------------------------------------------------------

def fetch_mlb_odds(api_keys: list[str]) -> list[dict]:
    """
    Fetch live MLB odds from The Odds API.
    Tries each key in rotation until one succeeds.
    Returns raw JSON list of events with h2h + totals markets.
    """
    import requests

    sport = "baseball_mlb"
    regions = "us,eu,uk"
    markets = "h2h,totals"

    for key in api_keys:
        url = (
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
            f"?apiKey={key}&regions={regions}&markets={markets}"
            f"&oddsFormat=decimal&dateFormat=iso"
        )
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                # Key exhausted, try next
                continue
        except requests.RequestException:
            continue
    return []


def _best_odds(bookmakers: list[dict], market: str) -> dict | None:
    """
    Find the best (highest) odds across all bookmakers for a given market.
    Returns dict with keys: odds, bookmaker, or None if market not found.
    """
    best = None
    for bk in bookmakers:
        for mkt in bk.get("markets", []):
            if mkt["key"] != market:
                continue
            for outcome in mkt.get("outcomes", []):
                price = outcome.get("price", 0)
                if best is None or price > best["odds"]:
                    best = {
                        "odds": price,
                        "bookmaker": bk.get("title", "Unknown"),
                        "name": outcome.get("name", ""),
                        "point": outcome.get("point"),
                    }
    return best


def scan_mlb_edges(
    model: MLBModel,
    api_keys: list[str],
    min_edge: float = 0.01,
    bankroll: float = 5000.0,
    kelly_fraction: float = 0.125,
    max_bet_cap: float = 0.01,
) -> list[dict]:
    """
    Scan all live MLB games for +EV betting opportunities.

    Returns a list of leg dicts compatible with acca_tracker.json format:
    {
        "league": "MLB",
        "home": str,
        "away": str,
        "market": str,
        "odds": float,
        "model_prob": float,
        "edge": float,
        "stake": float,
        "status": "PENDING",
        "date": str (ISO),
        "bookmaker": str,
    }
    """
    events = fetch_mlb_odds(api_keys)
    if not events:
        print("[MLB Scanner] No odds data available.")
        return []

    legs = []
    for event in events:
        home = event.get("home_team", "")
        away = event.get("away_team", "")
        commence = event.get("commence_time", "")
        bookmakers = event.get("bookmakers", [])

        if not home or not away or not bookmakers:
            continue

        # Get model prediction (starter info not available from odds API,
        # so we pass None — model will use team averages)
        try:
            pred = model.predict(
                home_team=home,
                away_team=away,
                home_starter=None,
                away_starter=None,
                park=home,  # Use home team as park proxy
            )
        except Exception as e:
            print(f"[MLB Scanner] Prediction failed for {home} vs {away}: {e}")
            continue

        # --- Moneyline (h2h) market ---
        home_best = None
        away_best = None
        for bk in bookmakers:
            for mkt in bk.get("markets", []):
                if mkt["key"] != "h2h":
                    continue
                for outcome in mkt.get("outcomes", []):
                    price = outcome.get("price", 0)
                    name = outcome.get("name", "")
                    if name == home and (home_best is None or price > home_best["odds"]):
                        home_best = {"odds": price, "bookmaker": bk.get("title", "")}
                    elif name == away and (away_best is None or price > away_best["odds"]):
                        away_best = {"odds": price, "bookmaker": bk.get("title", "")}

        if home_best and away_best:
            # Devig the moneyline pair
            devigged = shin_devig([home_best["odds"], away_best["odds"]])

            # Home win edge
            home_edge = pred["home_win"] - devigged[0]
            if home_edge >= min_edge:
                stake = kelly_stake(
                    pred["home_win"], home_best["odds"], bankroll,
                    fraction=kelly_fraction, max_fraction=max_bet_cap,
                )
                legs.append({
                    "league": "MLB",
                    "home": home,
                    "away": away,
                    "market": "Home Win",
                    "odds": home_best["odds"],
                    "devig_prob": devigged[0],
                    "model_prob": pred["home_win"],
                    "edge": home_edge,
                    "stake": stake,
                    "status": "PENDING",
                    "date": commence,
                    "bookmaker": home_best["bookmaker"],
                })

            # Away win edge
            away_edge = pred["away_win"] - devigged[1]
            if away_edge >= min_edge:
                stake = kelly_stake(
                    pred["away_win"], away_best["odds"], bankroll,
                    fraction=kelly_fraction, max_fraction=max_bet_cap,
                )
                legs.append({
                    "league": "MLB",
                    "home": home,
                    "away": away,
                    "market": "Away Win",
                    "odds": away_best["odds"],
                    "devig_prob": devigged[1],
                    "model_prob": pred["away_win"],
                    "edge": away_edge,
                    "stake": stake,
                    "status": "PENDING",
                    "date": commence,
                    "bookmaker": away_best["bookmaker"],
                })

        # --- Totals (over/under) market ---
        for bk in bookmakers:
            for mkt in bk.get("markets", []):
                if mkt["key"] != "totals":
                    continue
                over_outcome = None
                under_outcome = None
                for outcome in mkt.get("outcomes", []):
                    if outcome.get("name") == "Over":
                        over_outcome = outcome
                    elif outcome.get("name") == "Under":
                        under_outcome = outcome

                if over_outcome and under_outcome:
                    line = over_outcome.get("point", 8.5)
                    over_odds = over_outcome.get("price", 1.91)
                    under_odds = under_outcome.get("price", 1.91)

                    devigged = shin_devig([over_odds, under_odds])

                    # Get model's over/under for this line
                    ou = pred.get("over_under", {})
                    over_key = f"over_{line}"
                    under_key = f"under_{line}"
                    model_over = ou.get(over_key, 0.5)
                    model_under = ou.get(under_key, 0.5)

                    over_edge = model_over - devigged[0]
                    if over_edge >= min_edge:
                        stake = kelly_stake(
                            model_over, over_odds, bankroll,
                            fraction=kelly_fraction, max_fraction=max_bet_cap,
                        )
                        legs.append({
                            "league": "MLB",
                            "home": home,
                            "away": away,
                            "market": f"Over {line}",
                            "odds": over_odds,
                            "devig_prob": devigged[0],
                            "model_prob": model_over,
                            "edge": over_edge,
                            "stake": stake,
                            "status": "PENDING",
                            "date": commence,
                            "bookmaker": bk.get("title", ""),
                        })

                    under_edge = model_under - devigged[1]
                    if under_edge >= min_edge:
                        stake = kelly_stake(
                            model_under, under_odds, bankroll,
                            fraction=kelly_fraction, max_fraction=max_bet_cap,
                        )
                        legs.append({
                            "league": "MLB",
                            "home": home,
                            "away": away,
                            "market": f"Under {line}",
                            "odds": under_odds,
                            "devig_prob": devigged[1],
                            "model_prob": model_under,
                            "edge": under_edge,
                            "stake": stake,
                            "status": "PENDING",
                            "date": commence,
                            "bookmaker": bk.get("title", ""),
                        })

    print(f"[MLB Scanner] Found {len(legs)} +EV legs across {len(events)} games.")
    return legs


if __name__ == "__main__":
    # Quick test — requires API keys
    keys = [
        "017cbc1f3724942ba358b77a4b1095fe",
        "2dd91edd9c74fda2e0df435129777d4c",
        "0ecab0bb21f55f88ce50c67b38478c0d",
    ]
    model = MLBModel()
    model.fit(seasons=[2023, 2024])
    edges = scan_mlb_edges(model, keys)
    for leg in edges:
        print(f"  {leg['home']} vs {leg['away']}: {leg['market']} @ {leg['odds']} (edge: +{leg['edge']*100:.1f}%)")
