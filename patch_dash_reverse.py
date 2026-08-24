import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Change `for acca in data:` to `for acca in reversed(data):`
content = content.replace("for acca in data:", "for acca in reversed(data):")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
