#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

def get_eth_price():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=10)
        if response.status_code == 200:
            return float(response.json()['price'])
    except Exception as e:
        print(f"Price error: {e}")
    return None

def create_clear_signal(eth_price):
    price_level = round(eth_price / 50) * 50
    
    if eth_price > price_level + 25:
        action = "BUY"
        strategy = "Bull Call Spread"
        long_strike = price_level
        short_strike = price_level + 200
        option_type = "C"
    elif eth_price < price_level - 25:
        action = "SELL" 
        strategy = "Bear Put Spread"
        long_strike = price_level
        short_strike = price_level - 200
        option_type = "P"
    else:
        return None
    
    expiry_date = datetime.now() + timedelta(days=35)
    expiry_str = expiry_date.strftime('%d%b%y').upper()
    
    cost = 0.05
    max_profit = abs(short_strike - long_strike) - (cost * 100)
    
    return {
        'action': action,
        'strategy': strategy,
        'eth_price': eth_price,
        'long_strike': long_strike,
        'short_strike': short_strike,
        'expiry': expiry_str,
        'option_type': option_type,
        'cost': cost,
        'max_profit': max_profit
    }

def send_signal(signal):
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = f"""🎯 ETH OPTIONS TRADE

ACTION: {signal['action']} {signal['strategy']}

MARKET:
ETH Price: ${signal['eth_price']:,.2f}

TRADE SETUP:
BUY: ETH-{signal['expiry']}-{signal['long_strike']:.0f}-{signal['option_type']}
SELL: ETH-{signal['expiry']}-{signal['short_strike']:.0f}-{signal['option_type']}

ECONOMICS:
Cost: {signal['cost']:.3f} ETH per spread
Max Profit: {signal['max_profit']:.3f} ETH
ROI: {(signal['max_profit']/signal['cost']*100):.0f}%

EXPIRY: {signal['expiry']}"""
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        print(f"Signal sent: {response.status_code}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Send error: {e}")
        return False

def main():
    print(f"Clear ETH Signals: {datetime.now().strftime('%H:%M')}")
    
    eth_price = get_eth_price()
    if not eth_price:
        print("Failed to get price")
        return
    
    print(f"ETH: ${eth_price:,.2f}")
    
    signal = create_clear_signal(eth_price)
    if signal:
        print(f"Signal: {signal['action']} @ {signal['long_strike']}")
        send_signal(signal)
    else:
        print("No signal (price stable)")

if __name__ == "__main__":
    main()
