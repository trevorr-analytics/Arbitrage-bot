import os
import re

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# We need to completely rewrite the filtering logic.
# Currently, `data = valid_accas` happens before `for acca in reversed(data): all_legs.append(leg)`
# Let's find the whole block and replace it.

bad_logic = """if data:
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
    data = valid_accas"""

new_logic = """if data:
    valid_accas = []
    raw_all_legs = []
    
    # First, collect all unique future legs regardless of acca validity
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
                out_of_week = True
        
        if not has_past_leg and not out_of_week:
            valid_accas.append(acca)
            
    # Overwrite data with only valid future accas (so the Acca tabs don't show past games)
    data = valid_accas"""

content = content.replace(bad_logic, new_logic)

# Since we already populated raw_all_legs correctly, we need to remove the old all_legs population loop.
old_loop = """for acca in reversed(data):
    is_nba = False
    for leg in acca.get("legs", []):
        if leg.get("league") in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            is_nba = True
        
        # deduplicate legs
        # Check by match signature to avoid referencing issues
        leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
        if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in all_legs):
            all_legs.append(leg)

    if is_nba:
        nba_accas.append(acca)
    else:
        soccer_accas.append(acca)"""

new_loop = """all_legs = raw_all_legs

for acca in data: # We already reversed earlier if we needed, but data is now just valid_accas
    is_nba = False
    for leg in acca.get("legs", []):
        if leg.get("league") in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            is_nba = True

    if is_nba:
        nba_accas.append(acca)
    else:
        soccer_accas.append(acca)"""

content = content.replace(old_loop, new_loop)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
