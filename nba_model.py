import math
import scipy.stats as st

class NBAModel:
    """
    Independent Probability Model for NBA matches.
    Evaluates Moneyline and Totals utilizing an Elo rating framework and possession-based 
    efficiency averages. Handles Home Court Advantage explicitly.
    """
    def __init__(self):
        self.team_ratings = {}
        # NBA home-court advantage is roughly equivalent to +65 Elo points (~2.3 points spread)
        self.home_advantage = 65 
        
    def known_teams(self):
        return [
            "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", 
            "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets", 
            "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers", 
            "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat", 
            "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", 
            "New York Knicks", "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", 
            "Phoenix Suns", "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", 
            "Toronto Raptors", "Utah Jazz", "Washington Wizards"
        ]
        
    def fit(self, data=None, league_name="NBA"):
        """
        In production, this will parse the FiveThirtyEight or Kaggle historical CSV 
        and replay the Elo updates (handling Back-to-Backs and injury absences).
        For the initial structure, it stubs all 30 teams with baseline ratings.
        """
        for team in self.known_teams():
            self.team_ratings[team] = {
                "elo": 1500.0,
                "off_rtg": 114.0, # Points per 100 possessions
                "def_rtg": 114.0,
                "pace": 99.0      # Possessions per 48 mins
            }
            
    def predict(self, home_team: str, away_team: str, over_under_line: float = 225.5) -> dict:
        """
        Returns probabilities for Moneyline and the specific Over/Under line requested.
        """
        # 1. Moneyline Math (Elo formulation)
        h_elo = self.team_ratings.get(home_team, {}).get("elo", 1500.0)
        a_elo = self.team_ratings.get(away_team, {}).get("elo", 1500.0)
        
        # Apply strict Home Court Advantage scalar
        h_elo += self.home_advantage
        
        # Win probability using standard Elo math (base 10, divisor 400)
        exp_home = 1.0 / (1.0 + 10.0 ** ((a_elo - h_elo) / 400.0))
        exp_away = 1.0 - exp_home
        
        # 2. Totals Math (Pace & Efficiency)
        h_pace = self.team_ratings.get(home_team, {}).get("pace", 99.0)
        a_pace = self.team_ratings.get(away_team, {}).get("pace", 99.0)
        exp_poss = (h_pace + a_pace) / 2.0
        
        h_off = self.team_ratings.get(home_team, {}).get("off_rtg", 114.0)
        a_def = self.team_ratings.get(away_team, {}).get("def_rtg", 114.0)
        a_off = self.team_ratings.get(away_team, {}).get("off_rtg", 114.0)
        h_def = self.team_ratings.get(home_team, {}).get("def_rtg", 114.0)
        
        # Project home and away points based on matched efficiency and pace
        exp_home_pts = (h_off + a_def) / 2.0 * (exp_poss / 100.0)
        exp_away_pts = (a_off + h_def) / 2.0 * (exp_poss / 100.0)
        exp_total = exp_home_pts + exp_away_pts
        
        # Assume normal distribution of points with an ~14 point standard deviation for totals
        std_dev = 14.0
        
        # Probability that actual total > over_under_line
        prob_over = 1.0 - st.norm.cdf(over_under_line, loc=exp_total, scale=std_dev)
        prob_under = 1.0 - prob_over
        
        return {
            "home_win": exp_home,
            "away_win": exp_away,
            "draw": 0.0, # Basketball ML includes OT; "draw" odds exist rarely in 3-way markets, mapped to 0 here
            "over_total": prob_over,
            "under_total": prob_under
        }
