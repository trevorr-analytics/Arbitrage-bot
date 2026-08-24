import sys
sys.path.append("C:\\Users\\hp\\Desktop\\AutoQuant_Betting_Bot")
from accumulator_builder import get_all_ev_legs, build_accumulators

legs = get_all_ev_legs()
soccer_1x2_legs = [leg for leg in legs if leg["league"] != "NBA" and leg["market"] in ["Home Win", "Away Win", "Draw"]]
soccer_ou_legs = [leg for leg in legs if leg["league"] != "NBA" and ("Over" in leg["market"] or "Under" in leg["market"])]
nba_legs = [leg for leg in legs if leg["league"] == "NBA"]

print(f"1X2 legs: {len(soccer_1x2_legs)}")
print(f"O/U legs: {len(soccer_ou_legs)}")
print(f"NBA legs: {len(nba_legs)}")

a1, _ = build_accumulators(soccer_1x2_legs)
a2, _ = build_accumulators(soccer_ou_legs)
a3, _ = build_accumulators(nba_legs)

print(f"1X2 accas: {len(a1)}")
print(f"O/U accas: {len(a2)}")
print(f"NBA accas: {len(a3)}")
