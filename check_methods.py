from euroleague_api.boxscore_data import BoxScoreData
boxscore_data = BoxScoreData(competition="E")
print([m for m in dir(boxscore_data) if "player" in m and "season" in m])
