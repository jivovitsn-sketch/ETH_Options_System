#!/usr/bin/env python3
import requests
import json
from datetime import datetime
from signal_deduplicator import SignalDeduplicator

class FixedETHCollector:
    def __init__(self):
        self.deduplicator = SignalDeduplicator()
        
    def get_eth_price(self):
        try:
            response = requests.get('https://api.bybit.com/v2/public/tickers?symbol=ETHUSDT', timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data['result'][0]['last_price'])
        except:
            pass
        return None
    
    def analyze_and_signal(self):
        eth_price = self.get_eth_price()
        if not eth_price:
            return
        
        # Простая логика без спама
        price_level = round(eth_price / 100) * 100
        
        if eth_price > price_level + 50:
            signal_type = "BREAKOUT_UP"
            strategy = "Bull Call Spread"
        elif eth_price < price_level - 50:
            signal_type = "BREAKOUT_DOWN" 
            strategy = "Bear Put Spread"
        else:
            return  # Нет сигнала
        
        # Проверяем дедупликацию
        if not self.deduplicator.should_send_signal(signal_type, eth_price):
            print(f"Signal {signal_type} skipped (duplicate)")
            return
        
        # Отправляем сигнал
        self.send_clean_signal(signal_type, strategy, eth_price)
    
    def send_clean_signal(self, signal_type, strategy, eth_price):
        try:
            with open('config/telegram.json') as f:
                config = json.load(f)
            
            message = f"""
🎯 <b>ETH OPTIONS SIGNAL</b>

<b>Type:</b> {signal_type}
<b>Strategy:</b> {strategy}
<b>ETH Price:</b> ${eth_price:,.2f}
<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

<i>Next signal in 4+ hours minimum</i>
            """
            
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            data = {
                'chat_id': config['channels']['vip'],
                'text': message.strip(),
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
            if response.status_code == 200:
                print(f"Clean signal sent: {signal_type}")
            
        except Exception as e:
            print(f"Signal error: {e}")

if __name__ == "__main__":
    collector = FixedETHCollector()
    collector.analyze_and_signal()
