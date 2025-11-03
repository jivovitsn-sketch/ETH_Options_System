#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЕЖЕДНЕВНЫЙ АДМИНСКИЙ ОТЧЕТ
Отправляет полный отчет о состоянии системы в админский канал
"""

import sqlite3
import logging
from datetime import datetime, timedelta
import os
import json
from telegram_sender import send_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminDailyReport:
    def __init__(self):
        self.db_path = './data/unlimited_oi.db'
        
    def generate_report(self):
        """Генерация полного отчета"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_status': {},
            'data_metrics': {},
            'signal_stats': {},
            'issues': []
        }
        
        # 1. Статус процессов
        report['system_status'] = self.get_system_status()
        
        # 2. Метрики данных
        report['data_metrics'] = self.get_data_metrics()
        
        # 3. Статистика сигналов
        report['signal_stats'] = self.get_signal_stats()
        
        # 4. Проблемы
        report['issues'] = self.detect_issues(report)
        
        return report
    
    def get_system_status(self):
        """Статус системных процессов"""
        status = {}
        
        # Проверяем процессы
        processes = [
            'unlimited_oi_monitor.py',
            'futures_data_monitor.py',
            'liquidations_monitor.py',
            'funding_rate_monitor.py'
        ]
        
        try:
            result = os.popen('ps aux').read()
            for proc in processes:
                status[proc] = proc in result
        except Exception as e:
            logger.error(f"Process check failed: {e}")
            
        return status
    
    def get_data_metrics(self):
        """Метрики данных"""
        metrics = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Данные за последние 24 часа
            cutoff = int((datetime.now() - timedelta(hours=24)).timestamp())
            
            # Общее количество записей
            cursor.execute('SELECT COUNT(*) FROM all_positions_tracking WHERE timestamp > ?', (cutoff,))
            metrics['total_records_24h'] = cursor.fetchone()[0]
            
            # По активам
            assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
            for asset in assets:
                cursor.execute('SELECT COUNT(*) FROM all_positions_tracking WHERE asset = ? AND timestamp > ?', (asset, cutoff))
                metrics[f'{asset}_records_24h'] = cursor.fetchone()[0]
                
            # Свежесть данных
            cursor.execute('SELECT MAX(timestamp) FROM all_positions_tracking')
            latest_ts = cursor.fetchone()[0]
            if latest_ts:
                data_age = datetime.now().timestamp() - latest_ts
                metrics['data_freshness_minutes'] = int(data_age / 60)
            else:
                metrics['data_freshness_minutes'] = 9999
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Data metrics failed: {e}")
            metrics['error'] = str(e)
            
        return metrics
    
    def get_signal_stats(self):
        """Статистика сигналов"""
        stats = {}
        
        try:
            # Анализируем smart_signals.log
            if os.path.exists('logs/smart_signals.log'):
                with open('logs/smart_signals.log', 'r') as f:
                    lines = f.readlines()[-1000:]  # последние 1000 строк
                    
                stats['total_lines'] = len(lines)
                stats['signals_sent'] = len([l for l in lines if 'SENT' in l or 'Отправлен' in l])
                stats['errors'] = len([l for l in lines if 'ERROR' in l or 'Ошибка' in l])
                
                # Последние сигналы
                recent_signals = []
                for line in lines[-10:]:
                    if 'SENT' in line or 'signal_type' in line:
                        recent_signals.append(line.strip())
                stats['recent_signals'] = recent_signals[-3:]  # последние 3
                
        except Exception as e:
            logger.error(f"Signal stats failed: {e}")
            stats['error'] = str(e)
            
        return stats
    
    def detect_issues(self, report):
        """Обнаружение проблем"""
        issues = []
        
        # Проверка процессов
        status = report['system_status']
        for proc, running in status.items():
            if not running:
                issues.append(f"❌ Процесс {proc} не запущен")
                
        # Проверка свежести данных
        freshness = report['data_metrics'].get('data_freshness_minutes', 9999)
        if freshness > 30:  # больше 30 минут
            issues.append(f"⚠️ Данные устарели: {freshness} минут назад")
            
        # Проверка сигналов
        signals_sent = report['signal_stats'].get('signals_sent', 0)
        if signals_sent == 0:
            issues.append("⚠️ За последнее время не отправлено ни одного сигнала")
            
        return issues
    
    def send_report(self):
        """Отправка отчета в Telegram"""
        try:
            report = self.generate_report()
            
            # Форматируем сообщение
            message = "📊 ЕЖЕДНЕВНЫЙ ОТЧЕТ СИСТЕМЫ\\n"
            message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\\n\\n"
            
            # Статус процессов
            message += "🖥️ СТАТУС ПРОЦЕССОВ:\\n"
            for proc, running in report['system_status'].items():
                status = "✅" if running else "❌"
                message += f"{status} {proc}\\n"
            message += "\\n"
            
            # Данные
            metrics = report['data_metrics']
            message += "📈 ДАННЫЕ ЗА 24Ч:\\n"
            message += f"• Всего записей: {metrics.get('total_records_24h', 0):,}\\n"
            message += f"• Свежесть: {metrics.get('data_freshness_minutes', 0)} мин\\n"
            message += "\\n"
            
            # Сигналы
            stats = report['signal_stats']
            message += "🎯 СИГНАЛЫ:\\n"
            message += f"• Отправлено: {stats.get('signals_sent', 0)}\\n"
            message += f"• Ошибок: {stats.get('errors', 0)}\\n"
            message += "\\n"
            
            # Проблемы
            issues = report['issues']
            if issues:
                message += "🚨 ПРОБЛЕМЫ:\\n"
                for issue in issues[:5]:  # максимум 5 проблем
                    message += f"• {issue}\\n"
            else:
                message += "✅ Проблем не обнаружено\\n"
                
            # Отправляем
            send_message(message, is_admin=True)
            logger.info("✅ Daily admin report sent")
            
            # Сохраняем отчет в файл
            report_file = f"reports/admin_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            os.makedirs('reports', exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to send admin report: {e}")

if __name__ == '__main__':
    report = AdminDailyReport()
    report.send_report()
