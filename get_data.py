
from binance.client import Client
import pandas as pd
import time
from config import API_KEY, API_SECRET

# Cliente de Binance con configuración correcta
client = Client(
    API_KEY, 
    API_SECRET,
    testnet=False
)

def get_klines(symbol, interval, limit=100):
    """
    Obtiene datos OHLC (velas) de Binance con manejo de límites de API.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Usar futures_klines para datos de futuros
            raw = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            
            df = pd.DataFrame(raw, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "number_of_trades",
                "taker_buy_base", "taker_buy_quote", "ignore"
            ])

            # Conversión de columnas necesarias
            df = df.astype({
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float
            })

            # Convertir tiempo a datetime
            df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
            df.set_index("open_time", inplace=True)

            return df[["open", "high", "low", "close", "volume"]]

        except Exception as e:
            if "429" in str(e) or "418" in str(e):  # Rate limit
                wait_time = 30 * (attempt + 1)
                print(f"⚠️ Límite de API en get_klines. Esperando {wait_time}s")
                time.sleep(wait_time)
                continue
            else:
                print(f"Error al obtener datos de Binance: {str(e)}")
                if attempt == max_retries - 1:
                    return pd.DataFrame()
                
    return pd.DataFrame()
