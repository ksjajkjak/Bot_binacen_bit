
import numpy as np
from collections import deque

class SimpleMarketAI:
    """
    IA ligera para análisis de mercado basada en estadísticas simples:
    pendiente, momentum y volatilidad. No afecta decisiones de trading,
    solo proporciona información.
    """

    def __init__(self, window_size=14):
        self.window_size = window_size
        self.price_memory = deque(maxlen=window_size)
        self.trend_memory = deque(maxlen=5)

    def analyze_trend(self, prices):
        """Analiza tendencia usando pendiente lineal, momentum y volatilidad"""
        if len(prices) < self.window_size:
            return "NEUTRAL", 0.5, "Datos insuficientes"

        prices = np.array(prices)
        x = np.arange(len(prices))

        # Cálculo de la pendiente (dirección de la tendencia)
        slope, _ = np.polyfit(x, prices, 1)

        # Volatilidad relativa (std / media)
        volatility = np.std(prices) / np.mean(prices)

        # Momentum = cambio porcentual entre los últimos y primeros precios
        momentum = np.mean(prices[-3:]) / np.mean(prices[:3]) - 1

        # Análisis
        message = []
        if slope > 0 and momentum > 0.005:
            trend = "BULLISH"
            confidence = min(0.5 + abs(momentum) * 50, 0.95)
            message.append(f"Tendencia alcista (momentum: {momentum*100:.2f}%)")
        elif slope < 0 and momentum < -0.005:
            trend = "BEARISH"
            confidence = min(0.5 + abs(momentum) * 50, 0.95)
            message.append(f"Tendencia bajista (momentum: {momentum*100:.2f}%)")
        else:
            trend = "NEUTRAL"
            confidence = 0.5
            message.append("Mercado en rango/neutral")

        # Volatilidad informativa
        if volatility > 0.02:
            message.append(f"Alta volatilidad ({volatility*100:.2f}%)")
        else:
            message.append(f"Baja volatilidad ({volatility*100:.2f}%)")

        # Evaluación de cambios recientes
        self.trend_memory.append(trend)
        if len(self.trend_memory) >= 3:
            if self.trend_memory[-1] != self.trend_memory[-2] and self.trend_memory[-2] == self.trend_memory[-3]:
                message.append("⚠️ Posible cambio de tendencia detectado")

        return trend, confidence, " | ".join(message)

    def update(self, price):
        """Añade un nuevo precio a la memoria"""
        self.price_memory.append(price)

    def get_insight(self):
        """Devuelve análisis actual del mercado"""
        if len(self.price_memory) < self.window_size:
            return "Acumulando datos...", 0.0

        trend, confidence, message = self.analyze_trend(list(self.price_memory))
        return message, confidence
