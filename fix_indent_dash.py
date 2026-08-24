import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

bad_indent = """            dt = parse_date(leg.get('date', ''))
        date_str = dt.strftime("%A, %b %d @ %H:%M UTC")"""

good_indent = """            dt = parse_date(leg.get('date', ''))
            date_str = dt.strftime("%A, %b %d @ %H:%M UTC")"""

content = content.replace(bad_indent, good_indent)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
