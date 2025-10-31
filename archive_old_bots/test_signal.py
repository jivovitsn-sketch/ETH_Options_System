import requests
import json
from datetime import datetime, timedelta

def test_telegram():
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = "TEST: ETH OPTIONS SIGNAL\n\nBUY: ETH-30NOV24-4100-C\nSELL: ETH-30NOV24-4300-C\n\nThis is a test message"
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        print(f"Test message sent: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS! Check VIP channel")
        else:
            print(f"FAILED: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_telegram()
