#!/usr/bin/env python3
"""TELEGRAM ALERTS - финальная версия с HTTP прокси"""
import requests
import json
from datetime import datetime
from pathlib import Path

class TelegramAlertsFinal:
    def __init__(self):
        # Загружаем конфиг
        config_file = Path(__file__).parent.parent / 'config' / 'telegram.json'
        
        with open(config_file) as f:
            config = json.load(f)
        
        self.token = config['bot_token']
        self.channels = config['channels']
        self.proxies = config['proxy']
        
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
        print("Telegram Alerts Final initialized")
        print(f"  Token: {self.token[:20]}...")
        print(f"  FREE channel: {self.channels['free']}")
        print(f"  VIP channel: {self.channels['vip']}")
        print(f"  ADMIN channel: {self.channels['admin']}")
        print(f"  HTTP Proxy: ✅")
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Отправка сообщения через HTTP прокси"""
        url = f"{self.api_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(
                url,
                json=data,
                proxies=self.proxies,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"✅ Telegram message sent to {chat_id}")
                return True
            else:
                print(f"❌ Telegram error {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram exception: {e}")
            return False
    
    def free_signal(self, asset, signal, price):
        """FREE канал - простые сигналы"""
        message = f"""
🔥 <b>SIGNAL</b>

<b>Asset:</b> {asset}
<b>Direction:</b> {signal}  
<b>Price:</b> ${price:,.2f}
<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
        """
        
        return self.send_message(self.channels['free'], message.strip())
    
    def vip_trade_opened(self, trade_data):
        """VIP канал - детальная информация"""
        message = f"""
📊 <b>VIP TRADE OPENED</b>

<b>Asset:</b> {trade_data['asset']}
<b>Strategy:</b> {trade_data['strategy']}
<b>Entry Price:</b> ${trade_data['entry']:,.2f}
<b>Position Size:</b> ${trade_data['size']:,.2f}
<b>Delta:</b> {trade_data.get('delta', 0):.4f}
<b>Theta:</b> {trade_data.get('theta', 0):.2f}/day

<i>Paper Trading Mode</i>
        """
        
        return self.send_message(self.channels['vip'], message.strip())
    
    def admin_system_started(self):
        """ADMIN канал - система запущена"""
        message = f"""
🚀 <b>SYSTEM STARTED</b>

Mode: Paper Trading
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Proxy: HTTP ✅

<i>ETH Options System</i>
        """
        
        return self.send_message(self.channels['admin'], message.strip())
    
    def admin_backup_complete(self, files_count):
        """ADMIN канал - backup завершен"""
        message = f"""
💾 <b>BACKUP COMPLETE</b>

Files: {files_count}
Time: {datetime.now().strftime('%H:%M:%S')}

<i>Auto Backup System</i>
        """
        
        return self.send_message(self.channels['admin'], message.strip())

if __name__ == "__main__":
    print("Тестируем Telegram через HTTP прокси...")
    
    bot = TelegramAlertsFinal()
    
    print("\n1️⃣ Тест FREE канала...")
    bot.free_signal('ETHUSDT', 'BUY', 3939.00)
    
    print("\n2️⃣ Тест VIP канала...")
    bot.vip_trade_opened({
        'asset': 'ETHUSDT',
        'strategy': 'Bull Call 60DTE',
        'entry': 3939.00,
        'size': 500,
        'delta': 0.071,
        'theta': 0.05
    })
    
    print("\n3️⃣ Тест ADMIN канала...")
    bot.admin_system_started()
    
    print("\n📱 Проверь свои Telegram каналы!")
