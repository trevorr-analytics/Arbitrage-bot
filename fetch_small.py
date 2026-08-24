from euroleague_api.boxscore_data import BoxScoreData
import pandas as pd
boxscore_data = BoxScoreData(competition="E")
dfs = []
for gamecode in range(1, 21):  # First 20 games of 2023 season
    try:
        df = boxscore_data.get_players_boxscore_stats(season=2023, gamecode=gamecode)
        dfs.append(df)
    except Exception as e:
        print(f"Skipping game {gamecode}")

if dfs:
    final_df = pd.concat(dfs)
    final_df.to_csv("basketball_data/euroleague_2023_boxscore.csv", index=False)
    print(f"EuroLeague dataset saved with {len(dfs)} games.")
