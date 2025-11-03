#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM SENDER - отправка сообщений в 3 канала
"""

import os
import requests
import logging
from typing import Optional
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramSender:
    def __init__(self):
        # Загружаем настройки из .env
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.free_chat_id = os.getenv('TELEGRAM_FREE_CHAT_ID')
        self.vip_chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID')
        self.admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        
        # Proxy settings
        self.proxy_url = os.getenv('TELEGRAM_PROXY_URL')
        self.proxy_username = os.getenv('TELEGRAM_PROXY_USERNAME')
        self.proxy_password = os.getenv('TELEGRAM_PROXY_PASSWORD')
        
        self.session = self._create_session()
        
        # Логируем настройки (без чувствительных данных)
        logger.info(f"📱 Telegram sender initialized. Bot: {bool(self.bot_token)}, FREE: {bool(self.free_chat_id)}, VIP: {bool(self.vip_chat_id)}, ADMIN: {bool(self.admin_chat_id)}")
        
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
                logger.info("✅ Proxy configured with authentication")
            else:
                logger.info("⚠️ Proxy configured without authentication")
                
        return session

    def send_message(self, text: str, chat_type: str = "admin") -> bool:
        """
        Отправка сообщения в Telegram
        
        Args:
            text: Текст сообщения
            chat_type: "free", "vip", или "admin"
            
        Returns:
            bool: Успешность отправки
        """
        if not self.bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not set")
            return False
            
        # Выбираем chat_id в зависимости от типа канала
        if chat_type == "free":
            chat_id = self.free_chat_id
            channel_name = "FREE"
        elif chat_type == "vip":
            chat_id = self.vip_chat_id  
            channel_name = "VIP"
        else:  # admin по умолчанию
            chat_id = self.admin_chat_id
            channel_name = "ADMIN"
        
        if not chat_id:
            logger.error(f"❌ Chat ID not set for {channel_name} channel")
            return False
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        try:
            logger.info(f"📤 Sending message to {channel_name} channel...")
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to {channel_name} channel")
                return True
            else:
                logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram send failed: {e}")
            return False

    def send_signal_message(self, asset: str, signal_type: str, confidence: float, 
                          strategies: list, details: str = "", is_vip: bool = True) -> bool:
        """Отправка сигнала в канал"""
        channel = "vip" if is_vip else "free"
        
        message = f"""
🎯 <b>{asset} TRADING SIGNAL</b>

📊 Type: {signal_type}
✅ Confidence: {confidence:.0%}
💡 Strategies: {', '.join(strategies)}

{details}

#Signals #Trading
        """.strip()
        
        return self.send_message(message, channel)

    def send_admin_message(self, title: str, message: str) -> bool:
        """Отправка сообщения в админский канал"""
        full_message = f"""
🛠️ <b>{title}</b>

{message}

⏰ {self._get_timestamp()}
        """.strip()
        
        return self.send_message(full_message, "admin")

    def send_free_message(self, message: str) -> bool:
        """Отправка сообщения в free канал"""
        return self.send_message(message, "free")

    def _get_timestamp(self):
        """Получение временной метки"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Создаем глобальный экземпляр для удобства
_sender = TelegramSender()

def send_message(text: str, chat_type: str = "admin") -> bool:
    """Упрощенная функция для отправки сообщений"""
    return _sender.send_message(text, chat_type)

def send_signal(asset: str, signal_type: str, confidence: float, 
                strategies: list, details: str = "", is_vip: bool = True) -> bool:
    """Функция для отправки сигналов"""
    return _sender.send_signal_message(asset, signal_type, confidence, strategies, details, is_vip)

def send_admin_alert(title: str, message: str) -> bool:
    """Функция для отправки админских уведомлений"""
    return _sender.send_admin_message(title, message)

def send_free_message(message: str) -> bool:
    """Функция для отправки в free канал"""
    return _sender.send_free_message(message)

# Оригинальные функции для обратной совместимости
def send_to_telegram(message: str, chat_id: str = None):
    """Оригинальная функция для обратной совместимости"""
    if chat_id == os.getenv('TELEGRAM_ADMIN_CHAT_ID'):
        return send_admin_alert("Сообщение", message)
    else:
        return send_free_message(message)

def send_admin_message(message: str):
    """Оригинальная функция для обратной совместимости"""
    return send_admin_alert("Уведомление", message)

def send_vip_message(message: str):
    """Оригинальная функция для обратной совместимости"""
    return send_signal("VIP", "ALERT", 1.0, ["Alert"], message, is_vip=True)

if __name__ == '__main__':
    # Тест отправки во все каналы
    test_msg = "🧪 Тест Telegram sender - система работает!"
    
    print("Testing FREE channel...")
    success_free = send_free_message(test_msg + " [FREE]")
    
    print("Testing VIP channel...") 
    success_vip = send_signal("TEST", "TEST", 0.75, ["Test Strategy"], "Test details", is_vip=True)
    
    print("Testing ADMIN channel...")
    success_admin = send_admin_alert("Тест системы", test_msg + " [ADMIN]")
    
    print(f"Results: FREE={success_free}, VIP={success_vip}, ADMIN={success_admin}")
