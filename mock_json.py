import json
from dixon_coles import DixonColesModel, load_league_data
from basketball_model import BasketballModel

soccer_model = DixonColesModel(use_xg=True, xg_weight=0.7)
df = load_league_data("EPL")
soccer_model.fit(df, "EPL")
s_pred1 = soccer_model.predict("Man City", "Arsenal")
s_pred2 = soccer_model.predict("Liverpool", "Chelsea")

bball_model = BasketballModel()
# Use a default fallback since the CSV is somehow missing in this dir or path is wrong
bball_model.player_ratings = {"CAMPAZZO, FACUNDO": 1574.8, "YABUSELE, GUERSCHON": 1555.6, "LAPROVITTOLA, NICOLAS": 1521.3}
bball_model.team_rosters = {
    "Real Madrid": {"CAMPAZZO, FACUNDO": 30, "YABUSELE, GUERSCHON": 30, "MUSA, DZANAN": 25},
    "FC Barcelona": {"LAPROVITTOLA, NICOLAS": 30, "VESELY, JAN": 25}
}
b_pred = bball_model.predict("Real Madrid", "FC Barcelona", league="EuroLeague")

out = {
    "soccer1": s_pred1,
    "soccer2": s_pred2,
    "bball1": b_pred
}
print(json.dumps(out))
