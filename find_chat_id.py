#!/usr/bin/env python3
import requests
import time
import json

# Настройки из .env
BOT_TOKEN = "8465104192:AAHaKFyt6KzvhEo1YplPiFri8QF3hwj6-qM"
PROXY_URL = "http://uQnxk4:wgu4pJ@77.83.186.47:8000"

proxies = {
    'http': PROXY_URL,
    'https': PROXY_URL
}

def get_chat_id():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("=== RAW RESPONSE ===")
            print(json.dumps(data, indent=2))
            
            if data['ok'] and data['result']:
                print("\n=== CHATS FOUND ===")
                for update in data['result']:
                    if 'message' in update:
                        chat = update['message']['chat']
                        print(f"CHAT: {chat}")
                    elif 'channel_post' in update:
                        chat = update['channel_post']['chat']
                        print(f"CHANNEL: {chat}")
            else:
                print("No updates found. Send a message to the bot first.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    get_chat_id()
