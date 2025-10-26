#!/usr/bin/env python3
import requests
import json
from datetime import datetime

ASSETS = {
    'ETH': 'ETHUSDT',
    'BTC': 'BTCUSDT', 
    'SOL': 'SOLUSDT',
    'XRP': 'XRPUSDT'
}

def get_price(symbol):
    try:
        response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=10)
        if response.status_code == 200:
            return float(response.json()['price'])
    except:
        pass
    return None

def create_signal(asset, price):
    levels = {
        'ETH': {'level': 50, 'threshold': 25},
        'BTC': {'level': 1000, 'threshold': 500}, 
        'SOL': {'level': 5, 'threshold': 2},
        'XRP': {'level': 0.1, 'threshold': 0.05}
    }
    
    config = levels[asset]
    price_level = round(price / config['level']) * config['level']
    
    if price > price_level + config['threshold']:
        action = 'BUY'
        strategy = 'Bull Call Spread'
        long_strike = price_level
        short_strike = price_level + (config['level'] * 4)
    elif price < price_level - config['threshold']:
        action = 'SELL'
        strategy = 'Bear Put Spread'
        long_strike = price_level
        short_strike = price_level - (config['level'] * 4)
    else:
        return None
    
    return {
        'asset': asset,
        'action': action,
        'strategy': strategy,
        'price': price,
        'long_strike': long_strike,
        'short_strike': short_strike,
        'expiry': '29NOV24'
    }

def send_signal(signals):
    if not signals:
        return False
    
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = "OPTIONS SIGNALS\n\n"
        
        for signal in signals:
            message += f"""{signal['asset']} {signal['action']}: {signal['strategy']}
Price: ${signal['price']:,.4f}
Strikes: {signal['long_strike']:.4f}/{signal['short_strike']:.4f}
Expiry: {signal['expiry']}

"""
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        print(f"Signal sent: {response.status_code}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=== ETH, BTC, SOL, XRP Options ===")
    
    signals = []
    
    for asset, symbol in ASSETS.items():
        price = get_price(symbol)
        if price:
            print(f"{asset}: ${price:,.4f}")
            signal = create_signal(asset, price)
            if signal:
                signals.append(signal)
                print(f"  Signal: {signal['action']}")
        else:
            print(f"{asset}: Failed")
    
    if signals:
        result = send_signal(signals)
        print(f"Sent: {result}")
    else:
        print("No signals - testing with forced signals...")
        
        # Принудительный тест
        test_signals = [
            create_signal('ETH', 4100),
            create_signal('BTC', 75000), 
            create_signal('SOL', 200),
            create_signal('XRP', 3.0)
        ]
        
        test_signals = [s for s in test_signals if s]
        if test_signals:
            print(f"Sending {len(test_signals)} test signals")
            send_signal(test_signals)

if __name__ == "__main__":
    main()
