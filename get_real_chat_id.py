#!/usr/bin/env python3
import requests
import json

BOT_TOKEN = "8465104192:AAHaKFyt6KzvhEo1YplPiFri8QF3hwj6-qM"
PROXY = "http://uQnxk4:wgu4pJ@77.83.186.47:8000"

proxies = {
    'http': PROXY,
    'https': PROXY
}

def test_chat_id(chat_id, description):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': f'Тест сообщения для {description}',
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"✅ {description}: {chat_id} - РАБОТАЕТ!")
            return True
        else:
            error_msg = response.json().get('description', 'Unknown error')
            print(f"❌ {description}: {chat_id} - {error_msg}")
            return False
    except Exception as e:
        print(f"❌ {description}: {chat_id} - Ошибка: {e}")
        return False

print("=== ТЕСТИРУЕМ ТЕКУЩИЕ CHAT_ID ===")
test_chat_id("-1002345678262", "ADMIN")
test_chat_id("-1003001252760", "VIP") 
test_chat_id("-1002345678291", "FREE")

print("\n=== ИНСТРУКЦИЯ ===")
print("1. Добавьте бота @OptionsSignalsBot как администратора в ваши каналы")
print("2. Отправьте любое сообщение в канал")
print("3. Получите реальный chat_id через:")
print("   - Бота @userinfobot (перешлите сообщение из канала)")
print("   - Или создайте новые каналы и добавьте бота")
