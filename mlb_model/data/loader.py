import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import pybaseball

CACHE_DIR = Path(__file__).parent / "cache"

def _cache_path(name: str, season: int) -> Path:
    """Helper that returns the parquet cache path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}_{season}.parquet"

def _is_cache_fresh(path: Path, ttl_hours: int = 24) -> bool:
    """Returns True if cache file exists and is younger than ttl_hours."""
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - mtime) < timedelta(hours=ttl_hours)

def load_team_batting(season: int) -> pd.DataFrame:
    """Uses pybaseball.team_batting(season). Returns team-level wRC+, OPS, K%, BB%, HR/FB%."""
    cache_file = _cache_path("team_batting", season)
    if _is_cache_fresh(cache_file):
        return pd.read_parquet(cache_file)
    try:
        df = pybaseball.team_batting(season)
        df.to_parquet(cache_file)
        return df
    except Exception as e:
        print(f"Error loading team batting for {season}: {e}")
        return pd.DataFrame()

def load_team_pitching(season: int) -> pd.DataFrame:
    """Uses pybaseball.team_pitching(season). Returns team ERA, FIP, xFIP, K%, BB%, HR/9."""
    cache_file = _cache_path("team_pitching", season)
    if _is_cache_fresh(cache_file):
        return pd.read_parquet(cache_file)
    try:
        df = pybaseball.team_pitching(season)
        df.to_parquet(cache_file)
        return df
    except Exception as e:
        print(f"Error loading team pitching for {season}: {e}")
        return pd.DataFrame()

def load_starter_game_logs(season: int) -> pd.DataFrame:
    """Uses pybaseball.pitching_stats(season, qual=50)."""
    cache_file = _cache_path("starter_game_logs", season)
    if _is_cache_fresh(cache_file):
        return pd.read_parquet(cache_file)
    try:
        df = pybaseball.pitching_stats(season, qual=50)
        df.to_parquet(cache_file)
        return df
    except Exception as e:
        print(f"Error loading starter game logs for {season}: {e}")
        return pd.DataFrame()

def load_game_logs(season: int) -> pd.DataFrame:
    """Uses pybaseball.schedule_and_record(season, team) for each MLB team to build a complete game-by-game log."""
    cache_file = _cache_path("game_logs", season)
    if _is_cache_fresh(cache_file):
        return pd.read_parquet(cache_file)
    
    try:
        teams = ['ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 'COL', 'DET', 
                 'HOU', 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'OAK', 
                 'PHI', 'PIT', 'SDP', 'SEA', 'SFG', 'STL', 'TBR', 'TEX', 'TOR', 'WSN']
        all_games = []
        for team in teams:
            try:
                team_games = pybaseball.schedule_and_record(season, team)
                team_games['Team'] = team
                all_games.append(team_games)
            except Exception as e:
                print(f"Error loading schedule for {team} in {season}: {e}")
                
        if not all_games:
            return pd.DataFrame()
            
        df = pd.concat(all_games, ignore_index=True)
        # De-duplicate games (each game appears twice, once per team)
        if 'Date' in df.columns and 'Tm' in df.columns and 'Opp' in df.columns:
            df['Team1'] = df[['Tm', 'Opp']].min(axis=1)
            df['Team2'] = df[['Tm', 'Opp']].max(axis=1)
            df = df.drop_duplicates(subset=['Date', 'Team1', 'Team2'])
            df = df.drop(columns=['Team1', 'Team2'])
            
        df.to_parquet(cache_file)
        return df
    except Exception as e:
        print(f"Error loading game logs for {season}: {e}")
        return pd.DataFrame()

def load_park_factors(season: int) -> dict[str, float]:
    """Returns a dict mapping stadium/team name to a park factor float."""
    cache_file = _cache_path("park_factors", season)
    if _is_cache_fresh(cache_file):
        df = pd.read_parquet(cache_file)
        return df.set_index('team')['park_factor'].to_dict()
    
    fallback_pf = {
        'COL': 1.12, 'CIN': 1.07, 'BOS': 1.05, 'LAA': 1.02, 'KCR': 1.01,
        'ATL': 1.01, 'CHW': 1.01, 'BAL': 1.00, 'HOU': 1.00, 'PHI': 1.00,
        'TEX': 1.00, 'TOR': 1.00, 'LAD': 1.00, 'MIL': 0.99, 'MIN': 0.99,
        'PIT': 0.99, 'ARI': 0.99, 'CLE': 0.98, 'SDP': 0.98, 'SFG': 0.98,
        'MIA': 0.98, 'NYY': 0.98, 'CHC': 0.97, 'DET': 0.97, 'TBR': 0.97,
        'WSN': 0.97, 'OAK': 0.96, 'NYM': 0.95, 'STL': 0.95, 'SEA': 0.93
    }
    try:
        df = pd.DataFrame(list(fallback_pf.items()), columns=['team', 'park_factor'])
        df.to_parquet(cache_file)
        return fallback_pf
    except Exception as e:
        print(f"Error loading park factors for {season}: {e}")
        return fallback_pf
