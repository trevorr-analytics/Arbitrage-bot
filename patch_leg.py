import os

f2 = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py"
with open(f2, "r", encoding="utf-8") as f:
    c2 = f.read()

old_leg = """                    "edge": leg["edge"],
                    "date": leg.get("date", ""),"""

new_leg = """                    "edge": leg["edge"],
                    "model_prob": leg.get("model_prob", 0),
                    "date": leg.get("date", ""),"""

c2_new = c2.replace(old_leg, new_leg)

with open(f2, "w", encoding="utf-8") as f:
    f.write(c2_new)
