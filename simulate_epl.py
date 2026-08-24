import pandas as pd
from itertools import combinations

df = pd.read_csv("backtest/xg_grid_results.csv")
df = df[df["Model"] == "Weight_70_30"]

legs = []
for idx, row in df.iterrows():
    if pd.notna(row["PSH"]) and row["P_H"] > (1 / row["PSH"]):
        legs.append({
            "date": row["MatchDate"],
            "match": f"{row['HomeTeam']} vs {row['AwayTeam']}",
            "bet": 0, "odds": row["PSH"], "prob": row["P_H"], "actual": row["Actual"]
        })
    if pd.notna(row["PSA"]) and row["P_A"] > (1 / row["PSA"]):
        legs.append({
            "date": row["MatchDate"],
            "match": f"{row['HomeTeam']} vs {row['AwayTeam']}",
            "bet": 2, "odds": row["PSA"], "prob": row["P_A"], "actual": row["Actual"]
        })

df_legs = pd.DataFrame(legs)
all_accas = []

for date, group in df_legs.groupby("date"):
    daily_legs = group.to_dict('records')
    if len(daily_legs) < 2: continue
    for combo in combinations(daily_legs, 2):
        if combo[0]["match"] == combo[1]["match"]: continue
        odds = combo[0]["odds"] * combo[1]["odds"]
        if 1.5 <= odds <= 3.5:
            edge = (combo[0]["prob"] * combo[1]["prob"]) - (1/odds)
            if edge > 0:
                all_accas.append({
                    "date": date, "odds": odds, "edge": edge,
                    "won": (combo[0]["actual"] == combo[0]["bet"]) and (combo[1]["actual"] == combo[1]["bet"])
                })

df_accas = pd.DataFrame(all_accas)
filtered_accas = []
for date, group in df_accas.groupby("date"):
    group["dist"] = abs(group["odds"] - 2.0)
    top10 = group.sort_values("dist").head(10)
    filtered_accas.extend(top10.to_dict('records'))

df_final = pd.DataFrame(filtered_accas)

if len(df_final) == 0:
    print("No accumulators formed.")
else:
    total_staked = len(df_final)
    total_returned = df_final[df_final["won"]]["odds"].sum()
    roi = ((total_returned - total_staked) / total_staked) * 100
    print(f"--- EPL ACCUMULATOR BACKTEST RESULTS (70/30 Model) ---")
    print(f"Total Accumulators: {total_staked}")
    print(f"Win Rate: {(df_final['won'].sum() / total_staked)*100:.2f}%")
    print(f"ROI: {roi:.2f}%")
