import os

patch = """import difflib

def fuzzy_team(name: str, known: list) -> str:
    for k in known:
        if k.lower() == name.lower(): return k
    matches = difflib.get_close_matches(name, known, n=1, cutoff=0.55)
    if matches:
        return matches[0]
    generic = {"fc", "real", "united", "city", "athletic", "club", "de", "cf", "and", "hove", "albion"}
    name_clean = " ".join([w for w in name.lower().split() if w not in generic])
    if len(name_clean) > 3:
        for k in known:
            k_clean = " ".join([w for w in k.lower().split() if w not in generic])
            if name_clean in k_clean or (len(k_clean)>3 and k_clean in name_clean):
                return k
    return name if not known else None
"""

f2 = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py"
with open(f2, "r", encoding="utf-8") as f:
    c2 = f.read()

start2 = c2.find("def fuzzy_team(name: str, known: list) -> str:")
end2 = c2.find("def get_all_ev_legs() -> List[Dict]:", start2)

c2_new = c2[:start2] + patch + "\n" + c2[end2:]
with open(f2, "w", encoding="utf-8") as f:
    f.write(c2_new)
