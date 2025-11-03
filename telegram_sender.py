#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM SENDER - отправка сообщений
"""

import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def send_to_telegram(message: str, chat_id: str = None):
    """Отправка сообщения в Telegram"""
    
    if not chat_id:
        chat_id = os.getenv('VIP_CHAT_ID')
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token or not chat_id:
        logger.error("❌ Telegram credentials not configured")
        return False
    
    # Proxy settings
    proxy_url = os.getenv('TELEGRAM_PROXY_URL')
    proxy_username = os.getenv('TELEGRAM_PROXY_USERNAME') 
    proxy_password = os.getenv('TELEGRAM_PROXY_PASSWORD')
    
    session = requests.Session()
    
    if proxy_url:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        session.proxies.update(proxies)
        
        if proxy_username and proxy_password:
            session.auth = (proxy_username, proxy_password)
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = session.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Message sent to Telegram")
            return True
        else:
            logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Telegram send failed: {e}")
        return False

def send_admin_message(message: str):
    """Отправка сообщения в админский канал"""
    admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
    return send_to_telegram(message, admin_chat_id)

def send_vip_message(message: str):
    """Отправка сообщения в VIP канал"""
    return send_to_telegram(message)

if __name__ == '__main__':
    # Test
    test_msg = "🧪 Тест Telegram sender"
    success = send_admin_message(test_msg)
    print(f"Тест: {'✅ Успешно' if success else '❌ Ошибка'}")
