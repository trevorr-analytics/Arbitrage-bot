import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update parse_date
old_parse = """def parse_date(date_str):
    try:
        if date_str.endswith("Z"):
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return now"""

new_parse = """def parse_date(date_str):
    if not date_str:
        return None
    try:
        if date_str.endswith("Z"):
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None"""
content = content.replace(old_parse, new_parse)

# 2. Update logic loops
old_logic = """    # First, collect all unique future legs regardless of acca validity
    for acca in reversed(data):
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if now <= dt <= end_of_week:
                leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
                if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in raw_all_legs):
                    raw_all_legs.append(leg)
                    
        # Now validate the acca itself (must not contain past games)
        has_past_leg = False
        out_of_week = False
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt < now:
                has_past_leg = True
            elif dt > end_of_week:
                out_of_week = True"""

new_logic = """    # First, collect all unique future legs regardless of acca validity
    for acca in reversed(data):
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is None or (now <= dt <= end_of_week):
                leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
                if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in raw_all_legs):
                    raw_all_legs.append(leg)
                    
        # Now validate the acca itself (must not contain past games)
        has_past_leg = False
        out_of_week = False
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is not None:
                if dt < now:
                    has_past_leg = True
                elif dt > end_of_week:
                    out_of_week = True"""
content = content.replace(old_logic, new_logic)

# 3. Update all three rendering spots
content = content.replace("""        dt = parse_date(leg.get('date', ''))
        date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT")""",
"""        dt = parse_date(leg.get('date', ''))
        date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT") if dt else "Time TBD" """)

content = content.replace("""        dt = parse_date(leg.get('date', ''))
            date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT")""",
"""        dt = parse_date(leg.get('date', ''))
            date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT") if dt else "Time TBD" """)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
