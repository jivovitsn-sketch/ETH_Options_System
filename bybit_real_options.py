#!/usr/bin/env python3
import requests
import json
from datetime import datetime

class BybitRealOptions:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
    
    def get_real_options_data(self, coin='BTC'):
        """Получаем РЕАЛЬНУЮ опционную доску с Bybit"""
        
        try:
            # Инструменты опционов
            url = f"{self.base_url}/v5/market/instruments-info"
            params = {
                'category': 'option',
                'baseCoin': coin
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0:
                    return data['result']['list']
            
        except Exception as e:
            print(f"Error getting options: {e}")
        
        return []
    
    def get_real_option_prices(self, symbols):
        """Получаем реальные цены опционов"""
        
        try:
            url = f"{self.base_url}/v5/market/tickers"
            params = {
                'category': 'option'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0:
                    prices = {}
                    for ticker in data['result']['list']:
                        if ticker['symbol'] in symbols:
                            prices[ticker['symbol']] = {
                                'bid': float(ticker['bid1Price']) if ticker['bid1Price'] else 0,
                                'ask': float(ticker['ask1Price']) if ticker['ask1Price'] else 0,
                                'last': float(ticker['lastPrice']) if ticker['lastPrice'] else 0,
                                'volume': float(ticker['volume24h']) if ticker['volume24h'] else 0
                            }
                    return prices
            
        except Exception as e:
            print(f"Error getting prices: {e}")
        
        return {}
    
    def analyze_real_market(self):
        """Анализ реального опционного рынка"""
        
        print("=== REAL BYBIT OPTIONS ANALYSIS ===")
        
        # Получаем доступные опционы
        options = self.get_real_options_data('BTC')
        
        if not options:
            print("Нет данных по опционам BTC")
            return
        
        print(f"Найдено {len(options)} опционных инструментов BTC")
        
        # Группируем по экспирациям
        expirations = {}
        for opt in options:
            exp_date = opt['deliveryTime']
            if exp_date not in expirations:
                expirations[exp_date] = {'calls': [], 'puts': []}
            
            if opt['optionsType'] == 'Call':
                expirations[exp_date]['calls'].append(opt)
            else:
                expirations[exp_date]['puts'].append(opt)
        
        print(f"\nДоступные экспирации: {len(expirations)}")
        
        # Анализируем ближайшую экспирацию
        nearest_exp = min(expirations.keys())
        exp_data = expirations[nearest_exp]
        
        exp_date = datetime.fromtimestamp(int(nearest_exp)/1000)
        print(f"\nБлижайшая экспирация: {exp_date.strftime('%Y-%m-%d')}")
        print(f"Calls: {len(exp_data['calls'])}")
        print(f"Puts: {len(exp_data['puts'])}")
        
        # Получаем реальные цены для анализа
        symbols_to_check = []
        for call in exp_data['calls'][:10]:  # Первые 10 коллов
            symbols_to_check.append(call['symbol'])
        
        real_prices = self.get_real_option_prices(symbols_to_check)
        
        print(f"\nРеальные цены опционов:")
        for symbol, price_data in real_prices.items():
            if price_data['bid'] > 0 and price_data['ask'] > 0:
                spread = price_data['ask'] - price_data['bid']
                spread_pct = (spread / price_data['ask']) * 100
                print(f"{symbol}:")
                print(f"  Bid: ${price_data['bid']:,.0f} | Ask: ${price_data['ask']:,.0f}")
                print(f"  Spread: ${spread:,.0f} ({spread_pct:.1f}%)")
                print(f"  Volume 24h: {price_data['volume']:,.0f}")
        
        return {
            'options_available': len(options),
            'expirations': len(expirations),
            'nearest_expiry': exp_date,
            'real_prices': real_prices
        }

if __name__ == "__main__":
    bybit = BybitRealOptions()
    bybit.analyze_real_market()
