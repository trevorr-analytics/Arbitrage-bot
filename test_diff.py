import difflib

def fuzzy_team(name: str, known: list) -> str:
    # 1. Exact
    for k in known:
        if k.lower() == name.lower(): return k
        
    # 2. Difflib
    matches = difflib.get_close_matches(name, known, n=1, cutoff=0.55)
    if matches:
        return matches[0]
        
    # 3. Fallback stripped substring
    generic = {"fc", "real", "united", "city", "athletic", "club", "de", "cf", "and", "hove", "albion"}
    name_clean = " ".join([w for w in name.lower().split() if w not in generic])
    if len(name_clean) > 3:
        for k in known:
            k_clean = " ".join([w for w in k.lower().split() if w not in generic])
            if name_clean in k_clean or (len(k_clean)>3 and k_clean in name_clean):
                return k
    return None

known = ["Real Madrid", "Real Sociedad", "Racing Santander", "Man United", "Newcastle", "Liverpool", "Brighton"]
print("Real Racing Club de Santander ->", fuzzy_team("Real Racing Club de Santander", known))
print("Newcastle United ->", fuzzy_team("Newcastle United", known))
print("Brighton and Hove Albion ->", fuzzy_team("Brighton and Hove Albion", known))
