import pandas as pd
import numpy as np
import math
from get_data import get_klines
from binance_client import BinanceClient
from telegram_bot import send_telegram_message
from config import SYMBOL, SCALPING_TP, SCALPING_SL
import time

def run_scalping_strategy():
    """
    Ejecuta la estrategia de scalping con EMA 8/21 + RSI 14
    """
    try:
        client = BinanceClient()

        # Verificar si ya hay una posición abierta
        current_qty = client.get_position_qty()
        if current_qty > 0:
            print(f"Ya hay una posición abierta de {current_qty} {SYMBOL}")
            return

        # Pausa breve para control de tasa
        time.sleep(0.5)

        # Obtener datos para análisis técnico
        df = get_klines(SYMBOL, interval="5m", limit=50)
        if df.empty:
            print("No se pudieron obtener datos de mercado")
            return

        # Calcular indicadores técnicos
        # EMA rápida (8 períodos) - más reactiva
        df['ema_8'] = df['close'].ewm(span=8).mean()
        # EMA lenta (21 períodos) - confirma tendencia
        df['ema_21'] = df['close'].ewm(span=21).mean()

        # RSI (14 períodos)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Obtener valores actuales y anteriores para detectar cruces
        current_price = client.get_price()
        ema_8_current = df['ema_8'].iloc[-1]
        ema_21_current = df['ema_21'].iloc[-1]
        ema_8_previous = df['ema_8'].iloc[-2]
        ema_21_previous = df['ema_21'].iloc[-2]
        rsi_current = df['rsi'].iloc[-1]

        print(f"Precio actual: {current_price:.4f}")
        print(f"EMA 8: {ema_8_current:.4f}, EMA 21: {ema_21_current:.4f}")
        print(f"RSI: {rsi_current:.2f}")

        # Detectar cruces de EMAs
        cruce_alcista = (ema_8_previous <= ema_21_previous) and (ema_8_current > ema_21_current)
        cruce_bajista = (ema_8_previous >= ema_21_previous) and (ema_8_current < ema_21_current)

        # Señales de trading con lógica de cruces
        signal = None

        # Señal de compra: Cruce alcista + RSI > 55 (evitar zona neutral 45-55)
        if cruce_alcista and rsi_current > 55:
            signal = "BUY"
            print(f"🔥 CRUCE ALCISTA detectado! EMA 8 cruza por encima de EMA 21")

        # Señal de venta: Cruce bajista + RSI < 45 (evitar zona neutral 45-55)
        elif cruce_bajista and rsi_current < 45:
            signal = "SELL"
            print(f"🔥 CRUCE BAJISTA detectado! EMA 8 cruza por debajo de EMA 21")

        # Zona neutral: evitar operar
        elif 45 <= rsi_current <= 55:
            print(f"⚪ Mercado en zona neutral (RSI: {rsi_current:.1f}). Evitando operar.")

        # EMAs ya alineadas pero sin cruce reciente
        elif ema_8_current > ema_21_current and rsi_current > 55:
            print(f"📈 Tendencia alcista establecida, esperando entrada o cruce")
        elif ema_8_current < ema_21_current and rsi_current < 45:
            print(f"📉 Tendencia bajista establecida, esperando entrada o cruce")

        if signal:
            # Calcular cantidad óptima basada en el saldo disponible
            quantity = client.calcular_cantidad_optima(current_price, max_valor_orden=11.0)

            if quantity > 0:
                # Ejecutar orden de mercado
                order = client.place_market_order(signal, quantity)

                if order:
                    # Calcular precios de TP y SL
                    if signal == "BUY":
                        tp_price = current_price * (1 + SCALPING_TP)
                        sl_price = current_price * (1 - SCALPING_SL)
                    else:  # SELL
                        tp_price = current_price * (1 - SCALPING_TP)
                        sl_price = current_price * (1 + SCALPING_SL)

                    # Establecer TP/SL
                    client.set_tp_sl(signal, tp_price, sl_price)

                    # Notificar por Telegram
                    cruce_tipo = "ALCISTA 📈" if signal == "BUY" else "BAJISTA 📉"
                    message = (
                        f"🎯 Orden ejecutada: {signal} {quantity} {SYMBOL}\n"
                        f"💰 Precio: ${current_price:.4f}\n"
                        f"🔥 Cruce {cruce_tipo}: EMA 8 vs EMA 21\n"
                        f"📈 TP: ${tp_price:.4f} (+{SCALPING_TP*100:.1f}%)\n"
                        f"📉 SL: ${sl_price:.4f} (-{SCALPING_SL*100:.1f}%)\n"
                        f"📊 RSI: {rsi_current:.1f}"
                    )
                    send_telegram_message(message)

                    print(f"✅ Estrategia ejecutada: {signal} a {current_price:.4f}")
                else:
                    print("❌ No se pudo ejecutar la orden")
            else:
                print("⚠️ Cantidad insuficiente para operar")
        else:
            print("⏳ Sin señales de trading en este momento")

    except Exception as e:
        error_msg = str(e)
        print(f"Error en estrategia de scalping: {error_msg}")
        
        # Manejo específico de errores comunes
        if "<!DOCTYPE html>" in error_msg:
            print("🚨 PROBLEMA DETECTADO: Recibiendo HTML en lugar de JSON")
            print("Posibles causas:")
            print("- Restricciones geográficas de Binance")
            print("- Problemas de conectividad a internet")
            print("- Bloqueo temporal de IP")
            print("- Configuración incorrecta de VPN/Proxy")
            telegram_msg = "🚨 Error de conectividad con Binance. Posible bloqueo geográfico o de IP."
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            print("🌐 Problema de conexión a internet detectado")
            telegram_msg = f"🌐 Problema de conexión: {error_msg[:100]}..."
        elif "APIError" in error_msg:
            print("📡 Error de API de Binance")
            telegram_msg = f"📡 Error de API: {error_msg[:100]}..."
        else:
            telegram_msg = f"⚠️ Error en estrategia: {error_msg[:100]}..."
        
        try:
            send_telegram_message(telegram_msg)
        except:
            print("No se pudo enviar notificación por Telegram")
        
        # Pausa más larga en caso de errores de conectividad
        if "<!DOCTYPE html>" in error_msg or "connection" in error_msg.lower():
            print("⏸️ Pausa extendida de 5 minutos debido a problemas de conectividad")
            time.sleep(300)  # 5 minutos