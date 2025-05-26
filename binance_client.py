
from binance.client import Client
from binance.enums import *
from config import API_KEY, API_SECRET, SYMBOL, LEVERAGE, QTY
import time

class BinanceClient:
    def __init__(self):
        # Configurar cliente con endpoints correctos para futuros
        self.client = Client(
            API_KEY, 
            API_SECRET,
            testnet=False
        )
        
        # Verificar conexión con reintentos
        self._verify_connection()
        
        # Configurar apalancamiento con manejo de errores
        self._setup_leverage()
    
    def _verify_connection(self):
        """Verificar conexión con Binance con reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Test básico de conectividad
                server_time = self.client.futures_time()
                print(f"✅ Conectado a Binance Futures. Hora del servidor: {server_time}")
                
                # Verificar que podemos obtener información del símbolo
                exchange_info = self.client.futures_exchange_info()
                symbol_found = any(s['symbol'] == SYMBOL for s in exchange_info['symbols'])
                
                if not symbol_found:
                    raise Exception(f"Símbolo {SYMBOL} no encontrado en Binance Futures")
                
                print(f"✅ Símbolo {SYMBOL} verificado")
                return
                
            except Exception as e:
                error_msg = str(e)
                if "<!DOCTYPE html>" in error_msg:
                    print(f"❌ Error HTML recibido de Binance (intento {attempt+1}/{max_retries})")
                    print("Esto puede indicar restricciones geográficas o de IP")
                elif "APIError" in error_msg:
                    print(f"❌ Error de API: {error_msg}")
                else:
                    print(f"❌ Error de conexión: {error_msg}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    print(f"Reintentando en {wait_time} segundos...")
                    time.sleep(wait_time)
                else:
                    print("❌ No se pudo establecer conexión con Binance después de varios intentos")
                    raise Exception("Conexión fallida - verifica tu conexión a internet y configuración de API")
    
    def _setup_leverage(self):
        """Configurar apalancamiento con manejo de errores"""
        try:
            self.client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)
            print(f"✅ Apalancamiento configurado: {LEVERAGE}x para {SYMBOL}")
        except Exception as e:
            error_msg = str(e)
            if "leverage not modified" in error_msg.lower():
                print(f"ℹ️ Apalancamiento ya estaba en {LEVERAGE}x")
            else:
                print(f"⚠️ Error al configurar apalancamiento: {error_msg}")
                print("El bot continuará, pero verifica manualmente el apalancamiento")

    def get_price(self):
        """Obtener precio con manejo robusto de errores"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                price = self.client.futures_mark_price(symbol=SYMBOL)
                return float(price['markPrice'])
            except Exception as e:
                error_msg = str(e)
                
                if "<!DOCTYPE html>" in error_msg:
                    print(f"⚠️ Respuesta HTML recibida en lugar de JSON (intento {attempt+1}/{max_retries})")
                    print("Posible bloqueo geográfico o problema de conectividad")
                    wait_time = 30 * (attempt + 1)
                elif "429" in error_msg or "418" in error_msg:
                    print(f"⚠️ Límite de API excedido (intento {attempt+1}/{max_retries})")
                    wait_time = 60 * (attempt + 1)
                elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    print(f"⚠️ Problema de conexión (intento {attempt+1}/{max_retries})")
                    wait_time = 15 * (attempt + 1)
                else:
                    print(f"⚠️ Error desconocido: {error_msg}")
                    wait_time = 20 * (attempt + 1)
                
                if attempt < max_retries - 1:
                    print(f"Esperando {wait_time}s antes del siguiente intento...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"No se pudo obtener precio después de {max_retries} intentos: {error_msg}")
        
        raise Exception("Límite de reintentos excedido")

    def get_last_prices(self, limit=5):
        klines = self.client.futures_klines(symbol=SYMBOL, interval='5m', limit=limit)
        return [float(k[4]) for k in klines]

    def get_symbol_info(self):
        info = self.client.futures_exchange_info()
        for symbol_info in info['symbols']:
            if symbol_info['symbol'] == SYMBOL:
                return symbol_info
        return None

    def validar_cantidad(self, precio, cantidad, max_valor_orden=11.72):
        symbol_info = self.get_symbol_info()
        step_size = 0.001
        min_qty = 0.001

        if symbol_info:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    step_size = float(filter['stepSize'])
                    min_qty = float(filter['minQty'])
                    break

        min_order_value = 5
        cantidad_minima_valor = min_order_value / precio
        cantidad_minima = max(cantidad_minima_valor, min_qty)
        cantidad_maxima_valor = max_valor_orden / precio

        if cantidad < cantidad_minima:
            print(f"Cantidad muy pequeña. Ajustando a mínima permitida: {cantidad_minima}")
            cantidad = cantidad_minima

        if cantidad > cantidad_maxima_valor:
            print(f"Cantidad excede el saldo disponible. Ajustando a máxima permitida: {cantidad_maxima_valor}")
            cantidad = cantidad_maxima_valor

        # Redondear cantidad al step_size
        cantidad = (cantidad // step_size) * step_size
        cantidad = round(cantidad, 8)

        valor_orden = cantidad * precio
        if valor_orden < min_order_value:
            print(f"Valor de orden ({valor_orden:.2f} USDT) menor que mínimo ({min_order_value} USDT). No se puede ejecutar.")
            return 0

        if valor_orden > max_valor_orden:
            print(f"Valor de orden ({valor_orden:.2f} USDT) mayor que límite disponible ({max_valor_orden} USDT). Ajustando.")
            cantidad = max_valor_orden / precio
            cantidad = (cantidad // step_size) * step_size
            cantidad = round(cantidad, 8)
            valor_orden = cantidad * precio

        print(f"Cantidad validada: {cantidad} ({valor_orden:.2f} USDT)")
        return cantidad

    def calcular_cantidad_optima(self, precio, max_valor_orden=11.0):
        symbol_info = self.get_symbol_info()
        step_size = 0.001
        min_qty = 0.001

        if symbol_info:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    step_size = float(filter['stepSize'])
                    min_qty = float(filter['minQty'])
                    break

        min_order_value = 1.0
        cantidad_minima = max(min_order_value / precio, min_qty)
        cantidad_maxima = max_valor_orden / precio

        if cantidad_minima > cantidad_maxima:
            print(f"No se puede calcular cantidad óptima: mínimo requerido excede saldo disponible.")
            return 0

        cantidad_optima = cantidad_maxima * 0.90
        cantidad_optima = (cantidad_optima // step_size) * step_size
        cantidad_optima = round(cantidad_optima, 8)

        valor_orden = cantidad_optima * precio
        print(f"Cantidad óptima calculada: {cantidad_optima} ({valor_orden:.2f} USDT)")

        return cantidad_optima

    def place_market_order(self, side, quantity):
        precio_actual = self.get_price()
        cantidad_validada = self.validar_cantidad(precio_actual, quantity)

        symbol_info = self.get_symbol_info()
        quantity_precision = 0

        if symbol_info:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    quantity_precision = len(str(filter['stepSize']).rstrip('0').split('.')[1]) if '.' in str(filter['stepSize']) else 0

        formatted_qty = f"{float(cantidad_validada):.{quantity_precision}f}"

        print(f"Orden de mercado: {side} {formatted_qty} {SYMBOL} a precio ~{precio_actual}")

        if float(cantidad_validada) <= 0:
            print("⚠️ La cantidad es demasiado pequeña o supera el saldo. No se ejecutó la orden.")
            return None

        try:
            return self.client.futures_create_order(
                symbol=SYMBOL,
                side=SIDE_BUY if side == "BUY" else SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=formatted_qty
            )
        except Exception as e:
            print(f"Error al ejecutar orden de mercado: {e}")
            if "APIError(code=-4164)" in str(e):
                print("⚠️ Error de valor mínimo de orden. Revisa tu saldo y configuración.")
            return None

    def place_limit_order(self, side, quantity, price):
        cantidad_validada = self.validar_cantidad(price, quantity)

        symbol_info = self.get_symbol_info()
        price_precision = 3
        quantity_precision = 0

        if symbol_info:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'PRICE_FILTER':
                    price_precision = len(str(filter['tickSize']).rstrip('0').split('.')[1]) if '.' in str(filter['tickSize']) else 0
                if filter['filterType'] == 'LOT_SIZE':
                    quantity_precision = len(str(filter['stepSize']).rstrip('0').split('.')[1]) if '.' in str(filter['stepSize']) else 0

        formatted_price = f"{price:.{price_precision}f}"
        formatted_qty = f"{float(cantidad_validada):.{quantity_precision}f}"

        print(f"Orden límite: {side} {formatted_qty} {SYMBOL} a precio {formatted_price}")

        if float(cantidad_validada) <= 0:
            print("⚠️ La cantidad es demasiado pequeña o supera el saldo. No se ejecutó la orden.")
            return None

        try:
            return self.client.futures_create_order(
                symbol=SYMBOL,
                side=SIDE_BUY if side == "BUY" else SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=formatted_qty,
                price=formatted_price
            )
        except Exception as e:
            print(f"Error al ejecutar orden límite: {e}")
            if "APIError(code=-4164)" in str(e):
                print("⚠️ Error de valor mínimo de orden. Revisa tu saldo y configuración.")
            return None

    def set_tp_sl(self, side, tp_price, sl_price):
        try:
            time.sleep(1)

            qty = self.get_position_qty()
            if qty <= 0:
                print("No hay posición abierta para configurar TP/SL")
                return

            symbol_info = self.get_symbol_info()
            price_precision = 3
            quantity_precision = 0

            if symbol_info:
                for filter in symbol_info['filters']:
                    if filter['filterType'] == 'PRICE_FILTER':
                        price_precision = len(str(filter['tickSize']).rstrip('0').split('.')[1]) if '.' in str(filter['tickSize']) else 0
                    if filter['filterType'] == 'LOT_SIZE':
                        quantity_precision = len(str(filter['stepSize']).rstrip('0').split('.')[1]) if '.' in str(filter['stepSize']) else 0

            formatted_qty = f"{qty:.{quantity_precision}f}"

            if tp_price:
                formatted_tp = f"{tp_price:.{price_precision}f}"
                try:
                    self.client.futures_create_order(
                        symbol=SYMBOL,
                        side=SIDE_SELL if side == "BUY" else SIDE_BUY,
                        type=ORDER_TYPE_LIMIT,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=formatted_qty,
                        price=formatted_tp,
                        reduceOnly=True
                    )
                    print(f"TP establecido correctamente a {formatted_tp}")
                except Exception as e:
                    print(f"Error al establecer TP: {e}")

            if sl_price:
                formatted_sl = f"{sl_price:.{price_precision}f}"
                try:
                    self.client.futures_create_order(
                        symbol=SYMBOL,
                        side=SIDE_SELL if side == "BUY" else SIDE_BUY,
                        type=ORDER_TYPE_STOP_MARKET,
                        stopPrice=formatted_sl,
                        quantity=formatted_qty,
                        reduceOnly=True
                    )
                    print(f"SL establecido correctamente a {formatted_sl}")
                except Exception as e:
                    print(f"Error al establecer SL: {e}")
        except Exception as e:
            print(f"Error general en TP/SL: {e}")

    def get_position_qty(self):
        positions = self.client.futures_position_information(symbol=SYMBOL)
        for p in positions:
            if float(p['positionAmt']) != 0:
                return abs(float(p['positionAmt']))
        return 0
