#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTEM MANAGER - Центральный менеджер системы
"""

import subprocess
import time
import sqlite3
import logging
import os
from datetime import datetime, timedelta
import psutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/system_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.monitors = {
            'futures': {
                'script': './futures_data_monitor.py',
                'enabled': True,
                'restart_on_fail': True
            },
            'unlimited_oi': {
                'script': './unlimited_oi_monitor.py',
                'enabled': True,
                'restart_on_fail': True
            },
            'liquidations': {
                'script': './liquidations_monitor.py',
                'enabled': True,
                'restart_on_fail': True
            },
            'funding': {
                'script': './funding_rate_monitor.py',
                'enabled': True,
                'restart_on_fail': True
            }
        }
        
        self.analytics = {
            'gamma': './gamma_exposure_calculator.py',
            'max_pain': './max_pain_calculator.py',
            'volatility': './volatility_greeks_analyzer.py'
        }
        
        self.signal_generator = './advanced_signals_generator.py'
    
    def is_process_running(self, script_name):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info.get('cmdline', [])
                if cmdline and script_name in ' '.join(cmdline):
                    return True, proc.info['pid']
            return False, None
        except Exception as e:
            logger.error(f"Ошибка проверки процесса {script_name}: {e}")
            return False, None
    
    def start_monitor(self, name, config):
        script = config['script']
        is_running, pid = self.is_process_running(script)
        if is_running:
            logger.info(f"✅ {name} уже запущен (PID: {pid})")
            return True
        
        try:
            log_file = f"./logs/{name}.log"
            cmd = f"nohup python3 {script} > {log_file} 2>&1 &"
            subprocess.Popen(cmd, shell=True, cwd=self.base_dir)
            time.sleep(2)
            
            is_running, pid = self.is_process_running(script)
            if is_running:
                logger.info(f"🚀 {name} запущен (PID: {pid})")
                return True
            else:
                logger.error(f"❌ {name} не запустился")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка запуска {name}: {e}")
            return False
    
    def stop_monitor(self, name, config):
        script = config['script']
        is_running, pid = self.is_process_running(script)
        
        if not is_running:
            logger.info(f"ℹ️ {name} не запущен")
            return True
        
        try:
            subprocess.run(['kill', str(pid)], check=True)
            logger.info(f"🛑 {name} остановлен (PID: {pid})")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка остановки {name}: {e}")
            return False
    
    def start_all_monitors(self):
        logger.info("=" * 80)
        logger.info("🚀 ЗАПУСК ВСЕХ МОНИТОРОВ")
        logger.info("=" * 80)
        
        for name, config in self.monitors.items():
            if config['enabled']:
                self.start_monitor(name, config)
        
        logger.info("=" * 80)
        logger.info("✅ Запуск завершен")
        self.show_status()
    
    def stop_all_monitors(self):
        logger.info("=" * 80)
        logger.info("🛑 ОСТАНОВКА ВСЕХ МОНИТОРОВ")
        logger.info("=" * 80)
        
        for name, config in self.monitors.items():
            self.stop_monitor(name, config)
        
        logger.info("=" * 80)
        logger.info("✅ Остановка завершена")
    
    def restart_all_monitors(self):
        logger.info("🔄 ПЕРЕЗАПУСК ВСЕХ МОНИТОРОВ")
        self.stop_all_monitors()
        time.sleep(3)
        self.start_all_monitors()
    
    def show_status(self):
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 СТАТУС СИСТЕМЫ")
        logger.info("=" * 80)
        
        logger.info("\n🔍 МОНИТОРЫ:")
        running_count = 0
        for name, config in self.monitors.items():
            is_running, pid = self.is_process_running(config['script'])
            status = f"✅ Работает (PID: {pid})" if is_running else "❌ Не запущен"
            logger.info(f"  {name:15} {status}")
            if is_running:
                running_count += 1
        
        logger.info("\n📊 СВЕЖЕСТЬ ДАННЫХ:")
        self.check_data_freshness()
        
        logger.info("\n💾 ДИСКОВОЕ ПРОСТРАНСТВО:")
        self.check_disk_space()
        
        logger.info("\n" + "=" * 80)
        logger.info(f"📈 Мониторы: {running_count}/{len(self.monitors)}")
        logger.info("=" * 80)
    
    def check_data_freshness(self):
        try:
            conn = sqlite3.connect('./data/unlimited_oi.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT asset, 
                       MAX(timestamp) as last_ts,
                       datetime(MAX(timestamp), 'unixepoch') as last_update
                FROM all_positions_tracking 
                GROUP BY asset
            """)
            results = cursor.fetchall()
            conn.close()
            
            now = datetime.now().timestamp()
            for asset, last_ts, last_update in results:
                age_minutes = (now - last_ts) / 60
                status = "🟢" if age_minutes < 15 else "🟡" if age_minutes < 60 else "🔴"
                logger.info(f"  {status} {asset:6} {age_minutes:.1f} мин назад ({last_update})")
        except Exception as e:
            logger.error(f"  ❌ Ошибка проверки OI: {e}")
    
    def check_disk_space(self):
        try:
            usage = psutil.disk_usage('.')
            free_gb = usage.free / (1024**3)
            percent = usage.percent
            
            status = "🟢" if percent < 80 else "🟡" if percent < 90 else "🔴"
            logger.info(f"  {status} Свободно: {free_gb:.1f} GB ({100-percent:.1f}% свободно)")
        except Exception as e:
            logger.error(f"  ❌ Ошибка проверки диска: {e}")
    
    def health_check(self):
        logger.info("=" * 80)
        logger.info("🏥 HEALTH CHECK")
        logger.info("=" * 80)
        
        issues = []
        
        logger.info("\n1️⃣ Проверка мониторов...")
        for name, config in self.monitors.items():
            if not config['enabled']:
                continue
            
            is_running, pid = self.is_process_running(config['script'])
            if not is_running:
                issue = f"Монитор {name} не запущен"
                issues.append(issue)
                logger.warning(f"  ⚠️ {issue}")
                
                if config['restart_on_fail']:
                    logger.info(f"  🔄 Перезапускаем {name}...")
                    self.start_monitor(name, config)
        
        logger.info("\n2️⃣ Проверка свежести данных...")
        try:
            conn = sqlite3.connect('./data/unlimited_oi.db')
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(timestamp) FROM all_positions_tracking")
            last_ts = cursor.fetchone()[0]
            conn.close()
            
            age_minutes = (datetime.now().timestamp() - last_ts) / 60
            if age_minutes > 30:
                issue = f"Данные OI устарели на {age_minutes:.1f} минут"
                issues.append(issue)
                logger.warning(f"  ⚠️ {issue}")
            else:
                logger.info(f"  ✅ Данные OI свежие ({age_minutes:.1f} мин)")
        except Exception as e:
            issue = f"Ошибка проверки данных: {e}"
            issues.append(issue)
            logger.error(f"  ❌ {issue}")
        
        logger.info("\n3️⃣ Проверка диска...")
        try:
            usage = psutil.disk_usage('.')
            if usage.percent > 90:
                issue = f"Диск заполнен на {usage.percent}%"
                issues.append(issue)
                logger.warning(f"  ⚠️ {issue}")
            else:
                logger.info(f"  ✅ Диск: {100-usage.percent:.1f}% свободно")
        except Exception as e:
            logger.error(f"  ❌ Ошибка проверки диска: {e}")
        
        logger.info("\n" + "=" * 80)
        if not issues:
            logger.info("✅ ВСЕ СИСТЕМЫ РАБОТАЮТ НОРМАЛЬНО")
        else:
            logger.warning(f"⚠️ ОБНАРУЖЕНО {len(issues)} ПРОБЛЕМ:")
            for issue in issues:
                logger.warning(f"  • {issue}")
        logger.info("=" * 80)
        
        return len(issues) == 0
    
    def run_analytics(self):
        logger.info("=" * 80)
        logger.info("📊 ЗАПУСК АНАЛИТИКИ")
        logger.info("=" * 80)
        
        for name, script in self.analytics.items():
            logger.info(f"\n🔄 Запуск {name}...")
            try:
                result = subprocess.run(
                    ['python3', script],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ {name} завершен успешно")
                else:
                    logger.error(f"❌ {name} завершился с ошибкой: {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.error(f"⏱️ {name} превысил таймаут (5 мин)")
            except Exception as e:
                logger.error(f"❌ Ошибка запуска {name}: {e}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ АНАЛИТИКА ЗАВЕРШЕНА")
        logger.info("=" * 80)
    
    def git_sync(self):
        logger.info("=" * 80)
        logger.info("🔄 GIT SYNC")
        logger.info("=" * 80)
        
        try:
            result = subprocess.run(['git', 'status', '--short'], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            
            if result.stdout.strip():
                logger.info("📝 Обнаружены изменения:")
                logger.info(result.stdout)
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                commit_msg = f"AUTO: [{timestamp}] System update"
                
                subprocess.run(['git', 'add', '.'], cwd=self.base_dir)
                subprocess.run(['git', 'commit', '-m', commit_msg], cwd=self.base_dir)
                subprocess.run(['git', 'push'], cwd=self.base_dir)
                
                logger.info("✅ Изменения запушены в GitHub")
            else:
                logger.info("ℹ️ Нет изменений для коммита")
        
        except Exception as e:
            logger.error(f"❌ Ошибка Git sync: {e}")
        
        logger.info("=" * 80)


def main():
    import sys
    
    manager = SystemManager()
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 system_manager.py start       - Запустить все мониторы")
        print("  python3 system_manager.py stop        - Остановить все мониторы")
        print("  python3 system_manager.py restart     - Перезапустить все мониторы")
        print("  python3 system_manager.py status      - Показать статус")
        print("  python3 system_manager.py health      - Health check с автофиксом")
        print("  python3 system_manager.py analytics   - Запустить аналитику")
        print("  python3 system_manager.py git-sync    - Синхронизация с GitHub")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        manager.start_all_monitors()
    elif command == 'stop':
        manager.stop_all_monitors()
    elif command == 'restart':
        manager.restart_all_monitors()
    elif command == 'status':
        manager.show_status()
    elif command == 'health':
        manager.health_check()
    elif command == 'analytics':
        manager.run_analytics()
    elif command == 'git-sync':
        manager.git_sync()
    else:
        print(f"❌ Неизвестная команда: {command}")


if __name__ == '__main__':
    main()
