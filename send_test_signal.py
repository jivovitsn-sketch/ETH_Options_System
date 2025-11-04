from discord_sender import discord_sender
from telegram_sender import telegram_sender
import time

def send_test_signals():
    print("Отправка тестовых сигналов...")
    
    # Тестовый VIP сигнал
    vip_msg = "🎯 TEST VIP SIGNAL\\nDOGE BULLISH 85%\\nEntry: 0.150-0.155\\nTarget: 0.165-0.170\\nStop: 0.145"
    
    # Тестовый FREE сигнал  
    free_msg = "🎯 TEST FREE SIGNAL\\nETH BULLISH 72%\\nEntry: 3400-3450\\nTarget: 3550-3600\\nStop: 3350"
    
    # Отправляем в Telegram
    telegram_sender.send_to_vip(vip_msg)
    telegram_sender.send_to_free(free_msg)
    
    # Отправляем в Discord
    discord_sender.send_to_vip("⭐ " + vip_msg)
    discord_sender.send_to_free("📢 " + free_msg)
    
    print("✅ Тестовые сигналы отправлены в оба канала")

if __name__ == "__main__":
    send_test_signals()
