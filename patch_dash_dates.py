import os
import re

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add timedelta import
content = content.replace("from datetime import datetime, timezone", "from datetime import datetime, timezone, timedelta")

# Insert filtering logic right after data = load_data() and before if not data:
filter_logic = """
now = datetime.now(timezone.utc)
end_of_week = now + timedelta(days=7)

def parse_date(date_str):
    try:
        if date_str.endswith("Z"):
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return now

if data:
    valid_accas = []
    for acca in data:
        has_past_leg = False
        out_of_week = False
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt < now:
                has_past_leg = True
            elif dt > end_of_week:
                out_of_week = True
        # Keep only if no past leg. If it's next week, we allow it but deprioritize later or exclude?
        # The user said "priorities given for games playing this week", let's strictly show this week to avoid confusion.
        if not has_past_leg and not out_of_week:
            valid_accas.append(acca)
    data = valid_accas

"""

content = content.replace("if not data:\n    st.warning", filter_logic + "if not data:\n    st.warning")

# Improve date rendering in render_acca
old_render = "date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')"
new_render = """dt = parse_date(leg.get('date', ''))
        date_str = dt.strftime("%A, %b %d @ %H:%M UTC")"""
content = content.replace(old_render, new_render)

# Improve date rendering in Top Picks (singles)
old_render_tp = "date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')"
content = content.replace(old_render_tp, new_render)

# Improve date rendering in Safe tab
old_render_safe = "date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')"
new_render_safe = """dt = parse_date(leg.get('date', ''))
            date_str = dt.strftime("%A, %b %d @ %H:%M UTC")"""
content = content.replace(old_render_safe, new_render_safe)

# Add the date to the Safe Tab rendering
content = content.replace("<b>Market:</b>", "<b>Date & Time:</b> {date_str} <br>\n                    <b>Market:</b>")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
