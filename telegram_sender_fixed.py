#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM SENDER FIXED - только исправления для отправки, без изменения логики
"""

import os
import requests
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.free_chat_id = os.getenv('TELEGRAM_FREE_CHAT_ID')
        self.vip_chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID')
        self.admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')

        # Proxy settings
        self.proxy_url = os.getenv('TELEGRAM_PROXY_URL')
        self.proxy_username = os.getenv('TELEGRAM_PROXY_USERNAME')
        self.proxy_password = os.getenv('TELEGRAM_PROXY_PASSWORD')

        # Настройка прокси
        if self.proxy_url and self.proxy_username and self.proxy_password:
            proxy_with_auth = self.proxy_url.replace('http://', f'http://{self.proxy_username}:{self.proxy_password}@')
            self.proxies = {'http': proxy_with_auth, 'https': proxy_with_auth}
        else:
            self.proxies = None

    def send_message(self, message: str, chat_id: str) -> bool:
        """Отправка сообщения в указанный чат"""
        if not self.bot_token or not chat_id:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, proxies=self.proxies, timeout=10)
            return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def send_to_free(self, message: str) -> bool:
        """Отправка в FREE канал"""
        return self.send_message(message, self.free_chat_id)

    def send_to_vip(self, message: str) -> bool:
        """Отправка в VIP канал"""
        return self.send_message(message, self.vip_chat_id)

    def send_to_admin(self, message: str) -> bool:
        """Отправка в ADMIN канал"""
        return self.send_message(message, self.admin_chat_id)

# Глобальный экземпляр
telegram_sender = TelegramSender()
