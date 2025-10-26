#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def get_eth_price():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=10)
        if response.status_code == 200:
            return float(response.json()['price'])
    except:
        pass
    return 3950  # Fallback

def create_signal(eth_price):
    # Простая логика - ВСЕГДА создаем сигнал для теста
    if eth_price > 4000:
        return {
            'action': 'BUY',
            'strategy': 'Bull Call Spread',
            'eth_price': eth_price,
            'long_strike': 4000,
            'short_strike': 4200,
            'expiry': '29NOV24',
            'cost': 0.05,
            'max_profit': 0.15
        }
    else:
        return {
            'action': 'SELL',
            'strategy': 'Bear Put Spread', 
            'eth_price': eth_price,
            'long_strike': 3900,
            'short_strike': 3700,
            'expiry': '29NOV24',
            'cost': 0.05,
            'max_profit': 0.15
        }

def send_telegram(signal):
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = f"""🎯 ETH OPTIONS TRADE

ACTION: {signal['action']} {signal['strategy']}

MARKET:
ETH Price: ${signal['eth_price']:,.2f}

TRADE SETUP:
BUY: ETH-{signal['expiry']}-{signal['long_strike']:.0f}-C
SELL: ETH-{signal['expiry']}-{signal['short_strike']:.0f}-C

ECONOMICS:
Cost: {signal['cost']:.3f} ETH
Max Profit: {signal['max_profit']:.3f} ETH
ROI: {(signal['max_profit']/signal['cost']*100):.0f}%

EXPIRY: {signal['expiry']}

TEST SIGNAL - CHECKING SYSTEM"""
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message
        }
        
        print(f"Sending to chat: {config['channels']['vip']}")
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        
        print(f"Response: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=== Working Signal System ===")
    
    eth_price = get_eth_price()
    print(f"ETH: ${eth_price}")
    
    signal = create_signal(eth_price)
    print(f"Signal: {signal['action']}")
    
    result = send_telegram(signal)
    print(f"Sent: {result}")

if __name__ == "__main__":
    main()
