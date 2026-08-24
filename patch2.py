import re

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\basketball_model.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("def known_teams(self):`n        return []`n    def get_player_elo", "def known_teams(self):\n        return []\n    def get_player_elo")

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\basketball_model.py", "w", encoding="utf-8") as f:
    f.write(text)
