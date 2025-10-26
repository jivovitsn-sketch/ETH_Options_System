#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКАЯ ОТПРАВКА МЕСЯЧНЫХ ОТЧЕТОВ в Telegram
"""
import schedule
import time
from datetime import datetime
from telegram_alerts_final import TelegramAlertsFinal
from dashboard_generator import TradingDashboard
from trading_journal import TradingJournal
import pandas as pd

class MonthlyReportSender:
    def __init__(self):
        self.telegram = TelegramAlertsFinal()
        self.dashboard = TradingDashboard()
        self.journal = TradingJournal()
        
    def send_monthly_report(self):
        """Отправка месячного отчета"""
        
        print(f"📊 Generating monthly report for {datetime.now().strftime('%B %Y')}")
        
        try:
            # Генерируем дашборд
            dashboard_image = self.dashboard.generate_monthly_dashboard()
            
            # Читаем данные для текстовой сводки
            trades_df = pd.read_excel('data/Enhanced_Trading_Journal.xlsx', sheet_name='trades')
            
            # Создаем FOMO текст
            summary_text = self.dashboard.create_fomo_summary(trades_df)
            
            # Отправляем в админский канал
            success = self.telegram.send_message(
                self.telegram.channels['admin'], 
                summary_text
            )
            
            if success:
                print("✅ Monthly report sent to Telegram")
            else:
                print("❌ Failed to send monthly report")
                
            # TODO: Отправка изображения дашборда
            # (Требует доработки Telegram bot для отправки изображений)
            
        except Exception as e:
            print(f"❌ Error sending monthly report: {e}")
    
    def setup_scheduler(self):
        """Настройка расписания отправки"""
        
        # Отправка каждое 1 число месяца в 10:00
        schedule.every().month.at("10:00").do(self.send_monthly_report)
        
        # Тестовая отправка каждую неделю (для отладки)
        # schedule.every().week.do(self.send_monthly_report)
        
        print("📅 Monthly report scheduler setup:")
        print("   • Monthly: 1st day of month at 10:00")
        print("   • Test mode: Weekly (comment out for production)")
    
    def run_scheduler(self):
        """Запуск планировщика"""
        
        print("🤖 Monthly report scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Проверка каждый час

if __name__ == "__main__":
    sender = MonthlyReportSender()
    
    # Тестовая отправка
    print("Testing monthly report...")
    sender.send_monthly_report()
    
    # Настройка расписания
    sender.setup_scheduler()
    
    # Запуск (закомментировано для теста)
    # sender.run_scheduler()
