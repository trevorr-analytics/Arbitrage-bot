import re

file_path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\sports_model\dashboard.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the first dt parsing
content = content.replace(
    '''        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is None or (now <= dt <= end_of_week):''',
    '''        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is None:
                dt = parse_date(acca.get("timestamp", ""))
            if dt is None or (now <= dt <= end_of_week):'''
)

# Replace the second dt parsing
content = content.replace(
    '''        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is not None:
                if dt < now:''',
    '''        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is None:
                dt = parse_date(acca.get("timestamp", ""))
            if dt is not None:
                if dt < now:'''
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
