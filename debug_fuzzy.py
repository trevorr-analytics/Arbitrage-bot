def fuzzy_team(name, known_teams):
    name_lower = name.lower()
    for k in known_teams:
        if k.lower() == name_lower: return k
    name_tokens = set(name_lower.split())
    for k in known_teams:
        if name_tokens & set(k.lower().split()): return k
    return None

teams = ["Rennes", "Paris SG", "Lille", "Monaco", "Lens", "Marseille"]
print("Rennes ->", fuzzy_team("Rennes", teams))
print("Paris Saint Germain ->", fuzzy_team("Paris Saint Germain", teams))
