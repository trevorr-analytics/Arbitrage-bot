import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def compute_overdispersion(game_logs: pd.DataFrame) -> float:
    """
    Compute Negative Binomial r parameter from historical run data.
    Uses method-of-moments: r = mean^2 / (variance - mean).
    Returns default 6.0 if insufficient data or variance <= mean.
    """
    default_r = 6.0
    
    if game_logs is None or game_logs.empty or "runs" not in game_logs.columns:
        return default_r
        
    runs = game_logs["runs"].dropna()
    if len(runs) < 30:
        return default_r
        
    mean = runs.mean()
    variance = runs.var()
    
    if variance <= mean or mean == 0:
        return default_r
        
    r = (mean ** 2) / (variance - mean)
    return float(r)

def get_bullpen_fatigue_factor(team: str, game_date: str, game_logs: pd.DataFrame) -> float:
    """
    Returns a multiplier (1.0 = normal, >1.0 = tired bullpen allows more runs).
    Checks how many games the team played in the prior 3 days.
    If 3+ games in 3 days, return 1.08 (tired bullpen).
    If back-to-back day games, return 1.05.
    Otherwise return 1.0.
    """
    if game_logs is None or game_logs.empty:
        return 1.0
        
    if isinstance(game_date, str):
        try:
            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
        except ValueError:
            return 1.0
    else:
        date_obj = game_date
        
    # Assume game_logs has 'team', 'date', and optionally 'day_night' ('D' or 'N')
    if 'team' not in game_logs.columns or 'date' not in game_logs.columns:
        return 1.0
        
    team_logs = game_logs[game_logs['team'] == team].copy()
    if team_logs.empty:
        return 1.0
        
    team_logs['date'] = pd.to_datetime(team_logs['date'])
    
    three_days_ago = date_obj - timedelta(days=3)
    recent_games = team_logs[(team_logs['date'] >= three_days_ago) & (team_logs['date'] < date_obj)]
    
    # 3+ games in the last 3 days
    if len(recent_games) >= 3:
        return 1.08
        
    # Back-to-back day games
    if len(recent_games) >= 2 and 'day_night' in recent_games.columns:
        recent_games = recent_games.sort_values('date')
        last_two = recent_games.tail(2)
        # Check if consecutive days
        if (last_two.iloc[-1]['date'] - last_two.iloc[-2]['date']).days == 1:
            if all(last_two['day_night'].astype(str).str.upper() == 'D'):
                return 1.05
                
    return 1.0

def compute_matchup_features(
    home_team: str,
    away_team: str,
    home_starter_name: str | None,
    away_starter_name: str | None,
    park_factors: dict[str, float],
    team_batting: pd.DataFrame,
    team_pitching: pd.DataFrame,
    starter_stats: pd.DataFrame,
    game_logs: pd.DataFrame,
    weather: dict | None = None,
) -> dict:
    """
    Computes MLB feature engineering final vector for simulation.
    
    Returns dict with keys:
    - home_run_exp: float (expected runs for home team)
    - away_run_exp: float (expected runs for away team)
    - overdispersion_r: float (Negative Binomial shape parameter)
    - home_starter_fip: float or None
    - away_starter_fip: float or None
    - park_factor: float
    - weather_adj: float (1.0 = no adjustment)
    """
    # Base Constants
    LEAGUE_AVG_RUNS = 4.5
    LEAGUE_AVG_FIP = 4.0
    
    def get_team_stat(df: pd.DataFrame, team: str, col: str, default: float) -> float:
        if df is None or df.empty or 'team' not in df.columns or col not in df.columns:
            return default
        vals = df.loc[df['team'] == team, col].values
        return float(vals[0]) if len(vals) > 0 else default
        
    def get_starter_stat(df: pd.DataFrame, starter: str | None, col: str, default: float) -> float | None:
        if not starter or df is None or df.empty or 'player_name' not in df.columns or col not in df.columns:
            return None
        vals = df.loc[df['player_name'] == starter, col].values
        return float(vals[0]) if len(vals) > 0 else None

    # 1. Base run rate initialized
    home_base_runs = LEAGUE_AVG_RUNS
    away_base_runs = LEAGUE_AVG_RUNS
    
    # 2. Team batting adjustment (wRC+ relative to 100)
    home_wrc_plus = get_team_stat(team_batting, home_team, 'wRC+', 100.0)
    away_wrc_plus = get_team_stat(team_batting, away_team, 'wRC+', 100.0)
    
    home_batting_adj = home_wrc_plus / 100.0
    away_batting_adj = away_wrc_plus / 100.0
    
    # 3. Opposing pitching adjustment & 4. Starter adjustment
    home_team_fip = get_team_stat(team_pitching, home_team, 'FIP', LEAGUE_AVG_FIP)
    away_team_fip = get_team_stat(team_pitching, away_team, 'FIP', LEAGUE_AVG_FIP)
    
    # Away starter faces Home lineup
    away_starter_fip = get_starter_stat(starter_stats, away_starter_name, 'FIP', None)
    if away_starter_fip is not None:
        effective_away_fip = (0.60 * away_starter_fip) + (0.40 * away_team_fip)
    else:
        effective_away_fip = away_team_fip
        
    home_pitching_adj = effective_away_fip / LEAGUE_AVG_FIP
    
    # Home starter faces Away lineup
    home_starter_fip = get_starter_stat(starter_stats, home_starter_name, 'FIP', None)
    if home_starter_fip is not None:
        effective_home_fip = (0.60 * home_starter_fip) + (0.40 * home_team_fip)
    else:
        effective_home_fip = home_team_fip
        
    away_pitching_adj = effective_home_fip / LEAGUE_AVG_FIP
    
    # 5. Park factor
    park_factor = park_factors.get(home_team, 1.0)
    
    # 6. Weather adjustment
    weather_adj = 1.0
    if weather:
        roof = weather.get('roof', '').lower()
        wind_speed = weather.get('wind_speed', 0.0)
        wind_direction = weather.get('wind_direction', '').lower()
        
        is_dome = 'dome' in roof or 'closed' in roof
        
        if not is_dome:
            if wind_speed > 15:
                if 'out' in wind_direction:
                    weather_adj = 1.05
                elif 'in' in wind_direction:
                    weather_adj = 0.95
                    
    # Calculate preliminary runs
    home_run_exp = home_base_runs * home_batting_adj * home_pitching_adj * park_factor * weather_adj
    away_run_exp = away_base_runs * away_batting_adj * away_pitching_adj * park_factor * weather_adj
    
    # 7. Home advantage
    home_run_exp += 0.25
    
    # 8. Overdispersion parameter
    overdispersion_r = compute_overdispersion(game_logs)
    
    return {
        "home_run_exp": round(home_run_exp, 4),
        "away_run_exp": round(away_run_exp, 4),
        "overdispersion_r": round(overdispersion_r, 4),
        "home_starter_fip": home_starter_fip,
        "away_starter_fip": away_starter_fip,
        "park_factor": park_factor,
        "weather_adj": weather_adj
    }
