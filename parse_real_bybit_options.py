#!/usr/bin/env python3
import requests
import re
from datetime import datetime

def parse_option_symbol(symbol):
    """Парсим страйк и тип из символа"""
    # BTC-25SEP26-90000-P-USDT
    match = re.match(r'([A-Z]+)-(\d{2}[A-Z]{3}\d{2})-(\d+)-([CP])-([A-Z]+)', symbol)
    
    if match:
        asset, expiry_str, strike, opt_type, currency = match.groups()
        return {
            'asset': asset,
            'expiry': expiry_str,
            'strike': int(strike),
            'type': 'Call' if opt_type == 'C' else 'Put',
            'currency': currency
        }
    return None

def analyze_real_bybit_options():
    base_url = "https://api.bybit.com"
    
    print("=== РЕАЛЬНЫЙ АНАЛИЗ BYBIT ОПЦИОНОВ ===")
    
    # Получаем BTC спот
    spot_response = requests.get(f"{base_url}/v5/market/tickers", 
                                params={'category': 'spot', 'symbol': 'BTCUSDT'})
    btc_price = float(spot_response.json()['result']['list'][0]['lastPrice'])
    print(f"BTC Spot: ${btc_price:,.0f}")
    
    # Получаем опционы
    options_response = requests.get(f"{base_url}/v5/market/instruments-info",
                                   params={'category': 'option', 'baseCoin': 'BTC'})
    
    options = options_response.json()['result']['list']
    
    # Парсим и группируем
    parsed_options = []
    for opt in options:
        parsed = parse_option_symbol(opt['symbol'])
        if parsed:
            parsed['symbol'] = opt['symbol']
            parsed['status'] = opt['status']
            parsed['deliveryTime'] = opt['deliveryTime']
            parsed_options.append(parsed)
    
    print(f"Распарсено опционов: {len(parsed_options)}")
    
    # Группируем по экспирациям
    expirations = {}
    for opt in parsed_options:
        exp = opt['expiry']
        if exp not in expirations:
            expirations[exp] = []
        expirations[exp].append(opt)
    
    print(f"Доступные экспирации: {list(expirations.keys())}")
    
    # Анализируем ближайшую экспирацию
    nearest_exp = min(expirations.keys())
    nearest_options = expirations[nearest_exp]
    
    print(f"\nБлижайшая экспирация: {nearest_exp}")
    
    # Ищем ATM опционы (в пределах 10% от спота)
    atm_options = []
    for opt in nearest_options:
        strike_diff_pct = abs(opt['strike'] - btc_price) / btc_price
        if strike_diff_pct < 0.1:  # В пределах 10%
            atm_options.append(opt)
    
    print(f"ATM опционы (±10%): {len(atm_options)}")
    
    # Показываем структуру для торговли
    calls = [opt for opt in atm_options if opt['type'] == 'Call']
    puts = [opt for opt in atm_options if opt['type'] == 'Put']
    
    print(f"Calls: {len(calls)}, Puts: {len(puts)}")
    
    # Bull Call Spread возможности
    calls_sorted = sorted(calls, key=lambda x: x['strike'])
    if len(calls_sorted) >= 2:
        print(f"\nВозможные Bull Call Spreads:")
        for i in range(len(calls_sorted)-1):
            long_call = calls_sorted[i]
            short_call = calls_sorted[i+1]
            spread_width = short_call['strike'] - long_call['strike']
            
            print(f"  Long ${long_call['strike']:,} / Short ${short_call['strike']:,}")
            print(f"  Ширина: ${spread_width:,}")
    
    # Проверяем реальные цены
    print(f"\nПроверяем ликвидность...")
    symbols_to_check = [opt['symbol'] for opt in atm_options[:5]]
    
    prices_response = requests.get(f"{base_url}/v5/market/tickers",
                                 params={'category': 'option'})
    
    if prices_response.status_code == 200:
        all_prices = prices_response.json()['result']['list']
        
        liquid_options = 0
        for ticker in all_prices:
            if ticker['symbol'] in symbols_to_check:
                bid = float(ticker['bid1Price']) if ticker['bid1Price'] else 0
                ask = float(ticker['ask1Price']) if ticker['ask1Price'] else 0
                volume = float(ticker['volume24h']) if ticker['volume24h'] else 0
                
                if bid > 0 and ask > 0:
                    liquid_options += 1
                    spread_pct = ((ask - bid) / ask) * 100
                    print(f"  {ticker['symbol']}")
                    print(f"    Bid/Ask: ${bid:,.0f}/${ask:,.0f} (спред {spread_pct:.1f}%)")
                    print(f"    Volume 24h: {volume:,.2f}")
        
        print(f"\nЛиквидных опционов: {liquid_options}/{len(symbols_to_check)}")
        
        if liquid_options == 0:
            print("⚠️  ПРОБЛЕМА: Нет ликвидности в ATM опционах!")
            print("   Возможно нужно использовать Deribit или другую биржу")

if __name__ == "__main__":
    analyze_real_bybit_options()
