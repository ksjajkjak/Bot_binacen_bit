import requests
from telegram_bot import send_telegram_message
from config import SYMBOL, CRYPTOPANIC_API_KEY

def get_crypto_news():
    """
    Obtiene las últimas noticias de CryptoPanic para la moneda configurada.
    Solo informativo, no afecta decisiones de trading.
    """
    try:
        base_symbol = SYMBOL.replace("USDT", "")
        url = (
            f"https://cryptopanic.com/api/v1/posts/"
            f"?auth_token={CRYPTOPANIC_API_KEY}&currencies={base_symbol}&public=true"
        )

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                recent_news = data['results'][:3]
                news_message = f"📰 Últimas noticias sobre {base_symbol}:\n\n"

                for news in recent_news:
                    title = news.get('title', 'Sin título')
                    source = news.get('source', {}).get('title', 'Fuente desconocida')
                    url = news.get('url', '')
                    votes = news.get('votes', {})
                    positive = votes.get('positive', 0)
                    negative = votes.get('negative', 0)
                    sentiment_icon = "🟢" if positive >= negative else "🔴"

                    news_message += f"{sentiment_icon} {title}\n"
                    news_message += f"📊 Fuente: {source}\n"
                    news_message += f"🔗 {url[:50]}...\n\n"

                send_telegram_message(news_message, is_news=True)
                return True
            else:
                print("No hay noticias recientes disponibles")
                return False
        else:
            print(f"Error al obtener noticias: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error al obtener noticias de CryptoPanic: {e}")
        send_telegram_message(f"⚠️ Error al obtener noticias: {str(e)}", is_news=True)
        return False