import os
import requests
from dotenv import load_dotenv

load_dotenv()

def setup_telegram_with_proxy():
    """Настройка Telegram с использованием прокси"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    vip_chat = os.getenv('TELEGRAM_VIP_CHAT_ID')
    proxy_url = os.getenv('TELEGRAM_PROXY_URL')
    proxy_user = os.getenv('TELEGRAM_PROXY_USERNAME')
    proxy_pass = os.getenv('TELEGRAM_PROXY_PASSWORD')
    
    print("🔧 НАСТРОЙКИ TELEGRAM:")
    print(f"• BOT_TOKEN: {'✅' if bot_token and bot_token != 'your_bot_token_here' else '❌'} {'Установлен' if bot_token and bot_token != 'your_bot_token_here' else 'НЕ настроен'}")
    print(f"• VIP_CHAT_ID: {'✅' if vip_chat and vip_chat != 'your_vip_chat_id' else '❌'} {'Установлен' if vip_chat and vip_chat != 'your_vip_chat_id' else 'НЕ настроен'}")
    print(f"• PROXY: {'✅' if proxy_url else '❌'} {'Настроен' if proxy_url else 'Не настроен'}")
    
    if bot_token == 'your_bot_token_here' or vip_chat == 'your_vip_chat_id':
        print("\n🚨 ВНИМАНИЕ: Нужно настроить .env файл!")
        print("1. Создайте бота через @BotFather в Telegram")
        print("2. Получите токен бота")
        print("3. Добавьте бота в ваш чат")
        print("4. Получите chat_id через @userinfobot")
        print("5. Обновите файл .env с реальными значениями")
        return False
    
    return True

def test_telegram_connection():
    """Тестирование подключения к Telegram"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID')
    proxy_url = os.getenv('TELEGRAM_PROXY_URL')
    
    if not bot_token or not chat_id:
        print("❌ Telegram не настроен")
        return False
    
    try:
        # Пробуем без прокси сначала
        url = f'https://api.telegram.org/bot{bot_token}/getMe'
        
        proxies = None
        if proxy_url:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        response = requests.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print("✅ Подключение к Telegram успешно")
            return True
        else:
            print(f"❌ Ошибка подключения: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def send_test_message():
    """Отправка тестового сообщения"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID')
    proxy_url = os.getenv('TELEGRAM_PROXY_URL')
    
    try:
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': '🧪 ТЕСТОВОЕ СООБЩЕНИЕ\nСистема опционных сигналов работает! ✅\n\nЕсли вы видите это сообщение, значит Telegram настроен правильно! 🚀',
            'parse_mode': 'Markdown'
        }
        
        proxies = None
        if proxy_url:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        response = requests.post(url, json=payload, proxies=proxies, timeout=15)
        if response.status_code == 200:
            print("✅ Тестовое сообщение отправлено в Telegram!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ПРОВЕРКА НАСТРОЕК TELEGRAM")
    print("=" * 50)
    
    if setup_telegram_with_proxy():
        print("\n🔗 ТЕСТИРУЕМ ПОДКЛЮЧЕНИЕ...")
        if test_telegram_connection():
            print("\n📨 ОТПРАВЛЯЕМ ТЕСТОВОЕ СООБЩЕНИЕ...")
            send_test_message()
        else:
            print("\n🚨 Не удалось подключиться к Telegram")
            print("Попробуйте:")
            print("1. Проверить интернет соединение")
            print("2. Проверить настройки прокси")
            print("3. Убедиться что бот активен")
    else:
        print("\n📝 ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:")
        print("1. Откройте Telegram и найдите @BotFather")
        print("2. Отправьте /newbot и следуйте инструкциям")
        print("3. Скопируйте токен бота")
        print("4. Найдите @userinfobot чтобы получить ваш chat_id")
        print("5. Отредактируйте файл .env:")
        print("   TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        print("   TELEGRAM_VIP_CHAT_ID=ваш_chat_id")
