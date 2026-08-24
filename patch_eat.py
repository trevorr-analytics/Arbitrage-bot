import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace UTC format with EAT format globally in the dashboard
old_render = 'date_str = dt.strftime("%A, %b %d @ %H:%M UTC")'
new_render = 'date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT")'

content = content.replace(old_render, new_render)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
