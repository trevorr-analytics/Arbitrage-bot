import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\accumulator_builder.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

dreamer_logic = """    # -- DREAMER PARLAY --
    print("Building the Dreamer Parlay (Odds > 500.0)...")
    dreamer_legs = []
    current_odds = 1.0
    sorted_ev_legs = sorted(ev_legs, key=lambda x: x["edge"], reverse=True)
    for leg in sorted_ev_legs:
        # Avoid duplicate matches in the dreamer parlay
        if not any(l["match_id"] == leg["match_id"] for l in dreamer_legs):
            dreamer_legs.append(leg)
            current_odds *= leg["odds"]
            if current_odds >= 500.0:
                break
                
    if current_odds >= 500.0:
        dreamer_acca = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "PENDING",
            "combined_odds": current_odds,
            "combined_edge": sum(l["edge"] for l in dreamer_legs) / len(dreamer_legs) if dreamer_legs else 0,
            "stake": 100.0,
            "is_dreamer": True,
            "legs": []
        }
        for leg in dreamer_legs:
            dreamer_acca["legs"].append({
                "match_id": leg["match_id"],
                "league": leg["league"],
                "home": leg["home"],
                "away": leg["away"],
                "market": leg["market"],
                "odds": leg["odds"],
                "edge": leg["edge"],
                "model_prob": leg.get("model_prob", 0),
                "date": leg.get("date", ""),
                "status": "PENDING"
            })
        tracked_data.append(dreamer_acca)

    # Save tracking JSON"""

content = content.replace("    # Save tracking JSON", dreamer_logic)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
