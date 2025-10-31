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
    # УПРОЩЕННАЯ ЛОГИКА - более чувствительная
    levels = {
        'ETH': {'base': 3900, 'range': 100},
        'BTC': {'base': 70000, 'range': 2000},
        'SOL': {'base': 180, 'range': 20}, 
        'XRP': {'base': 2.5, 'range': 0.3}
    }
    
    config = levels[asset]
    
    if price > config['base'] + config['range']:
        return {
            'asset': asset,
            'action': 'BUY',
            'strategy': 'Bull Call Spread',
            'price': price,
            'signal_reason': f"Price {price} > {config['base'] + config['range']}"
        }
    elif price < config['base'] - config['range']:
        return {
            'asset': asset,
            'action': 'SELL',
            'strategy': 'Bear Put Spread', 
            'price': price,
            'signal_reason': f"Price {price} < {config['base'] - config['range']}"
        }
    
    return None

def send_signals(signals):
    if not signals:
        return False
    
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = f"🎯 CRYPTO OPTIONS SIGNALS\n\n"
        
        for signal in signals:
            message += f"""📊 {signal['asset']} {signal['action']}
Strategy: {signal['strategy']}
Price: ${signal['price']:,.2f}
Reason: {signal['signal_reason']}

"""
        
        message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        print(f"Signals sent: {response.status_code}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=== Multi-Asset Options System ===")
    
    signals = []
    
    for asset, symbol in ASSETS.items():
        price = get_price(symbol)
        if price:
            print(f"{asset}: ${price:,.2f}")
            signal = create_signal(asset, price)
            if signal:
                signals.append(signal)
                print(f"  -> {signal['action']} signal")
            else:
                print(f"  -> No signal")
    
    if signals:
        print(f"\nSending {len(signals)} signals...")
        send_signals(signals)
    else:
        print("\nNo real signals, sending test...")
        test_signals = [
            {'asset': 'ETH', 'action': 'BUY', 'strategy': 'Bull Call', 'price': 4000, 'signal_reason': 'Test signal'},
            {'asset': 'BTC', 'action': 'SELL', 'strategy': 'Bear Put', 'price': 70000, 'signal_reason': 'Test signal'}
        ]
        send_signals(test_signals)

if __name__ == "__main__":
    main()
