import time
import schedule
from binance_client import BinanceClient
from strategy_scalping import run_scalping_strategy
from simple_ai import SimpleMarketAI
from crypto_news import get_crypto_news
from telegram_bot import send_telegram_message
from get_data import get_klines
from config import SYMBOL

print("💰 Bot ejecutándose en MODO REAL con tu cuenta de Binance")

# Verificar sincronización de tiempo al inicio
try:
    from binance_client import BinanceClient
    test_client = BinanceClient()
    server_time = test_client.client.get_server_time()
    import datetime
    local_time = int(datetime.datetime.now().timestamp() * 1000)
    time_diff = abs(server_time['serverTime'] - local_time)
    
    if time_diff > 5000:  # Más de 5 segundos de diferencia
        print(f"⚠️ ADVERTENCIA: Diferencia de tiempo detectada: {time_diff}ms")
        print("Considera sincronizar tu reloj del sistema")
    else:
        print(f"✅ Sincronización de tiempo correcta (diferencia: {time_diff}ms)")
        
except Exception as e:
    print(f"⚠️ No se pudo verificar sincronización de tiempo: {e}")

# Inicializamos IA ligera para análisis adicional
market_ai = SimpleMarketAI(window_size=14)

def check_market_conditions():
    """
    Chequeo informativo periódico:
    - Precio actual
    - Análisis IA ligera
    - Noticias (solo informativo, no afecta órdenes)
    """
    try:
        client = BinanceClient()
        price = client.get_price()

        # Obtener datos OHLC para análisis IA
        df = get_klines(SYMBOL, interval="5m", limit=20)
        closes = df["close"].tolist()

        # Actualizar IA con los últimos precios
        for price_val in closes[-14:]:
            market_ai.update(price_val)

        insight, confidence = market_ai.get_insight()

        # Armar mensaje informativo
        message = (
            f"📊 Precio actual de {SYMBOL}: ${price:.4f}\n"
            f"🤖 Análisis IA ligera: {insight} (Confianza: {confidence*100:.1f}%)"
        )

        send_telegram_message(message, is_news=True)

        # Obtener noticias y enviarlas solo como info
        news_sent = get_crypto_news()
        if not news_sent:
            send_telegram_message("ℹ️ No hay noticias recientes disponibles.", is_news=True)

    except Exception as e:
        send_telegram_message(f"⚠️ Error al chequear condiciones de mercado: {str(e)}", is_news=True)


if __name__ == "__main__":
    send_telegram_message("🚀 Bot iniciado con estrategia EMA + RSI y análisis IA ligera - CUENTA REAL")

    # Programar chequeo informativo cada 2 horas
    schedule.every(2).hours.do(check_market_conditions)

    # Chequeo inicial
    check_market_conditions()

    while True:
        try:
            # Ejecutar tareas programadas (noticias y análisis)
            schedule.run_pending()

            # Ejecutar la estrategia scalping (operativa real)
            run_scalping_strategy()

            # Esperar 5 minutos antes del siguiente ciclo
            time.sleep(300)

        except Exception as e:
            error_msg = str(e)
            print(f"Error en el bucle principal: {error_msg}")
            
            # Determinar tiempo de espera basado en el tipo de error
            if "<!DOCTYPE html>" in error_msg or "connection" in error_msg.lower():
                wait_time = 300  # 5 minutos para problemas de conectividad
                print(f"⏸️ Problema de conectividad. Esperando {wait_time//60} minutos antes de reintentar")
            else:
                wait_time = 60   # 1 minuto para otros errores
            
            try:
                send_telegram_message(f"⚠️ Error en bucle principal: {error_msg[:100]}...")
            except:
                print("No se pudo enviar notificación de error por Telegram")
            
            time.sleep(wait_time)