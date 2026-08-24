import re

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "r", encoding="utf-8") as f:
    text = f.read()

fit_replacement = """        if league in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            model = BasketballModel()
            if league == "EuroLeague" and os.path.exists("basketball_data/euroleague_2023_boxscore.csv"):
                model.fit("basketball_data/euroleague_2023_boxscore.csv", league_name=league)
            else:
                model.fit() # Stub fit for others
            known = model.known_teams()
"""

text = re.sub(r'        if league in \["NBA", "EuroLeague", "NCAAB", "WNBA"\]:\s*model = BasketballModel\(\)\s*model\.fit\(\) # Stub fit for now, later replaced with full 538 history\s*known = model\.known_teams\(\)', fit_replacement, text, flags=re.DOTALL)

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "w", encoding="utf-8") as f:
    f.write(text)
