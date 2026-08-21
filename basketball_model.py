import math
import pandas as pd
import numpy as np
import scipy.stats as st

class BasketballModel:
    """
    Player-level Elo Engine for Basketball.
    Supports NBA, EuroLeague, NCAAB, and other secondary leagues.
    
    Instead of hardcoded team ratings, this model tracks individual player Elo.
    A team's game rating is the minutes-weighted average of its active roster's Elo.
    After a match, the Elo update is distributed among players based on their court time
    and individual Box Plus/Minus (or simply minutes played if BPM isn't available).
    """
    def __init__(self, home_advantage_elo=65, base_elo=1500.0, k_factor=20.0):
        self.player_ratings = {} # dict[player_id -> elo]
        self.team_rosters = {}   # dict[team -> dict[player_id -> expected_minutes]]
        self.home_advantage = home_advantage_elo
        self.base_elo = base_elo
        self.k_factor = k_factor
        
        # We also need pace and offensive/defensive ratings for Totals (O/U)
        self.team_stats = {} # dict[team -> {"off_rtg": 110, "def_rtg": 110, "pace": 98}]
        
    def known_teams(self):
        return []
    def get_player_elo(self, player_name: str) -> float:
        return self.player_ratings.get(player_name, self.base_elo)
        
    def set_active_roster(self, team: str, roster_minutes: dict):
        """
        roster_minutes: dict mapping player_name to expected minutes (should sum to ~240 for NBA, ~200 for FIBA)
        """
        self.team_rosters[team] = roster_minutes
        
    def get_team_elo(self, team: str) -> float:
        """
        Calculates the team's effective Elo based on the currently active roster.
        """
        roster = self.team_rosters.get(team, {})
        if not roster:
            return self.base_elo # Fallback if no roster data
            
        total_minutes = sum(roster.values())
        if total_minutes == 0: return self.base_elo
        
        weighted_elo_sum = sum(self.get_player_elo(p) * mins for p, mins in roster.items())
        # Multiply by 5 because there are 5 players on the court at any time
        # The team's rating is effectively the sum of the 5 players on the floor.
        average_court_elo = (weighted_elo_sum / total_minutes) * 5
        return average_court_elo
        
    def update_ratings(self, home_team: str, away_team: str, home_score: int, away_score: int, home_minutes: dict, away_minutes: dict):
        """
        Updates player Elos post-match based on the actual result.
        home_minutes/away_minutes: dict of player_name -> minutes actually played in the game.
        """
        h_elo = self.get_team_elo(home_team) + self.home_advantage
        a_elo = self.get_team_elo(away_team)
        
        # Expected win prob
        exp_home = 1.0 / (1.0 + 10.0 ** ((a_elo - h_elo) / 400.0))
        
        # Actual outcome (1 for home win, 0 for away win, 0.5 for tie)
        if home_score > away_score:
            actual_home = 1.0
        elif home_score < away_score:
            actual_home = 0.0
        else:
            actual_home = 0.5
            
        # Point differential multiplier (Margin of Victory)
        mov = abs(home_score - away_score)
        elo_diff = h_elo - a_elo if home_score > away_score else a_elo - h_elo
        mov_multiplier = math.log(mov + 1) * (2.2 / ((elo_diff)*0.001 + 2.2))
        
        # Total Elo shift for the team
        shift = self.k_factor * mov_multiplier * (actual_home - exp_home)
        
        # Distribute shift to players based on % of total team minutes played
        h_total_mins = sum(home_minutes.values())
        a_total_mins = sum(away_minutes.values())
        
        for p, mins in home_minutes.items():
            current_elo = self.get_player_elo(p)
            weight = (mins / h_total_mins) * 5 if h_total_mins > 0 else 0
            self.player_ratings[p] = current_elo + (shift * weight)
            
        for p, mins in away_minutes.items():
            current_elo = self.get_player_elo(p)
            weight = (mins / a_total_mins) * 5 if a_total_mins > 0 else 0
            # Away shift is inverse of home shift
            self.player_ratings[p] = current_elo - (shift * weight)
            
    def fit(self, historical_data_path: str = None, league_name: str = "NBA"):
        if not historical_data_path:
            print(f"[BasketballModel] No historical data provided for {league_name}. Using uncalibrated baseline (1500 Elo).")
            return
            
        try:
            df = pd.read_csv(historical_data_path)
            
            # EuroLeague API format support
            if 'Gamecode' in df.columns and 'Minutes' in df.columns and 'Points' in df.columns:
                print(f"[BasketballModel] Detected EuroLeague format. Calibrating Elo...")
                
                # Convert 'MM:SS' to fractional minutes
                def parse_mins(x):
                    if pd.isna(x) or not isinstance(x, str) or ':' not in x: return 0.0
                    m, s = x.split(':')
                    return float(m) + float(s)/60.0
                
                df['Minutes_Float'] = df['Minutes'].apply(parse_mins)
                df = df.fillna({"Points": 0})
                
                # Group by Gamecode
                games = df.groupby('Gamecode')
                for game_id, g_df in games:
                    home_df = g_df[g_df['Home'] == 1]
                    away_df = g_df[g_df['Home'] == 0]
                    
                    if len(home_df) == 0 or len(away_df) == 0: continue
                    
                    home_team = home_df['Team'].iloc[0]
                    away_team = away_df['Team'].iloc[0]
                    
                    home_score = home_df['Points'].sum()
                    away_score = away_df['Points'].sum()
                    
                    home_mins = {row['Player']: row['Minutes_Float'] for _, row in home_df.iterrows() if row['Minutes_Float'] > 0}
                    away_mins = {row['Player']: row['Minutes_Float'] for _, row in away_df.iterrows() if row['Minutes_Float'] > 0}
                    
                    self.update_ratings(home_team, away_team, home_score, away_score, home_mins, away_mins)
                    
                print(f"[BasketballModel] Successfully calibrated player Elos on {len(games)} historical matches.")
            else:
                print("[BasketballModel] Format not recognized.")
                
        except Exception as e:
            print(f"[BasketballModel] Error loading {historical_data_path}: {e}")

    def predict(self, home_team: str, away_team: str, over_under_line: float = 225.5, league: str = "NBA") -> dict:
        h_elo = self.get_team_elo(home_team) + self.home_advantage
        a_elo = self.get_team_elo(away_team)
        
        exp_home = 1.0 / (1.0 + 10.0 ** ((a_elo - h_elo) / 400.0))
        exp_away = 1.0 - exp_home
        
        # Default stats based on league
        base_pace = 99.0 if league == "NBA" else 82.0 # FIBA/EuroLeague is much slower
        base_rtg = 114.0 if league == "NBA" else 108.0
        
        h_pace = self.team_stats.get(home_team, {}).get("pace", base_pace)
        a_pace = self.team_stats.get(away_team, {}).get("pace", base_pace)
        exp_poss = (h_pace + a_pace) / 2.0
        
        h_off = self.team_stats.get(home_team, {}).get("off_rtg", base_rtg)
        a_def = self.team_stats.get(away_team, {}).get("def_rtg", base_rtg)
        a_off = self.team_stats.get(away_team, {}).get("off_rtg", base_rtg)
        h_def = self.team_stats.get(home_team, {}).get("def_rtg", base_rtg)
        
        exp_home_pts = (h_off + a_def) / 2.0 * (exp_poss / 100.0)
        exp_away_pts = (a_off + h_def) / 2.0 * (exp_poss / 100.0)
        exp_total = exp_home_pts + exp_away_pts
        
        std_dev = 14.0 if league == "NBA" else 12.0
        
        prob_over = 1.0 - st.norm.cdf(over_under_line, loc=exp_total, scale=std_dev)
        prob_under = 1.0 - prob_over
        
        return {
            "home_win": exp_home,
            "away_win": exp_away,
            "draw": 0.0,
            "over_total": prob_over,
            "under_total": prob_under
        }



