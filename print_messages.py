import sys
sys.path.append("C:\\Users\\hp\\Desktop\\AutoQuant_Betting_Bot")
from accumulator_builder import get_all_ev_legs, build_accumulators
from telegram_notifier import get_telegram_messages_by_category

legs = get_all_ev_legs()
soccer_legs = [leg for leg in legs if leg["league"] != "NBA"]
nba_legs = [leg for leg in legs if leg["league"] == "NBA"]

accas_soccer, _ = build_accumulators(soccer_legs, max_odds=2.05)
accas_nba, _ = build_accumulators(nba_legs, max_odds=2.05)

accas_soccer.sort(key=lambda x: x["edge"], reverse=True)
accas_nba.sort(key=lambda x: x["edge"], reverse=True)

msgs = get_telegram_messages_by_category(accas_soccer[:10], accas_nba[:10])
for m in msgs:
    print(m)
    print("="*40)
