
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message, is_news=False):
    try:
        header = "📰 *NOTICIAS CRIPTO*:" if is_news else "📈 *ALERTA DE TRADING*:"
        full_message = f"{header}\n\n{message}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": full_message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Error al enviar mensaje Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error Telegram: {str(e)}")
