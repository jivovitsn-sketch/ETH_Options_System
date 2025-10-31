import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_proxy_connection():
    """Тестируем подключение через прокси"""
    
    proxy_url = os.getenv('TELEGRAM_PROXY_URL')
    proxy_user = os.getenv('TELEGRAM_PROXY_USERNAME') 
    proxy_pass = os.getenv('TELEGRAM_PROXY_PASSWORD')
    
    print("🔧 НАСТРОЙКИ ПРОКСИ:")
    print(f"URL: {proxy_url}")
    print(f"Username: {proxy_user}")
    print(f"Password: {proxy_pass}")
    
    if not proxy_url:
        print("❌ Прокси не настроен")
        return False
    
    try:
        # Формируем прокси строку с аутентификацией
        if proxy_user and proxy_pass:
            proxy_with_auth = f"http://{proxy_user}:{proxy_pass}@{proxy_url.split('//')[1]}"
        else:
            proxy_with_auth = proxy_url
            
        proxies = {
            'http': proxy_with_auth,
            'https': proxy_with_auth
        }
        
        print(f"🔗 Тестируем прокси: {proxy_with_auth.split('@')[1] if '@' in proxy_with_auth else proxy_with_auth}")
        
        # Тестируем подключение через прокси
        test_url = "https://api.telegram.org"
        response = requests.get(test_url, proxies=proxies, timeout=15)
        
        if response.status_code == 200:
            print("✅ Прокси работает!")
            return True
        else:
            print(f"❌ Ошибка прокси: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения через прокси: {e}")
        return False

def update_telegram_sender():
    """Обновляем функцию отправки Telegram для использования прокси"""
    
    with open('advanced_signals_generator.py', 'r') as f:
        content = f.read()
    
    # Заменяем функцию send_telegram_message
    new_telegram_function = '''
    def send_telegram_message(self, message, is_vip=False):
        """Отправка сообщения в Telegram с использованием прокси"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID' if is_vip else 'TELEGRAM_ADMIN_CHAT_ID')
            proxy_url = os.getenv('TELEGRAM_PROXY_URL')
            proxy_user = os.getenv('TELEGRAM_PROXY_USERNAME')
            proxy_pass = os.getenv('TELEGRAM_PROXY_PASSWORD')
            
            if not bot_token or not chat_id:
                logger.warning("❌ Telegram credentials not set")
                return
            
            # Настраиваем прокси
            proxies = None
            if proxy_url:
                if proxy_user and proxy_pass:
                    proxy_with_auth = f"http://{proxy_user}:{proxy_pass}@{proxy_url.split('//')[1]}"
                else:
                    proxy_with_auth = proxy_url
                proxies = {
                    'http': proxy_with_auth,
                    'https': proxy_with_auth
                }
                logger.info(f"🔗 Using proxy: {proxy_url}")
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            # Увеличиваем таймаут и пробуем с прокси
            response = requests.post(url, json=payload, proxies=proxies, timeout=20)
            if response.status_code == 200:
                logger.info("✅ Сообщение отправлено в Telegram")
            else:
                logger.error(f"❌ Ошибка отправки в Telegram: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка Telegram: {e}")
            # Пробуем без прокси как fallback
            try:
                if proxies:
                    logger.info("🔄 Пробуем без прокси...")
                    response = requests.post(url, json=payload, timeout=20)
                    if response.status_code == 200:
                        logger.info("✅ Сообщение отправлено без прокси")
                    else:
                        logger.error(f"❌ Ошибка без прокси: {response.text}")
            except Exception as e2:
                logger.error(f"❌ Ошибка при fallback: {e2}")
'''
    
    # Заменяем старую функцию на новую
    import re
    old_pattern = r'def send_telegram_message\([^)]*\):.*?except Exception as e:\s*logger.error\(f"❌ Ошибка Telegram: {e}"\)'
    new_content = re.sub(old_pattern, new_telegram_function, content, flags=re.DOTALL)
    
    with open('advanced_signals_generator.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Функция отправки Telegram обновлена для работы с прокси")

if __name__ == "__main__":
    print("🔧 НАСТРОЙКА ПРОКСИ ДЛЯ TELEGRAM")
    print("=" * 50)
    
    if test_proxy_connection():
        print("\n✅ Прокси работает, обновляем код...")
        update_telegram_sender()
    else:
        print("\n🚨 Проблемы с прокси, настраиваем отправку без прокси...")
        update_telegram_sender()
