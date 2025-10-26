#!/usr/bin/env python3
"""
LIVE TRADER с интеграцией журнала
"""
from signal_manager import SignalManager
from telegram_alerts_final import TelegramAlertsFinal
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))
from trading_journal import TradingJournal

import time
from datetime import datetime

class LiveTraderWithJournal:
    def __init__(self):
        self.signal_manager = SignalManager('4h')
        self.telegram = TelegramAlertsFinal()
        self.journal = TradingJournal()
        
        print("Live Trader with Journal initialized")
        print("  Telegram: ✅")
        print("  Journal: ✅") 
        print("  Signal Manager: ✅")
        
        # Уведомляем о запуске
        self.telegram.admin_system_started()
    
    def simulate_trading_session(self, duration_minutes=5):
        """Симуляция торговой сессии"""
        
        print(f"\n🚀 Starting {duration_minutes}-minute simulation...")
        
        start_time = time.time()
        trades_made = 0
        
        while time.time() - start_time < duration_minutes * 60:
            
            # Симуляция проверки рынка
            current_price = 3900 + (time.time() % 100) - 50
            
            # Симуляция сигнала (каждые 2 минуты)
            if int(time.time()) % 120 == 0:
                
                signal_type = "BUY" if trades_made % 2 == 0 else "SELL"
                
                # Проверяем можно ли отправить сигнал
                if self.signal_manager.should_send_signal('ETHUSDT', signal_type, current_price):
                    
                    # FREE сигнал
                    self.telegram.free_signal('ETHUSDT', signal_type, current_price)
                    
                    # Создаем сделку
                    trade_data = {
                        'asset': 'ETHUSDT',
                        'signal': signal_type,
                        'strategy': '60_DTE_Bull_Call',
                        'entry': current_price,
                        'exit': current_price + (50 if signal_type == 'BUY' else -50),
                        'size': 500,
                        'cost': 89,
                        'delta': 0.071,
                        'theta': 0.05,
                        'confidence': 'HIGH'
                    }
                    
                    # VIP уведомление
                    self.telegram.vip_trade_opened(trade_data)
                    
                    # Добавляем в журнал
                    self.journal.add_trade(trade_data)
                    
                    trades_made += 1
                    print(f"  📊 Trade #{trades_made}: {signal_type} @ ${current_price:.2f}")
            
            time.sleep(30)  # Проверка каждые 30 секунд
        
        print(f"\n✅ Simulation complete:")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Trades made: {trades_made}")
        print(f"   Check Telegram channels for updates")
        print(f"   Check Excel: data/Enhanced_Trading_Journal.xlsx")

if __name__ == "__main__":
    trader = LiveTraderWithJournal()
    trader.simulate_trading_session(5)
