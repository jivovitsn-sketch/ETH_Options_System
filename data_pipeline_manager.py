#!/usr/bin/env python3
import schedule
import time
import subprocess
import logging
from datetime import datetime
import sqlite3
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/data_pipeline.log'),
        logging.StreamHandler()
    ]
)

class DataPipelineManager:
    def __init__(self):
        self.scripts = {
            'futures': {
                'script': './futures_data_monitor.py',
                'interval_minutes': 1,
                'last_run': None,
                'timeout': 30
            },
            'liquidations': {
                'script': './liquidations_monitor.py', 
                'interval_minutes': 1,
                'last_run': None,
                'timeout': 30
            },
            'gamma': {
                'script': './gamma_exposure_calculator.py',
                'interval_minutes': 5,
                'last_run': None, 
                'timeout': 60
            },
            'funding': {
                'script': './funding_rate_monitor.py',
                'interval_minutes': 5,
                'last_run': None,
                'timeout': 30
            }
        }
        
    def run_script(self, script_name, script_config):
        """Запуск скрипта с контролем времени и ошибок"""
        try:
            logging.info(f"Запуск {script_name}...")
            result = subprocess.run(
                ['python3', script_config['script']],
                timeout=script_config['timeout'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logging.info(f"{script_name} успешно выполнен")
                script_config['last_run'] = datetime.now()
                return True
            else:
                logging.error(f"Ошибка в {script_name}: {result.stderr}")
                self.send_alert(f"🚨 СБОЙ {script_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logging.error(f"Таймаут {script_name} (> {script_config['timeout']} сек)")
            self.send_alert(f"⏰ ТАЙМАУТ {script_name}")
            return False
        except Exception as e:
            logging.error(f"Ошибка запуска {script_name}: {e}")
            self.send_alert(f"🚨 ОШИБКА {script_name}: {e}")
            return False
    
    def send_alert(self, message):
        """Отправка алерта в Telegram"""
        try:
            from telegram_helper import send_telegram_message
            send_telegram_message(message, is_alert=True)
        except Exception as e:
            logging.error(f"Не удалось отправить алерт: {e}")
    
    def check_data_freshness(self):
        """Проверка свежести данных"""
        try:
            conn = sqlite3.connect('./data/futures_data.db')
            cursor = conn.cursor()
            
            tables_to_check = ['futures_ticker', 'liquidations', 'orderbook_snapshots']
            current_time = datetime.now().timestamp()
            max_age_threshold = 300  # 5 минут
            
            alerts = []
            for table in tables_to_check:
                cursor.execute(f"SELECT MAX(timestamp) FROM {table}")
                result = cursor.fetchone()
                if result and result[0]:
                    data_age = current_time - result[0]
                    if data_age > max_age_threshold:
                        alerts.append(f"📊 Данные в {table} устарели: {data_age/60:.1f} мин назад")
            
            conn.close()
            
            if alerts:
                self.send_alert("🚨 ПРОВЕРКА СВЕЖЕСТИ ДАННЫХ:\\n" + "\\n".join(alerts))
                
        except Exception as e:
            logging.error(f"Ошибка проверки свежести данных: {e}")
    
    def backup_databases(self):
        """Создание бэкапов баз данных"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            backup_dir = f"./backups/{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            databases = [
                './data/futures_data.db',
                './data/funding_alerts.db', 
                './data/oi_signals.db'
            ]
            
            for db_path in databases:
                if os.path.exists(db_path):
                    backup_path = f"{backup_dir}/{os.path.basename(db_path)}"
                    subprocess.run(['cp', db_path, backup_path])
            
            # Удаляем старые бэкапы (оставляем последние 10)
            backups = sorted([d for d in os.listdir('./backups') if os.path.isdir(f'./backups/{d}')])
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    subprocess.run(['rm', '-rf', f'./backups/{old_backup}'])
                    
            logging.info(f"Создан бэкап: {backup_dir}")
            
        except Exception as e:
            logging.error(f"Ошибка создания бэкапа: {e}")
    
    def start(self):
        """Запуск пайплайна"""
        logging.info("🚀 Запуск системы управления данными...")
        
        # Запускаем все скрипты сразу при старте
        for name, config in self.scripts.items():
            self.run_script(name, config)
        
        # Настраиваем расписание
        schedule.every(1).minutes.do(lambda: self.run_script('futures', self.scripts['futures']))
        schedule.every(1).minutes.do(lambda: self.run_script('liquidations', self.scripts['liquidations']))
        schedule.every(5).minutes.do(lambda: self.run_script('gamma', self.scripts['gamma']))
        schedule.every(5).minutes.do(lambda: self.run_script('funding', self.scripts['funding']))
        schedule.every(10).minutes.do(self.check_data_freshness)
        schedule.every(6).hours.do(self.backup_databases)
        
        logging.info("📅 Расписание настроено. Запуск основного цикла...")
        
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    manager = DataPipelineManager()
    manager.start()
