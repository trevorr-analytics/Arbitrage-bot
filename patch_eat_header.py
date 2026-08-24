import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_update = "st.write(f\"**Last Updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\")"
new_update = "st.write(f\"**Last Updated:** {(datetime.now(timezone.utc) + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M EAT')}\")"

content = content.replace(old_update, new_update)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
