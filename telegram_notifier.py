import os
import requests

def send_telegram_message(message: str) -> bool:
    """
    Sends a message via the Funded Algo Telegram bot.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("[Telegram] Credentials missing. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        print("[Telegram] Top Accumulators successfully sent to your phone!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[Telegram] Failed to send message: {e}")
        # Print response body if available for debugging
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def get_telegram_messages_by_category(soccer_accas: list, nba: list) -> list:
    """
    Formats the categorized accumulators into a list of readable HTML messages for Telegram.
    This prevents hitting Telegram's 4096-character limit by splitting categories into separate texts.
    """
    messages = []
    
    def _format_date(iso_date):
        if not iso_date: return "Unknown"
        return iso_date.replace('T', ' ')[:16]

    if soccer_accas:
        msg = "<b>âš½ TOP SOCCER ACCUMULATORS</b>\n\n"
        for i, acca in enumerate(soccer_accas[:10]):
            msg += f"<b>ðŸ”¹ Acca #{i+1} | Odds: {acca['odds']:.2f}</b>\n"
            msg += f"<i>Edge: +{acca['edge']*100:.2f}% | Stake: KES {acca['stake']:.0f}</i>\n"
            for leg in acca['legs']:
                dt_str = _format_date(leg.get('date', ''))
                msg += f"   â€¢ [{leg['league']}] {leg['home']} vs {leg['away']} <i>({dt_str})</i>\n"
                msg += f"      ðŸ‘‰ {leg['market']} @ {leg['odds']:.2f} <i>(+{leg['edge']*100:.1f}%)</i>\n"
            msg += "\n"
        messages.append(msg)
            
    if nba:
        msg = "<b>ðŸ€ BASKETBALL ACCUMULATORS</b>\n\n"
        for i, acca in enumerate(nba[:10]):
            msg += f"<b>ðŸ”¹ Acca #{i+1} | Odds: {acca['odds']:.2f}</b>\n"
            msg += f"<i>Edge: +{acca['edge']*100:.2f}% | Stake: KES {acca['stake']:.0f}</i>\n"
            for leg in acca['legs']:
                dt_str = _format_date(leg.get('date', ''))
                msg += f"   â€¢ [{leg['league']}] {leg['home']} vs {leg['away']} <i>({dt_str})</i>\n"
                msg += f"      ðŸ‘‰ {leg['market']} @ {leg['odds']:.2f} <i>(+{leg['edge']*100:.1f}%)</i>\n"
            msg += "\n"
        messages.append(msg)
            
    if not messages:
        messages.append("<i>No +EV accumulators found for today's fixtures.</i>")
        
    return messages

