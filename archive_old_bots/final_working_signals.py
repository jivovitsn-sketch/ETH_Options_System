#!/usr/bin/env python3
import requests
import json

def test_send():
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = """ETH OPTIONS SIGNALS TEST

ETH BUY: Bull Call Spread
Price: $4100.00
Strikes: 4100/4300
Expiry: 29NOV24

BTC SELL: Bear Put Spread  
Price: $75000.00
Strikes: 75000/71000
Expiry: 29NOV24

WORKING TEST"""
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:100]}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing final signal system...")
    result = test_send()
    print(f"Success: {result}")
