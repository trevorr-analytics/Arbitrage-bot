import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("<span class=\"edge-text\">", "<span class='edge-text'>")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
