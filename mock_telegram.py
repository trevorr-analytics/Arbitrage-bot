from dixon_coles import DixonColesModel, load_league_data
from basketball_model import BasketballModel

print("Loading Soccer Model (EPL)...")
soccer_model = DixonColesModel(use_xg=True, xg_weight=0.7)
df = load_league_data("EPL")
soccer_model.fit(df, "EPL")
s_pred = soccer_model.predict("Man City", "Arsenal")

print("Loading Basketball Model (EuroLeague)...")
bball_model = BasketballModel()
bball_model.fit("basketball_data/euroleague_2023_boxscore.csv", league_name="EuroLeague")
b_pred = bball_model.predict("Real Madrid", "FC Barcelona", league="EuroLeague")

print("\n--- GENERATED ACCUMULATORS ---")
print("<b>⚽ TOP SOCCER ACCUMULATORS</b>\n")
print(f"<b>🔹 Acca #1 | Odds: 1.95</b>")
print(f"<i>Edge: +4.2% | Stake: KES 50</i>")
print(f"   • [EPL] Man City vs Arsenal")
print(f"      👉 Home Win @ 1.95 <i>(Model Prob: {s_pred['home_win']*100:.1f}%)</i>\n")

print("<b>🏀 BASKETBALL ACCUMULATORS</b>\n")
print(f"<b>🔹 Acca #1 | Odds: 1.90</b>")
print(f"<i>Edge: +5.5% | Stake: KES 50</i>")
print(f"   • [EuroLeague] Real Madrid vs FC Barcelona")
print(f"      👉 Home Win @ 1.90 <i>(Model Prob: {b_pred['home_win']*100:.1f}%)</i>\n")

