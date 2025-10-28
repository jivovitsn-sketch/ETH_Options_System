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
        
        if 'bybit_api' in config:
            self.api_key = config['bybit_api']['key']
            self.api_secret = config['bybit_api']['secret']
            self.use_auth = True
        else:
            self.use_auth = False
            
        self.base_url = "https://api.bybit.com"
    
    def get_bybit_price(self, symbol):
        try:
            url = f"{self.base_url}/v5/market/tickers"
            params = {
                'category': 'spot',
                'symbol': symbol
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0:
                    return float(data['result']['list'][0]['lastPrice'])
            
        except Exception as e:
            print(f"Bybit API error: {e}")
        
        return None
    
    def calculate_smart_levels(self):
        # ДОБАВЛЯЕМ XRP
        symbols = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT',
            'SOL': 'SOLUSDT',
            'XRP': 'XRPUSDT'  # Вот он!
        }
        
        levels = {}
        
        for asset, symbol in symbols.items():
            price = self.get_bybit_price(symbol)
            
            if not price:
                print(f"Не удалось получить цену {asset} с Bybit")
                continue
            
            # Настройки по активам
            if asset == 'BTC':
                step = 1000
                resistance_pct = 1.02
                support_pct = 0.98
            elif asset == 'ETH':
                step = 50
                resistance_pct = 1.025
                support_pct = 0.975
            elif asset == 'SOL':
                step = 5
                resistance_pct = 1.03
                support_pct = 0.97
            elif asset == 'XRP':
                step = 0.1
                resistance_pct = 1.03
                support_pct = 0.97
            
            levels[asset] = {
                'current': price,
                'resistance': round(price * resistance_pct / step) * step,
                'support': round(price * support_pct / step) * step,
                'strong_resistance': round(price * 1.05 / step) * step,
                'strong_support': round(price * 0.95 / step) * step
            }
        
        return levels
    
    def check_signals(self):
        print(f"=== BYBIT LEVELS CHECK (все 4 актива): {datetime.now().strftime('%H:%M:%S')} ===")
        print(f"API Mode: {'Authenticated' if self.use_auth else 'Public'}")
        
        levels = self.calculate_smart_levels()
        signals = []
        
        for asset, data in levels.items():
            price = data['current']
            
            print(f"\n{asset}: ${price:,.4f}")
            print(f"  Support: ${data['support']:,.4f} | Resistance: ${data['resistance']:,.4f}")
            
            # Проверяем значимые движения
            if price >= data['strong_resistance']:
                signals.append({
                    'asset': asset,
                    'action': 'STRONG BUY',
                    'reason': f"Пробой сильного сопротивления ${data['strong_resistance']:,.4f}",
                    'price': price
                })
            elif price <= data['strong_support']:
                signals.append({
                    'asset': asset,
                    'action': 'STRONG SELL', 
                    'reason': f"Пробой сильной поддержки ${data['strong_support']:,.4f}",
                    'price': price
                })
            else:
                print(f"  -> В диапазоне")
        
        if signals:
            print(f"\n🚨 BYBIT SIGNALS:")
            for signal in signals:
                print(f"  {signal['asset']}: {signal['action']}")
                print(f"     {signal['reason']}")
        else:
            print(f"\n✅ Все 4 актива в диапазонах")
        
        return signals

if __name__ == "__main__":
    bybit_system = BybitLevelsSystem()
    bybit_system.check_signals()
