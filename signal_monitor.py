import time
import subprocess
import re
from discord_sender import discord_sender

def monitor_logs():
    """Мониторит логи на появление новых сигналов"""
    print("🔍 Мониторинг сигналов запущен...")
    
    while True:
        try:
            # Проверяем логи генератора сигналов
            result = subprocess.run(['tail', '-n', '50', 'logs/advanced_signals_generator.log'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\\n')
                for line in lines:
                    if any(word in line.upper() for word in ['BULLISH', 'BEARISH', 'SIGNAL', 'СИГНАЛ']):
                        print(f"🎯 Найден сигнал: {line}")
                        
                        # Определяем тип сигнала
                        if 'VIP' in line.upper():
                            discord_sender.send_to_vip(f"🎯 {line}")
                        elif 'FREE' in line.upper():
                            discord_sender.send_to_free(f"🎯 {line}")
            
            time.sleep(30)  # Проверяем каждые 30 секунд
            
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_logs()
