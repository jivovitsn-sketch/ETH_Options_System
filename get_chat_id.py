#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_updates():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    proxy_url = os.getenv('TELEGRAM_PROXY_URL')
    proxy_username = os.getenv('TELEGRAM_PROXY_USERNAME')
    proxy_password = os.getenv('TELEGRAM_PROXY_PASSWORD')
    
    if proxy_url and proxy_username and proxy_password:
        proxy_with_auth = proxy_url.replace('http://', f'http://{proxy_username}:{proxy_password}@')
        proxies = {'http': proxy_with_auth, 'https': proxy_with_auth}
    else:
        proxies = None
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok'] and data['result']:
                print("=== НАЙДЕННЫЕ ЧАТЫ ===")
                for update in data['result']:
                    if 'message' in update:
                        chat = update['message']['chat']
                        print(f"Тип: {chat['type']}, ID: {chat['id']}, Название: {chat.get('title', chat.get('first_name', 'N/A'))}")
                    elif 'channel_post' in update:
                        chat = update['channel_post']['chat']
                        print(f"Тип: канал, ID: {chat['id']}, Название: {chat.get('title', 'N/A')}")
            else:
                print("❌ Нет обновлений. Отправьте сообщение боту в чат и попробуйте снова.")
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    get_updates()
