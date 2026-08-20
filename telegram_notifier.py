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

def format_categorized_accas_for_telegram(soccer_1x2: list, soccer_ou: list, nba: list) -> str:
    """
    Formats the categorized accumulators into a readable HTML message for Telegram.
    """
    msg = "<b>🤖 AUTO-QUANT VALUE ACCUMULATORS 🤖</b>\n\n"
    
    if soccer_1x2:
        msg += "<b>⚽ SOCCER (1X2 MATCH WINNER)</b>\n"
        for i, acca in enumerate(soccer_1x2[:5]):
            msg += f"<b>🔹 Acca #{i+1} | Odds: {acca['odds']:.2f}</b>\n"
            msg += f"<i>Edge: +{acca['edge']*100:.2f}% | Stake: KES {acca['stake']:.0f}</i>\n"
            for leg in acca['legs']:
                msg += f"   • [{leg['league']}] {leg['home']} vs {leg['away']}\n"
                msg += f"      👉 {leg['market']} @ {leg['odds']:.2f} <i>(+{leg['edge']*100:.1f}%)</i>\n"
            msg += "\n"
            
    if soccer_ou:
        msg += "<b>⚽ SOCCER (OVER/UNDER GOALS)</b>\n"
        for i, acca in enumerate(soccer_ou[:5]):
            msg += f"<b>🔹 Acca #{i+1} | Odds: {acca['odds']:.2f}</b>\n"
            msg += f"<i>Edge: +{acca['edge']*100:.2f}% | Stake: KES {acca['stake']:.0f}</i>\n"
            for leg in acca['legs']:
                msg += f"   • [{leg['league']}] {leg['home']} vs {leg['away']}\n"
                msg += f"      👉 {leg['market']} @ {leg['odds']:.2f} <i>(+{leg['edge']*100:.1f}%)</i>\n"
            msg += "\n"
            
    if nba:
        msg += "<b>🏀 NBA ACCUMULATORS</b>\n"
        for i, acca in enumerate(nba[:10]):
            msg += f"<b>🔹 Acca #{i+1} | Odds: {acca['odds']:.2f}</b>\n"
            msg += f"<i>Edge: +{acca['edge']*100:.2f}% | Stake: KES {acca['stake']:.0f}</i>\n"
            for leg in acca['legs']:
                msg += f"   • [{leg['league']}] {leg['home']} vs {leg['away']}\n"
                msg += f"      👉 {leg['market']} @ {leg['odds']:.2f} <i>(+{leg['edge']*100:.1f}%)</i>\n"
            msg += "\n"
            
    if not soccer_1x2 and not soccer_ou and not nba:
        msg += "<i>No +EV accumulators found for today's fixtures.</i>"
        
    return msg
