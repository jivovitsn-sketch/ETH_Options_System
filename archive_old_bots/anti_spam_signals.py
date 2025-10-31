#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime, timedelta

class AntiSpamSignals:
    def __init__(self):
        self.last_signals_file = 'data/last_signals.json'
        self.min_interval_hours = 6  # Минимум 6 часов между сигналами
    
    def should_send_signal(self, asset, signal_type, price):
        """Проверяем можно ли отправить сигнал"""
        
        try:
            with open(self.last_signals_file) as f:
                last_signals = json.load(f)
        except:
            last_signals = {}
        
        now = datetime.now()
        signal_key = f"{asset}_{signal_type}_{round(price/1000)*1000}"
        
        # Проверяем последний сигнал
        if signal_key in last_signals:
            last_time = datetime.fromisoformat(last_signals[signal_key])
            hours_since = (now - last_time).total_seconds() / 3600
            
            if hours_since < self.min_interval_hours:
                print(f"БЛОКИРОВАНО: {signal_key} отправлен {hours_since:.1f}ч назад")
                return False
        
        # Сохраняем новый сигнал
        last_signals[signal_key] = now.isoformat()
        
        # Очищаем старые записи (>24ч)
        cutoff = now - timedelta(hours=24)
        last_signals = {k: v for k, v in last_signals.items() 
                       if datetime.fromisoformat(v) > cutoff}
        
        os.makedirs('data', exist_ok=True)
        with open(self.last_signals_file, 'w') as f:
            json.dump(last_signals, f)
        
        return True

    def get_price(self, symbol):
        try:
            response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=10)
            if response.status_code == 200:
                return float(response.json()['price'])
        except:
            pass
        return None

    def create_signal(self, asset, price):
        levels = {
            'ETH': {'base': 3900, 'range': 100},
            'BTC': {'base': 70000, 'range': 2000},
            'SOL': {'base': 180, 'range': 20}, 
            'XRP': {'base': 2.5, 'range': 0.3}
        }
        
        config = levels[asset]
        
        if price > config['base'] + config['range']:
            return {'action': 'BUY', 'reason': f"Breakout above {config['base'] + config['range']}"}
        elif price < config['base'] - config['range']:
            return {'action': 'SELL', 'reason': f"Breakdown below {config['base'] - config['range']}"}
        
        return None

    def send_to_channels(self, asset, signal, price):
        try:
            with open('config/telegram.json') as f:
                config = json.load(f)
            
            message = f"""🎯 {asset} {signal['action']}
Price: ${price:,.2f}
Reason: {signal['reason']}
Time: {datetime.now().strftime('%H:%M')}

⚠️ ANTI-SPAM: Next signal min 6h"""
            
            # Отправляем в оба канала
            for channel in ['vip', 'free']:
                url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
                data = {
                    'chat_id': config['channels'][channel],
                    'text': message
                }
                response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
                if response.status_code == 200:
                    print(f"✅ Sent to {channel.upper()}")
                else:
                    print(f"❌ Failed {channel}: {response.status_code}")
                    
        except Exception as e:
            print(f"Error: {e}")

    def run_check(self):
        print(f"=== ANTI-SPAM CHECK: {datetime.now().strftime('%H:%M:%S')} ===")
        
        ASSETS = {
            'ETH': 'ETHUSDT',
            'BTC': 'BTCUSDT',
            'SOL': 'SOLUSDT', 
            'XRP': 'XRPUSDT'
        }
        
        signals_sent = 0
        
        for asset, symbol in ASSETS.items():
            price = self.get_price(symbol)
            if not price:
                continue
                
            print(f"{asset}: ${price:,.2f}")
            
            signal = self.create_signal(asset, price)
            if not signal:
                continue
            
            # АНТИСПАМ ПРОВЕРКА
            if self.should_send_signal(asset, signal['action'], price):
                self.send_to_channels(asset, signal, price)
                signals_sent += 1
                print(f"✅ {asset} {signal['action']} signal sent")
            else:
                print(f"⛔ {asset} signal blocked (anti-spam)")
        
        if signals_sent == 0:
            print("✅ No spam - all signals blocked or no triggers")

if __name__ == "__main__":
    spam_filter = AntiSpamSignals()
    spam_filter.run_check()
