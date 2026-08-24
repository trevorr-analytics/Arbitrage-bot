import os
import sys

# Set credentials dynamically for this run
os.environ["TELEGRAM_BOT_TOKEN"] = "8643952370:AAGamjIx2lL1xRtPESGKcF9Rvw3q3XUZLAM"
os.environ["TELEGRAM_CHAT_ID"] = "5984452975"

sys.path.append("C:\\Users\\hp\\Desktop\\AutoQuant_Betting_Bot")
from accumulator_builder import get_all_ev_legs, build_accumulators, sort_and_bucket
from telegram_notifier import get_telegram_messages_by_category, send_telegram_message

print("Gathering legs...")
legs = get_all_ev_legs()
soccer_legs = [leg for leg in legs if leg["league"] not in ["NBA", "EuroLeague", "NCAAB", "WNBA"]]
nba_legs = [leg for leg in legs if leg["league"] in ["NBA", "EuroLeague", "NCAAB", "WNBA"]]

accas_soccer, _ = build_accumulators(soccer_legs, max_odds=3.5)
accas_nba, _ = build_accumulators(nba_legs, max_odds=3.5)

accas_soccer = sort_and_bucket(accas_soccer)
accas_nba = sort_and_bucket(accas_nba)

top_soccer = accas_soccer[:10]
top_nba = accas_nba[:10]

msgs = get_telegram_messages_by_category(top_soccer, top_nba)
print(f"Sending {len(msgs)} messages to Telegram...")

for m in msgs:
    success = send_telegram_message(m)
    print("Sent successfully!" if success else "Failed to send.")
