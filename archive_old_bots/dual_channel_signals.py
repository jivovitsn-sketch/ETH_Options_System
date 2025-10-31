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

def create_signals(asset, price):
    levels = {
        'ETH': {'base': 3900, 'range': 100},
        'BTC': {'base': 70000, 'range': 2000},
        'SOL': {'base': 180, 'range': 20}, 
        'XRP': {'base': 2.5, 'range': 0.3}
    }
    
    config = levels[asset]
    
    if price > config['base'] + config['range']:
        return {'action': 'BUY', 'reason': f"Breakout above {config['base'] + config['range']}"}
    elif price < config['base'] - config['range']:
        return {'action': 'SELL', 'reason': f"Breakdown below {config['base'] - config['range']}"}
    
    return None

def send_to_both_channels(signals):
    if not signals:
        return
    
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        # VIP сообщение (детальное)
        vip_message = f"🔥 VIP OPTIONS SIGNALS\n\n"
        for signal in signals:
            vip_message += f"""🎯 {signal['asset']} {signal['action']}
Strategy: Bull Call Spread
Price: ${signal['price']:,.2f}
Reason: {signal['reason']}
Expected ROI: 45%
Position Size: 3% max

"""
        vip_message += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n💎 VIP Exclusive Analysis"
        
        # FREE сообщение (базовое)
        free_message = f"📊 CRYPTO SIGNALS\n\n"
        for signal in signals:
            free_message += f"{signal['asset']}: {signal['action']} @ ${signal['price']:,.2f}\n"
        free_message += f"\n⏰ {datetime.now().strftime('%H:%M')}\n💡 Basic signals - Upgrade to VIP for detailed analysis"
        
        # Отправляем в VIP канал
        send_to_channel(config, 'vip', vip_message)
        
        # Отправляем в FREE канал  
        send_to_channel(config, 'free', free_message)
        
    except Exception as e:
        print(f"Error: {e}")

def send_to_channel(config, channel_type, message):
    try:
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels'][channel_type],
            'text': message
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Signal sent to {channel_type.upper()} channel")
        else:
            print(f"❌ Failed to send to {channel_type}: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error sending to {channel_type}: {e}")

def main():
    print(f"=== Dual Channel Signals: {datetime.now().strftime('%H:%M')} ===")
    
    signals = []
    
    for asset, symbol in ASSETS.items():
        price = get_price(symbol)
        if price:
            print(f"{asset}: ${price:,.2f}")
            signal = create_signals(asset, price)
            if signal:
                signal['asset'] = asset
                signal['price'] = price
                signals.append(signal)
                print(f"  -> {signal['action']} signal")
    
    if signals:
        print(f"\nSending {len(signals)} signals to both channels...")
        send_to_both_channels(signals)
    else:
        print("No signals generated")

if __name__ == "__main__":
    main()
