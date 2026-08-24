import re
with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_api.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("return cache[sport_key][\"data\"]", "return _parse_odds_data(cache[sport_key][\"data\"])")

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_api.py", "w", encoding="utf-8") as f:
    f.write(text)
