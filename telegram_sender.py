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
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            logger.info("✅ Message sent to Telegram")
            return True
        else:
            logger.error(f"❌ Telegram error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to send to Telegram: {e}")
        return False


if __name__ == '__main__':
    # Тест
    test_message = "🧪 Test message from ETH Options System"
    send_to_telegram(test_message)
