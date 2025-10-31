import os
import re

def find_telegram_credentials():
    """Ищем реальные Telegram credentials в системе"""
    
    # Проверяем другие .env файлы
    env_files = [
        '/home/eth_trader/ETH_Options_System_OLD_BACKUP/_cleanup_backup_20251020/FINAL_PRODUCTION_PACKAGE/.env',
        '/home/eth_trader/ETH_Options_System_OLD_BACKUP/.env'
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"🔍 Проверяем {env_file}")
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Ищем Telegram настройки
            token_match = re.search(r'TELEGRAM_BOT_TOKEN=([^\n]+)', content)
            chat_match = re.search(r'TELEGRAM_VIP_CHAT_ID=([^\n]+)', content)
            
            if token_match and token_match.group(1) != 'your_bot_token_here':
                print(f"✅ Найден реальный BOT_TOKEN: {token_match.group(1)[:20]}...")
                return token_match.group(1), chat_match.group(1) if chat_match else None
    
    print("❌ Реальные Telegram credentials не найдены")
    return None, None

def update_env_file(bot_token, chat_id):
    """Обновляем .env файл"""
    
    with open('.env', 'r') as f:
        content = f.read()
    
    # Заменяем токен и chat_id
    if bot_token:
        content = re.sub(r'TELEGRAM_BOT_TOKEN=.*', f'TELEGRAM_BOT_TOKEN={bot_token}', content)
    if chat_id:
        content = re.sub(r'TELEGRAM_VIP_CHAT_ID=.*', f'TELEGRAM_VIP_CHAT_ID={chat_id}', content)
        content = re.sub(r'TELEGRAM_ADMIN_CHAT_ID=.*', f'TELEGRAM_ADMIN_CHAT_ID={chat_id}', content)
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("✅ .env файл обновлен")

# Основная логика
bot_token, chat_id = find_telegram_credentials()

if bot_token:
    update_env_file(bot_token, chat_id)
    print("🎉 Telegram настройки обновлены!")
else:
    print("""
🚨 НЕОБХОДИМО НАСТРОИТЬ TELEGRAM ВРУЧНУЮ:

1. Создайте бота через @BotFather в Telegram
2. Получите токен бота (выглядит как: 1234567890:ABCdefGHIjklMnOpQRsTuvwxyz)
3. Добавьте бота в ваш чат
4. Получите chat_id через @userinfobot
5. Отредактируйте файл .env:

TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_VIP_CHAT_ID=ваш_chat_id
TELEGRAM_ADMIN_CHAT_ID=ваш_chat_id

После настройки перезапустите систему.
""")
