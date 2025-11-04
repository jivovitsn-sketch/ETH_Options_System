import sqlite3
from datetime import datetime, timedelta
from discord_sender import discord_sender

def check_tables():
    """Проверяет какие таблицы есть в базе"""
    try:
        conn = sqlite3.connect('crypto_signals.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("📊 Таблицы в базе данных:")
        for table in tables:
            print(f"  - {table[0]}")
        return [table[0] for table in tables]
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return []

def load_recent_signals(hours=24):
    """Загружает сигналы за последние N часов"""
    try:
        tables = check_tables()
        
        if 'signals' not in tables:
            print("❌ Таблица 'signals' не найдена")
            # Проверим другие возможные названия таблиц
            for table in tables:
                if 'signal' in table.lower():
                    print(f"ℹ️  Найдена похожая таблица: {table}")
            return
        
        conn = sqlite3.connect('crypto_signals.db')
        cursor = conn.cursor()

        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            SELECT signal_type, symbol, message, timestamp, confidence 
            FROM signals 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
        ''', (since_time,))

        signals = cursor.fetchall()
        print(f"📊 Найдено сигналов за {hours} часов: {len(signals)}")

        sent_count = 0
        for signal in signals:
            signal_type, symbol, message, timestamp, confidence = signal
            
            # Форматируем сообщение для Discord
            if "BULLISH" in message.upper():
                emoji = "🟢"
            elif "BEARISH" in message.upper():
                emoji = "🔴"
            else:
                emoji = "⚡"
                
            formatted_msg = f"{emoji} **{symbol}** | {timestamp}\\n{message}\\n📊 Confidence: {confidence}%"

            if signal_type == "VIP":
                if discord_sender.send_to_vip(formatted_msg):
                    sent_count += 1
            elif signal_type == "FREE":
                if discord_sender.send_to_free(formatted_msg):
                    sent_count += 1

            import time
            time.sleep(0.3)  # Задержка чтобы не спамить

        # Отчет админу
        report = f"📊 История загружена: {sent_count}/{len(signals)} сигналов за {hours} часов"
        discord_sender.send_to_admin(report)
        print(report)
        
    except Exception as e:
        print(f"❌ Ошибка загрузки истории: {e}")
        discord_sender.send_to_admin(f"❌ Ошибка загрузки истории: {e}")

if __name__ == "__main__":
    load_recent_signals(24)  # Загружаем за 24 часа
