#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Sender - отправка сообщений в Telegram каналы
"""

import os
import requests
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.vip_chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID')
        self.admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        
        # Proxy settings
        self.proxy_url = os.getenv('TELEGRAM_PROXY_URL')
        self.proxy_username = os.getenv('TELEGRAM_PROXY_USERNAME')
        self.proxy_password = os.getenv('TELEGRAM_PROXY_PASSWORD')
        
        self.session = self._create_session()
        
    def _create_session(self):
        """Создание сессии с прокси"""
        session = requests.Session()
        
        if self.proxy_url:
            proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
            session.proxies.update(proxies)
            
            if self.proxy_username and self.proxy_password:
                session.auth = (self.proxy_username, self.proxy_password)
                
        return session

    def send_message(self, text: str, is_admin: bool = False) -> bool:
        """
        Отправка сообщения в Telegram
        
        Args:
            text: Текст сообщения
            is_admin: True для отправки в админский канал, False для VIP канала
            
        Returns:
            bool: Успешность отправки
        """
        if not self.bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not set")
            return False
            
        chat_id = self.admin_chat_id if is_admin else self.vip_chat_id
        
        if not chat_id:
            logger.error(f"❌ Chat ID not set for {'admin' if is_admin else 'VIP'} channel")
            return False
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to {'admin' if is_admin else 'VIP'} channel")
                return True
            else:
                logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram send failed: {e}")
            return False

    def send_signal_message(self, asset: str, signal_type: str, confidence: float, 
                          strategies: list, details: str = "") -> bool:
        """Отправка сигнала в VIP канал"""
        message = f"""
🎯 <b>{asset} TRADING SIGNAL</b>

📊 Type: {signal_type}
✅ Confidence: {confidence:.0%}
💡 Strategies: {', '.join(strategies)}

{details}

#Signals #Trading
        """.strip()
        
        return self.send_message(message, is_admin=False)

    def send_admin_message(self, title: str, message: str) -> bool:
        """Отправка сообщения в админский канал"""
        full_message = f"""
🛠️ <b>{title}</b>

{message}

⏰ {self._get_timestamp()}
        """.strip()
        
        return self.send_message(full_message, is_admin=True)

    def _get_timestamp(self):
        """Получение временной метки"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Создаем глобальный экземпляр для удобства
_sender = TelegramSender()

def send_message(text: str, is_admin: bool = False) -> bool:
    """Упрощенная функция для отправки сообщений"""
    return _sender.send_message(text, is_admin)

def send_signal(asset: str, signal_type: str, confidence: float, 
                strategies: list, details: str = "") -> bool:
    """Функция для отправки сигналов"""
    return _sender.send_signal_message(asset, signal_type, confidence, strategies, details)

def send_admin_alert(title: str, message: str) -> bool:
    """Функция для отправки админских уведомлений"""
    return _sender.send_admin_message(title, message)

if __name__ == '__main__':
    # Тест отправки
    test_msg = "🧪 Тест Telegram sender - система работает!"
    success = send_message(test_msg, is_admin=True)
    print(f"Тест отправки: {'✅ Успешно' if success else '❌ Ошибка'}")
