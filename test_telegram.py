import sys
sys.path.append("C:\\Users\\hp\\Desktop\\AutoQuant_Betting_Bot")
from accumulator_builder import get_all_ev_legs, build_accumulators
from telegram_notifier import get_telegram_messages_by_category

legs = get_all_ev_legs()
bball_leagues = ["NBA", "EuroLeague", "NCAAB", "WNBA"]
soccer_legs = [leg for leg in legs if leg["league"] not in bball_leagues]
nba_legs = [leg for leg in legs if leg["league"] in bball_leagues]

accas_soccer, _ = build_accumulators(soccer_legs, max_odds=3.5)
accas_nba, _ = build_accumulators(nba_legs, max_odds=3.5)

accas_soccer.sort(key=lambda x: abs(x["odds"] - 2.0))
accas_nba.sort(key=lambda x: abs(x["odds"] - 2.0))

msgs = get_telegram_messages_by_category(accas_soccer[:10], accas_nba[:10])
with open("test_telegram.txt", "w", encoding="utf-8") as f:
    for m in msgs:
        f.write(m + "\n====================\n")
