#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVANCED HEALTH MONITOR
Мониторинг и автоматический перезапуск всех систем
"""

import os
import psutil
import subprocess
import sqlite3
from telegram_sender import send_admin_message
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram_sender import send_to_telegram

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedHealthMonitor:
    """Продвинутый мониторинг с автозапуском"""
    
    def __init__(self):
        self.admin_chat = os.getenv('ADMIN_CHAT_ID')
        
        # КРИТИЧЕСКИЕ ПРОЦЕССЫ (должны работать постоянно)
        self.critical_processes = {
            'unlimited_oi_monitor.py': {
                'name': 'Unlimited OI Monitor',
                'restart_cmd': 'python3 unlimited_oi_monitor.py',
                'max_restarts': 3
            },
            'futures_data_monitor.py': {
                'name': 'Futures Data Monitor',
                'restart_cmd': 'python3 futures_data_monitor.py',
                'max_restarts': 3
            },
            'liquidations_monitor.py': {
                'name': 'Liquidations Monitor',
                'restart_cmd': 'python3 liquidations_monitor.py',
                'max_restarts': 3
            },
            'funding_rate_monitor.py': {
                'name': 'Funding Rate Monitor',
                'restart_cmd': 'python3 funding_rate_monitor.py',
                'max_restarts': 3
            }
        }
        
        # Счётчик перезапусков
        self.restart_counts = {proc: 0 for proc in self.critical_processes}
        
        # Последняя проверка БД
        self.last_db_check = {}
    
    def is_process_running(self, script_name: str) -> bool:
        """Проверка запущен ли процесс"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and script_name in ' '.join(cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start_process(self, script_name: str, cmd: str) -> bool:
        """Запуск процесса"""
        try:
            logger.info(f"🚀 Starting {script_name}...")
            
            # Запускаем в фоне
            subprocess.Popen(
                cmd.split(),
                stdout=open(f'logs/{script_name}.log', 'a'),
                stderr=subprocess.STDOUT,
                cwd='/home/eth_trader/ETH_Options_System'
            )
            
            logger.info(f"✅ {script_name} started!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start {script_name}: {e}")
            return False
    
    def check_database_freshness(self, db_path: str, table: str, 
                                  max_age_minutes: int) -> dict:
        """Проверка свежести данных в БД"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT MAX(timestamp) FROM {table}')
            last_timestamp = cursor.fetchone()[0]
            conn.close()
            
            if not last_timestamp:
                return {
                    'status': 'NO_DATA',
                    'age_minutes': 999999,
                    'last_update': None
                }
            
            last_update = datetime.fromtimestamp(last_timestamp)
            age_minutes = (datetime.now() - last_update).total_seconds() / 60
            
            status = 'OK' if age_minutes < max_age_minutes else 'STALE'
            
            return {
                'status': status,
                'age_minutes': age_minutes,
                'last_update': last_update.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'age_minutes': 999999
            }
    
    def check_and_restart_processes(self) -> list:
        """Проверка и перезапуск процессов"""
        issues = []
        restarted = []
        
        for script_name, config in self.critical_processes.items():
            name = config['name']
            
            if not self.is_process_running(script_name):
                logger.warning(f"⚠️ {name} is DOWN!")
                
                # Проверяем счётчик перезапусков
                if self.restart_counts[script_name] < config['max_restarts']:
                    
                    logger.info(f"🔄 Attempting restart ({self.restart_counts[script_name] + 1}/{config['max_restarts']})...")
                    
                    if self.start_process(script_name, config['restart_cmd']):
                        self.restart_counts[script_name] += 1
                        restarted.append(name)
                        
                        msg = f"🔄 AUTO-RESTARTED: {name}\n"
                        msg += f"Restart #{self.restart_counts[script_name]}/{config['max_restarts']}"
                        send_to_telegram(msg, self.admin_chat)
                    else:
                        issues.append(f"❌ Failed to restart {name}")
                else:
                    issues.append(f"❌ {name} DOWN (max restarts reached!)")
                    
                    msg = f"🚨 CRITICAL: {name} DOWN!\n"
                    msg += f"Max restarts ({config['max_restarts']}) reached.\n"
                    msg += f"Manual intervention required!"
                    send_to_telegram(msg, self.admin_chat)
            else:
                # Процесс работает - сбрасываем счётчик
                if self.restart_counts[script_name] > 0:
                    logger.info(f"✅ {name} stable - resetting restart counter")
                    self.restart_counts[script_name] = 0
        
        return issues, restarted
    
    def check_databases(self) -> list:
        """Проверка свежести данных"""
        db_checks = {
            'Unlimited OI': {
                'path': './data/unlimited_oi.db',
                'table': 'all_positions_tracking',
                'max_age': 10  # минут
            },
            'Signal History': {
                'path': './data/signal_history.db',
                'table': 'signal_history',
                'max_age': 240  # 4 часа
            }
        }
        
        issues = []
        
        for name, config in db_checks.items():
            result = self.check_database_freshness(
                config['path'],
                config['table'],
                config['max_age']
            )
            
            if result['status'] == 'STALE':
                issues.append(
                    f"⚠️ {name}: data is {result['age_minutes']:.0f} min old"
                )
            elif result['status'] == 'ERROR':
                issues.append(f"❌ {name}: {result.get('error', 'unknown error')}")
        
        return issues
    
    def check_disk_space(self) -> list:
        """Проверка места на диске"""
        issues = []
        
        disk = psutil.disk_usage('/')
        
        if disk.percent > 90:
            issues.append(f"🔴 Disk {disk.percent}% full!")
        elif disk.percent > 80:
            issues.append(f"⚠️ Disk {disk.percent}% full")
        
        return issues
    
    def run_health_check(self):
        """Основной цикл проверки"""
        logger.info("=" * 60)
        logger.info("🏥 ADVANCED HEALTH CHECK")
        logger.info("=" * 60)
        
        all_issues = []
        
        # 1. Проверка и перезапуск процессов
        logger.info("\n1️⃣ Checking critical processes...")
        process_issues, restarted = self.check_and_restart_processes()
        all_issues.extend(process_issues)
        
        if restarted:
            logger.info(f"🔄 Restarted: {', '.join(restarted)}")
        
        # 2. Проверка БД
        logger.info("\n2️⃣ Checking databases...")
        db_issues = self.check_databases()
        all_issues.extend(db_issues)
        
        # 3. Проверка диска
        logger.info("\n3️⃣ Checking disk space...")
        disk_issues = self.check_disk_space()
        all_issues.extend(disk_issues)
        
        # 4. Отправка отчёта
        if all_issues:
            logger.warning(f"⚠️ Found {len(all_issues)} issues!")
            
            msg = f"🚨 *HEALTH ALERT*\n\n"
            msg += "\n".join(all_issues)
            msg += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            send_to_telegram(msg, self.admin_chat)
            
        else:
            logger.info("✅ All systems healthy!")
            
            # Отправляем OK каждые 6 часов
            current_hour = datetime.now().hour
            if current_hour % 6 == 0 and datetime.now().minute < 10:
                msg = "✅ *HEALTH: OK*\n\n"
                msg += "All systems operational\n"
                msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_to_telegram(msg, self.admin_chat)
        
        logger.info("=" * 60)


if __name__ == '__main__':
    monitor = AdvancedHealthMonitor()
    monitor.run_health_check()
