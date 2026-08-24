with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_api.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("print(\"\nERROR: ODDS_API_KEY environment variable is not set.\")", "print(\"\\nERROR: ODDS_API_KEY environment variable is not set.\")")

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\odds_api.py", "w", encoding="utf-8") as f:
    f.write(text)
