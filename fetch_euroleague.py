from euroleague_api.boxscore_data import BoxScoreData
import pandas as pd
boxscore_data = BoxScoreData(competition="E")
df = boxscore_data.get_players_boxscore_stats_single_season(season=2023)
df.to_csv("basketball_data/euroleague_2023_boxscore.csv", index=False)
print("EuroLeague dataset saved with shape:", df.shape)
