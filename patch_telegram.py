with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\telegram_notifier.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("NBA ACCUMULATORS", "BASKETBALL ACCUMULATORS")

with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\telegram_notifier.py", "w", encoding="utf-8") as f:
    f.write(text)
