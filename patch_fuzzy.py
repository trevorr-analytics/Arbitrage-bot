import re
with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("    return None\n", "    return name if not known else None\n")
with open(r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py", "w", encoding="utf-8") as f:
    f.write(text)
