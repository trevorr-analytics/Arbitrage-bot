import re

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\basketball_model.py", "r", encoding="utf-8") as f:
    text = f.read()

fit_replacement = """    def fit(self, historical_data_path: str = None, league_name: str = "NBA"):
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
"""

# replace everything from def fit to def predict
text = re.sub(r'    def fit\(self, historical_data_path: str = None, league_name: str = "NBA"\):.*?    def predict\(', fit_replacement + '\n    def predict(', text, flags=re.DOTALL)

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\basketball_model.py", "w", encoding="utf-8") as f:
    f.write(text)
