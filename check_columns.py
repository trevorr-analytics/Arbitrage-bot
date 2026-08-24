from euroleague_api.boxscore_data import BoxScoreData
boxscore_data = BoxScoreData(competition="E")
df = boxscore_data.get_players_boxscore_stats(season=2023, gamecode=1)
print(df.columns.tolist())
print(df.head(2).to_dict('records'))
