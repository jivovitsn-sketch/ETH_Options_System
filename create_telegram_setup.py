#!/usr/bin/env python3
"""Помощник создания Telegram каналов"""

def create_telegram_channels():
    print("""
════════════════════════════════════════════════════════════════
СОЗДАНИЕ TELEGRAM КАНАЛОВ С НУЛЯ
════════════════════════════════════════════════════════════════

ШАГИ:

1. СОЗДАТЬ БОТА:
   • Открой Telegram
   • Найди @BotFather
   • Отправь: /newbot
   • Название: ETH Options Alert Bot
   • Username: eth_options_alerts_bot (или любой свободный)
   • Скопируй TOKEN

2. СОЗДАТЬ 3 КАНАЛА:
   
   Канал 1: Free Signals
   • Создай канал: "ETH Options - Free Signals"
   • Сделай приватным
   • Добавь бота как администратора
   • Отправь любое сообщение
   • Переслади сообщение @userinfobot - получишь CHAT_ID

   Канал 2: VIP Analytics  
   • Создай канал: "ETH Options - VIP Analytics"
   • Сделай приватным
   • Добавь бота как администратора
   • Получи CHAT_ID аналогично

   Канал 3: Admin Logs
   • Создай канал: "ETH Options - Admin"
   • Добавь только себя + бота
   • Получи CHAT_ID

3. ЗАПОЛНИТЬ КОНФИГ:
   config/telegram.json

4. ТЕСТИРОВАТЬ ЧЕРЕЗ ПРОКСИ
   python3 bot/telegram_alerts.py

═══════════════════════════════════════════════════════════════
    """)

if __name__ == "__main__":
    create_telegram_channels()
