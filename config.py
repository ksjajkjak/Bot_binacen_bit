
import os

# Binance API credentials - Ahora desde Secrets
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Telegram configuration - Ahora desde Secrets  
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# CryptoPanic API - Ahora desde Secrets
CRYPTOPANIC_API_KEY = os.getenv('CRYPTOPANIC_API_KEY')

# Trading parameters
SYMBOL = 'SOLUSDT'  # Par de trading SOL/USDT
LEVERAGE = 20       # Apalancamiento x20 para margen cruzado

# Scalping parameters
SCALPING_TP = 0.008  # Take profit 0.8%
SCALPING_SL = 0.004  # Stop loss 0.4%

QTY = 0.1         # Cantidad base de SOL
