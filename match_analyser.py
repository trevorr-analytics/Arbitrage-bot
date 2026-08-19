"""
Match Analyser Dashboard
========================
Loads a list of fixtures with their bookmaker odds (1X2, Over/Under 2.5, BTTS),
trains the Dixon-Coles model on historical data, and outputs a comparison table:

  Match | Market | Bookie Odds | Implied Prob | Devigged Prob | Model Prob | Edge% | Kelly Stake

Usage:
  uv run python match_analyser.py --league ALL
  uv run python match_analyser.py --league EPL
  uv run python match_analyser.py --league Bundesliga --fixtures fixtures.csv
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
from typing import Optional

# Ensure standard output doesn't crash on Windows with emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))
from dixon_coles import DixonColesModel, load_league_data
from devig import shin_devig, fair_odds, kelly_stake, edge_pct
from odds_api import fetch_live_odds

BANKROLL_KES = 5000.0
MIN_EDGE_PCT = 2.0  # Only flag bets with edge > 2%

def safe_devig(odds_list: list[float]) -> list[float]:
    """Gracefully handle missing markets (0.0 odds)"""
    if any(o <= 1.0 for o in odds_list):
        return [0.0] * len(odds_list)
    try:
        return shin_devig(odds_list)
    except Exception:
        return [0.0] * len(odds_list)

# Sample upcoming fixtures (replace with real Betgr8 odds when available)

SAMPLE_FIXTURES = {
    "EPL": [
        ("Arsenal",          "Chelsea",         2.10, 3.40, 3.60, 1.85, 1.95, 1.80, 2.00),
        ("Liverpool",        "Man City",        2.50, 3.25, 2.90, 1.72, 2.10, 1.75, 2.05),
        ("Man United",       "Tottenham",       2.30, 3.20, 3.20, 1.90, 1.90, 1.85, 1.95),
        ("Newcastle",        "Aston Villa",     2.20, 3.30, 3.40, 1.95, 1.85, 1.90, 1.90),
        ("Brighton",         "Wolves",          1.95, 3.50, 3.90, 2.00, 1.80, 1.95, 1.85),
    ],
    "Bundesliga": [
        ("Bayern Munich",    "Dortmund",        1.60, 4.00, 5.50, 1.65, 2.25, 1.70, 2.15),
        ("Leverkusen",       "RB Leipzig",      2.10, 3.30, 3.60, 1.80, 2.00, 1.85, 1.95),
        ("Stuttgart",        "Frankfurt",       2.40, 3.20, 3.00, 1.90, 1.90, 1.85, 1.95),
    ],
    "LaLiga": [
        ("Real Madrid",      "Barcelona",       2.30, 3.40, 3.10, 1.75, 2.05, 1.80, 2.00),
        ("Atletico Madrid",  "Sevilla",         1.80, 3.60, 4.20, 2.05, 1.75, 1.90, 1.90),
        ("Athletic Bilbao",  "Real Sociedad",   2.40, 3.20, 3.00, 1.90, 1.90, 1.85, 1.95),
    ],
    "SerieA": [
        ("Juventus",         "AC Milan",        2.20, 3.20, 3.50, 1.95, 1.85, 1.90, 1.90),
        ("Inter",            "Napoli",          2.00, 3.40, 3.80, 1.85, 1.95, 1.80, 2.00),
    ],
    "Ligue1": [
        ("PSG",              "Marseille",       1.65, 4.20, 5.00, 1.55, 2.45, 1.70, 2.10),
        ("Monaco",           "Lyon",            2.10, 3.50, 3.40, 1.75, 2.05, 1.65, 2.20),
    ],
    "Eredivisie": [
        ("Ajax",             "PSV Eindhoven",   2.60, 3.50, 2.50, 1.55, 2.45, 1.50, 2.50),
        ("Feyenoord",        "AZ Alkmaar",      1.80, 3.80, 4.00, 1.65, 2.20, 1.75, 2.05),
    ]
}


def load_or_train_model(league: str, half_life: float = 90.0) -> DixonColesModel:
    """Load historical data and fit the Dixon-Coles model."""
    print(f"\n[Model] Loading {league} historical data...", end=" ", flush=True)
    try:
        data = load_league_data(league)
        # Use only most recent 3 seasons for fitting (recency matters)
        cutoff = data["Date"].max() - pd.Timedelta(days=3 * 365)
        data = data[data["Date"] >= cutoff]
        print(f"OK ({len(data)} matches)")
    except FileNotFoundError:
        print(f"No data found. Run data_downloader.py first.")
        return None

    print(f"[Model] Fitting Dixon-Coles model...", end=" ", flush=True)
    model = DixonColesModel(half_life_days=half_life)
    model.fit(data, league_name=league)
    print("Done.")
    return model


def analyse_fixture(
    league: str,
    home: str,
    away: str,
    odds_h: float,
    odds_d: float,
    odds_a: float,
    odds_over25: float,
    odds_under25: float,
    odds_btts_yes: float,
    odds_btts_no: float,
    model: Optional[DixonColesModel],
) -> list[dict]:
    """
    Analyse one fixture across all three markets.
    Returns rows for the display table.
    """
    rows = []

    # --- Devig the bookmaker odds ---
    dv_1x2 = safe_devig([odds_h, odds_d, odds_a])
    dv_h, dv_d, dv_a = dv_1x2
    dv_ou = safe_devig([odds_over25, odds_under25])
    dv_over, dv_under = dv_ou
    dv_btts = safe_devig([odds_btts_yes, odds_btts_no])
    dv_btts_yes, dv_btts_no = dv_btts

    # --- Model probabilities ---
    if model is not None:
        known = model.known_teams()
        h_match = _fuzzy_team(home, known)
        a_match = _fuzzy_team(away, known)

        if h_match and a_match:
            pred = model.predict(h_match, a_match)
            mp_h    = pred["home_win"]
            mp_d    = pred["draw"]
            mp_a    = pred["away_win"]
            mp_over = pred["over_2_5"]
            mp_under = pred["under_2_5"]
            mp_btts_yes = pred["btts_yes"]
            mp_btts_no  = pred["btts_no"]
            home_xg = pred["home_xg"]
            away_xg = pred["away_xg"]
        else:
            mp_h = mp_d = mp_a = mp_over = mp_under = mp_btts_yes = mp_btts_no = None
            home_xg = away_xg = None
    else:
        mp_h = mp_d = mp_a = mp_over = mp_under = mp_btts_yes = mp_btts_no = None
        home_xg = away_xg = None

    # --- Build rows ---
    markets = [
        ("Home Win",     odds_h,       dv_h,         mp_h),
        ("Draw",         odds_d,       dv_d,         mp_d),
        ("Away Win",     odds_a,       dv_a,         mp_a),
        ("Over 2.5",     odds_over25,  dv_over,      mp_over),
        ("Under 2.5",    odds_under25, dv_under,     mp_under),
        ("BTTS Yes",     odds_btts_yes, dv_btts_yes, mp_btts_yes),
        ("BTTS No",      odds_btts_no,  dv_btts_no,  mp_btts_no),
    ]

    for market, bookie_odds, dv_prob, model_prob in markets:
        if bookie_odds <= 1.0:
            continue  # Skip missing markets

        if model_prob is None or dv_prob == 0.0:
            edge = None
            kelly = None
            fair = fair_odds(dv_prob) if dv_prob > 0 else "N/A"
        else:
            edge = edge_pct(model_prob, dv_prob)
            kelly = kelly_stake(model_prob, bookie_odds, BANKROLL_KES) if edge > MIN_EDGE_PCT else 0.0
            fair = fair_odds(model_prob)

        rows.append({
            "League": league,
            "Home": home,
            "Away": away,
            "Market": market,
            "Bookie Odds": bookie_odds,
            "Implied Prob": f"{(1/bookie_odds)*100:.1f}%" if bookie_odds > 1 else "N/A",
            "Devigged Prob": f"{dv_prob*100:.1f}%" if dv_prob > 0 else "N/A",
            "Model Prob": f"{model_prob*100:.1f}%" if model_prob is not None else "N/A",
            "Fair Odds": fair if fair != "N/A" else "N/A",
            "Edge %": f"+{edge:.1f}%" if (edge is not None and edge > 0) else (f"{edge:.1f}%" if edge is not None else "N/A"),
            "Kelly Stake (KES)": kelly if kelly else "-",
            "xG": f"{home_xg:.2f} - {away_xg:.2f}" if home_xg else "N/A",
            "FLAG": "VALUE" if (edge is not None and edge >= MIN_EDGE_PCT) else "",
        })

    return rows


def _fuzzy_team(name: str, known: list) -> Optional[str]:
    name_lower = name.lower()
    for k in known:
        if k.lower() == name_lower:
            return k
    for k in known:
        if name_lower in k.lower() or k.lower() in name_lower:
            return k
    name_tokens = set(name_lower.split())
    for k in known:
        k_tokens = set(k.lower().split())
        if name_tokens & k_tokens:
            return k
    return None


def print_table(rows: list[dict]):
    if not rows:
        return

    value_bets = [r for r in rows if r["FLAG"] == "VALUE"]

    print(f"\n{'='*115}")
    print(f"  Multi-League Match Analysis Dashboard")
    print(f"  Bankroll: KES {BANKROLL_KES:,.0f}   Min Edge: {MIN_EDGE_PCT}%   Staking: Quarter-Kelly, 2% cap = max KES {BANKROLL_KES*0.02:.0f}/bet")
    print(f"{'='*115}")

    current_league = None
    current_match = None
    for r in rows:
        if r['League'] != current_league:
            current_league = r['League']
            print(f"\n{'*'*40} {current_league.upper()} {'*'*40}")

        match_header = f"{r['Home']} vs {r['Away']}"
        if match_header != current_match:
            current_match = match_header
            print(f"\n  {match_header}  (xG: {r['xG']})")
            print(f"  {'Market':<14} {'Bookie':>8} {'Implied':>9} {'Devigged':>10} {'Model':>8} {'Fair':>8} {'Edge':>8} {'Kelly KES':>10}  ")
            print(f"  {'-'*100}")

        flag = "  <- VALUE BET" if r["FLAG"] else ""
        print(
            f"  {r['Market']:<14} "
            f"{r['Bookie Odds']:>8.2f} "
            f"{r['Implied Prob']:>9} "
            f"{r['Devigged Prob']:>10} "
            f"{r['Model Prob']:>8} "
            f"{str(r['Fair Odds']):>8} "
            f"{r['Edge %']:>8} "
            f"{str(r['Kelly Stake (KES)']):>10}"
            f"{flag}"
        )

    print(f"\n{'='*115}")
    print(f"  VALUE BETS FOUND ACROSS ALL LEAGUES: {len(value_bets)}")
    for vb in value_bets:
        print(f"  **  [{vb['League']}] {vb['Home']} vs {vb['Away']} -- {vb['Market']} @ {vb['Bookie Odds']}  "
              f"(Model: {vb['Model Prob']}, Edge: {vb['Edge %']}, Stake: KES {vb['Kelly Stake (KES)']})")
    print(f"{'='*115}\n")


def run(league: str, fixtures_csv: Optional[str] = None, live: bool = False):
    leagues_to_run = list(SAMPLE_FIXTURES.keys()) if league == "ALL" else [league]
    
    all_rows = []
    for lg in leagues_to_run:
        model = load_or_train_model(lg)
        
        if live:
            fixture_list = fetch_live_odds(lg)
            if not fixture_list:
                print(f"[Fixtures] No live fixtures found for {lg} or error occurred.")
                continue
        elif fixtures_csv and os.path.exists(fixtures_csv) and league != "ALL":
            df = pd.read_csv(fixtures_csv)
            fixture_list = [tuple(row) for _, row in df.iterrows()]
        else:
            if league == "ALL":
                print(f"[Fixtures] Using sample fixtures for {lg}.")
            fixture_list = SAMPLE_FIXTURES.get(lg, [])
            if not fixture_list:
                continue
            
        for fixture in fixture_list:
            rows = analyse_fixture(lg, *fixture, model=model)
            all_rows.extend(rows)

    if league != "ALL" and not fixtures_csv and not live:
        print(f"  -> To use real Betgr8 odds: create a CSV with columns:")
        print(f"    home,away,odds_h,odds_d,odds_a,odds_over25,odds_under25,odds_btts_yes,odds_btts_no\n")
    elif live:
        print(f"\n  -> Odds sourced live from The Odds API (best available across bookmakers)\n")

    print_table(all_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Match Analysis Dashboard")
    parser.add_argument("--league", default="ALL",
                        choices=["ALL", "EPL", "Bundesliga", "LaLiga", "SerieA", "Ligue1", "Eredivisie"],
                        help="League to analyse (or ALL)")
    parser.add_argument("--fixtures", default=None,
                        help="Path to a CSV file with fixture odds (optional, applies if specific league chosen)")
    parser.add_argument("--live", action="store_true",
                        help="Fetch live upcoming fixtures and odds from The Odds API (requires ODDS_API_KEY)")
    args = parser.parse_args()

    run(args.league, args.fixtures, args.live)
