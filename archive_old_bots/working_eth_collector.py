#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime, timedelta

def get_eth_price():
    apis = [
        "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
        "https://api.coinbase.com/v2/exchange-rates?currency=ETH",
        "https://api.kraken.com/0/public/Ticker?pair=ETHUSD"
    ]
    
    for api in apis:
        try:
            response = requests.get(api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'price' in data:  # Binance
                    return float(data['price'])
                elif 'data' in data:  # Coinbase
                    return float(data['data']['rates']['USD'])
                elif 'result' in data:  # Kraken
                    return float(list(data['result'].values())[0]['c'][0])
                    
        except Exception as e:
            print(f"API {api} failed: {e}")
            continue
    
    return None

def send_signal(signal_type, eth_price):
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = f"ETH {signal_type} Signal\nPrice: ${eth_price:,.2f}\nTime: {datetime.now().strftime('%H:%M')}"
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        print(f"Signal sent: {response.status_code}")
        
    except Exception as e:
        print(f"Telegram error: {e}")

def main():
    print(f"ETH Check: {datetime.now().strftime('%H:%M')}")
    
    price = get_eth_price()
    if price:
        print(f"ETH: ${price:,.2f}")
        
        # Простая логика
        if price > 4200:
            send_signal("BREAKOUT UP", price)
        elif price < 3800:
            send_signal("BREAKOUT DOWN", price)
        else:
            print("No signal")
    else:
        print("Price fetch failed")

if __name__ == "__main__":
    main()
