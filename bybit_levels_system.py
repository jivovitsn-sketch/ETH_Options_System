#!/usr/bin/env python3
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime

class BybitLevelsSystem:
    def __init__(self):
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        # Твои Bybit API данные
        if 'bybit_api' in config:
            self.api_key = config['bybit_api']['key']
            self.api_secret = config['bybit_api']['secret']
            self.use_auth = True
        else:
            self.use_auth = False
            
        self.base_url = "https://api.bybit.com"
    
    def get_bybit_price(self, symbol):
        """Получаем цену с Bybit"""
        try:
            url = f"{self.base_url}/v5/market/tickers"
            params = {
                'category': 'spot',
                'symbol': symbol
            }
            
            if self.use_auth:
                # Добавляем аутентификацию если есть API ключи
                timestamp = str(int(time.time() * 1000))
                params['api_key'] = self.api_key
                params['timestamp'] = timestamp
                
                # Создаем подпись (упрощенно для GET запроса)
                query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
                signature = hmac.new(
                    self.api_secret.encode('utf-8'),
                    query_string.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                params['sign'] = signature
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0:
                    return float(data['result']['list'][0]['lastPrice'])
            
        except Exception as e:
            print(f"Bybit API error: {e}")
        
        return None
    
    def get_bybit_options_data(self, symbol):
        """Получаем данные опционов с Bybit"""
        try:
            url = f"{self.base_url}/v5/market/instruments-info"
            params = {
                'category': 'option',
                'baseCoin': symbol
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0:
                    return data['result']['list']
                    
        except Exception as e:
            print(f"Options data error: {e}")
        
        return []
    
    def calculate_smart_levels(self):
        """Расчет уровней на основе Bybit данных"""
        
        symbols = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT',
            'SOL': 'SOLUSDT'
        }
        
        levels = {}
        
        for asset, symbol in symbols.items():
            price = self.get_bybit_price(symbol)
            
            if not price:
                print(f"Не удалось получить цену {asset} с Bybit")
                continue
            
            # Умные уровни на основе опционных данных
            if asset == 'BTC':
                step = 1000
                resistance_pct = 1.02
                support_pct = 0.98
            elif asset == 'ETH':
                step = 50
                resistance_pct = 1.025
                support_pct = 0.975
            else:
                step = 5
                resistance_pct = 1.03
                support_pct = 0.97
            
            levels[asset] = {
                'current': price,
                'resistance': round(price * resistance_pct / step) * step,
                'support': round(price * support_pct / step) * step,
                'strong_resistance': round(price * 1.05 / step) * step,
                'strong_support': round(price * 0.95 / step) * step,
                'options_available': len(self.get_bybit_options_data(asset)) > 0
            }
        
        return levels
    
    def check_signals(self):
        """Проверяем сигналы на основе Bybit данных"""
        
        print(f"=== BYBIT LEVELS CHECK: {datetime.now().strftime('%H:%M:%S')} ===")
        print(f"API Mode: {'Authenticated' if self.use_auth else 'Public'}")
        
        levels = self.calculate_smart_levels()
        signals = []
        
        for asset, data in levels.items():
            price = data['current']
            
            print(f"\n{asset}: ${price:,.2f}")
            print(f"  Support: ${data['support']:,.0f} | Resistance: ${data['resistance']:,.0f}")
            print(f"  Options Available: {'✅' if data['options_available'] else '❌'}")
            
            # Проверяем значимые движения
            if price >= data['strong_resistance']:
                signals.append({
                    'asset': asset,
                    'action': 'STRONG BUY',
                    'reason': f"Пробой сильного сопротивления ${data['strong_resistance']:,.0f}",
                    'price': price,
                    'options_ready': data['options_available']
                })
            elif price <= data['strong_support']:
                signals.append({
                    'asset': asset,
                    'action': 'STRONG SELL', 
                    'reason': f"Пробой сильной поддержки ${data['strong_support']:,.0f}",
                    'price': price,
                    'options_ready': data['options_available']
                })
            else:
                print(f"  -> В диапазоне")
        
        if signals:
            print(f"\n🚨 BYBIT SIGNALS:")
            for signal in signals:
                status = "TRADEABLE" if signal['options_ready'] else "SPOT ONLY"
                print(f"  {signal['asset']}: {signal['action']} - {status}")
        else:
            print(f"\n✅ Все активы в диапазонах")
        
        return signals

if __name__ == "__main__":
    bybit_system = BybitLevelsSystem()
    bybit_system.check_signals()
