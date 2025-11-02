#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEALTH MONITOR - Мониторинг работы всех систем
Отправляет отчёты в ADMIN канал
"""

import os
import psutil
import requests
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class HealthMonitor:
    """Мониторинг здоровья систем"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        
        self.critical_processes = [
            'unlimited_oi_monitor.py',
            'futures_data_monitor.py',
            'liquidations_monitor.py',
        ]
    
    def check_processes(self) -> dict:
        """Проверка запущенных процессов"""
        status = {}
        
        for proc_name in self.critical_processes:
            is_running = any(proc_name in p.cmdline() for p in psutil.process_iter(['cmdline']))
            status[proc_name] = 'RUNNING' if is_running else 'STOPPED'
        
        return status
    
    def check_database_updates(self) -> dict:
        """Проверка свежести данных в БД"""
        results = {}
        
        # Проверяем unlimited_oi.db
        try:
            conn = sqlite3.connect('./data/unlimited_oi.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT MAX(timestamp) FROM all_positions_tracking')
            last_timestamp = cursor.fetchone()[0]
            conn.close()
            
            if last_timestamp:
                last_update = datetime.fromtimestamp(last_timestamp)
                age = (datetime.now() - last_update).total_seconds() / 60
                
                results['unlimited_oi'] = {
                    'last_update': last_update.strftime('%Y-%m-%d %H:%M:%S'),
                    'age_minutes': age,
                    'status': 'OK' if age < 10 else 'STALE'
                }
            else:
                results['unlimited_oi'] = {'status': 'NO_DATA'}
        except Exception as e:
            results['unlimited_oi'] = {'status': 'ERROR', 'error': str(e)}
        
        # Проверяем signal_history.db
        try:
            conn = sqlite3.connect('./data/signal_history.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT MAX(timestamp) FROM signal_history')
            last_timestamp = cursor.fetchone()[0]
            conn.close()
            
            if last_timestamp:
                last_update = datetime.fromtimestamp(last_timestamp)
                age = (datetime.now() - last_update).total_seconds() / 60
                
                results['signal_history'] = {
                    'last_update': last_update.strftime('%Y-%m-%d %H:%M:%S'),
                    'age_minutes': age,
                    'status': 'OK' if age < 60 else 'STALE'
                }
            else:
                results['signal_history'] = {'status': 'NO_DATA'}
        except Exception as e:
            results['signal_history'] = {'status': 'ERROR', 'error': str(e)}
        
        return results
    
    def check_disk_space(self) -> dict:
        """Проверка места на диске"""
        disk = psutil.disk_usage('/')
        return {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent_used': disk.percent,
            'status': 'OK' if disk.percent < 90 else 'WARNING'
        }
    
    def send_to_telegram(self, message: str):
        """Отправка в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.admin_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Health report sent to admin")
            else:
                logger.error(f"❌ Telegram error: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to send report: {e}")
    
    def run_health_check(self):
        """Запуск проверки здоровья"""
        logger.info("🏥 Running health check...")
        
        # Проверки
        processes = self.check_processes()
        databases = self.check_database_updates()
        disk = self.check_disk_space()
        
        # Проблемы?
        has_issues = False
        issues = []
        
        # Проверка процессов
        for proc, status in processes.items():
            if status == 'STOPPED':
                has_issues = True
                issues.append(f"❌ {proc} не запущен!")
        
        # Проверка БД
        for db, info in databases.items():
            if info['status'] == 'STALE':
                has_issues = True
                issues.append(f"⚠️ {db}: данные устарели ({info['age_minutes']:.0f} мин)")
            elif info['status'] == 'ERROR':
                has_issues = True
                issues.append(f"❌ {db}: ошибка")
        
        # Проверка диска
        if disk['status'] == 'WARNING':
            has_issues = True
            issues.append(f"⚠️ Диск заполнен на {disk['percent_used']}%")
        
        # Формируем отчёт
        if has_issues:
            message = "🚨 *HEALTH CHECK ALERT*\n\n"
            message += "\n".join(issues)
            message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.send_to_telegram(message)
            logger.warning("⚠️ Health issues detected!")
        else:
            # Всё OK - отправляем только раз в час
            current_hour = datetime.now().hour
            if current_hour % 6 == 0 and datetime.now().minute < 10:
                message = "✅ *HEALTH CHECK: OK*\n\n"
                message += "📊 Все системы работают\n"
                message += f"💾 Диск: {disk['free_gb']:.1f} GB свободно\n"
                
                # Статус БД
                for db, info in databases.items():
                    if info['status'] == 'OK':
                        message += f"✅ {db}: обновлено {info['age_minutes']:.0f} мин назад\n"
                
                message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.send_to_telegram(message)
            
            logger.info("✅ All systems healthy")


if __name__ == '__main__':
    monitor = HealthMonitor()
    monitor.run_health_check()
