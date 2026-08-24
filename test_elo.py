from basketball_model import BasketballModel

model = BasketballModel()
model.fit("basketball_data/euroleague_2023_boxscore.csv", league_name="EuroLeague")

# Print top 10 player Elos
sorted_players = sorted(model.player_ratings.items(), key=lambda x: x[1], reverse=True)
print("\nTop 10 EuroLeague Players by Adjusted Elo (2023 Season Calibration):")
for p, elo in sorted_players[:10]:
    print(f"{p}: {elo:.1f}")
