#!/usr/bin/env python3
"""
РЕАЛЬНЫЙ СИСТЕМНЫЙ МОНИТОР - НЕ ЗАГЛУШКА
"""
import subprocess
import time
import json
import requests
import os
from datetime import datetime, timedelta
from pathlib import Path
import psutil

class SystemMonitor:
    def __init__(self):
        self.config_file = Path('config/telegram.json')
        self.status_file = Path('logs/system_status.json')
        self.log_file = Path('logs/monitor.log')
        
        # Создаем директории
        Path('logs').mkdir(exist_ok=True)
        
        # Загружаем конфиг Telegram
        if self.config_file.exists():
            with open(self.config_file) as f:
                config = json.load(f)
                self.token = config['bot_token'] 
                self.admin_chat = config['channels']['admin']
                self.proxies = config['proxy']
        else:
            print("ERROR: No telegram config found")
            exit(1)
        
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
    def log(self, message):
        """Реальное логирование"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        # В файл
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
        
        # На экран
        print(log_entry)
    
    def send_telegram(self, message):
        """Реальная отправка в Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.admin_chat,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, proxies=self.proxies, timeout=10)
            
            if response.status_code == 200:
                self.log(f"Telegram sent: {message[:50]}...")
                return True
            else:
                self.log(f"Telegram failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"Telegram error: {e}")
            return False
    
    def check_processes(self):
        """Проверка процессов Python"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            python_processes = []
            for line in lines:
                if 'python' in line.lower() and any(bot in line for bot in ['trader', 'monitor', 'bot']):
                    python_processes.append(line.strip())
            
            return python_processes
            
        except Exception as e:
            self.log(f"Process check error: {e}")
            return []
    
    def check_disk_space(self):
        """Проверка места на диске"""
        try:
            usage = psutil.disk_usage('/')
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3) 
            percent_used = (usage.used / usage.total) * 100
            
            return {
                'free_gb': round(free_gb, 1),
                'total_gb': round(total_gb, 1), 
                'percent_used': round(percent_used, 1)
            }
        except:
            return {'error': 'Cannot check disk'}
    
    def check_memory(self):
        """Проверка памяти"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total_gb': round(memory.total / (1024**3), 1),
                'available_gb': round(memory.available / (1024**3), 1),
                'percent_used': memory.percent
            }
        except:
            return {'error': 'Cannot check memory'}
    
    def check_recent_files(self):
        """Проверка свежих файлов данных"""
        try:
            recent_files = []
            
            # Ищем файлы моложе 24 часов
            for root, dirs, files in os.walk('data/'):
                for file in files:
                    if file.endswith(('.csv', '.xlsx', '.json')):
                        filepath = os.path.join(root, file)
                        try:
                            mtime = os.path.getmtime(filepath)
                            if time.time() - mtime < 86400:  # 24 часа
                                recent_files.append({
                                    'file': filepath,
                                    'age_hours': round((time.time() - mtime) / 3600, 1)
                                })
                        except:
                            continue
            
            return recent_files[:10]  # Первые 10
            
        except Exception as e:
            self.log(f"File check error: {e}")
            return []
    
    def ping_check(self):
        """Быстрая проверка системы (каждые 10 минут)"""
        self.log("Ping check started")
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'processes': len(self.check_processes()),
            'disk': self.check_disk_space(),
            'memory': self.check_memory(),
            'recent_files': len(self.check_recent_files())
        }
        
        # Сохраняем статус
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        # Проверяем критичные проблемы
        critical_issues = []
        
        if status['disk']['percent_used'] > 90:
            critical_issues.append(f"Disk usage: {status['disk']['percent_used']}%")
        
        if status['memory']['percent_used'] > 95:
            critical_issues.append(f"Memory usage: {status['memory']['percent_used']}%")
        
        if status['processes'] == 0:
            critical_issues.append("No Python bots running")
        
        # Отправляем только критичные проблемы
        if critical_issues:
            message = f"🚨 <b>CRITICAL ISSUES</b>\n\n" + "\n".join(f"• {issue}" for issue in critical_issues)
            self.send_telegram(message)
        
        self.log(f"Ping check complete: {len(critical_issues)} issues")
        return status
    
    def daily_summary(self):
        """Ежедневная сводка (каждые 4-6 часов)"""
        self.log("Daily summary started")
        
        processes = self.check_processes()
        disk = self.check_disk_space()
        memory = self.check_memory()
        recent_files = self.check_recent_files()
        
        # Читаем логи за последние 4 часа
        log_errors = 0
        if self.log_file.exists():
            try:
                with open(self.log_file) as f:
                    lines = f.readlines()
                    for line in lines[-200:]:  # Последние 200 строк
                        if 'ERROR' in line.upper() or 'FAIL' in line.upper():
                            log_errors += 1
            except:
                pass
        
        message = f"""
📊 <b>SYSTEM HEALTH REPORT</b>

🤖 <b>Processes:</b> {len(processes)} Python bots
💾 <b>Disk:</b> {disk['free_gb']}GB free ({disk['percent_used']}% used)
🧠 <b>Memory:</b> {memory['available_gb']}GB available ({memory['percent_used']}% used)
📁 <b>Recent Files:</b> {len(recent_files)} files updated (24h)
🚨 <b>Log Errors:</b> {log_errors} errors (4h)

<b>Running Processes:</b>
{chr(10).join(f"• {proc.split()[-1]}" for proc in processes[:3]) if processes else "• No bots detected"}

<i>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
        """
        
        self.send_telegram(message.strip())
        self.log("Daily summary sent")
    
    def run_monitor(self):
        """Запуск мониторинга"""
        self.log("System monitor started")
        self.send_telegram("🚀 <b>System Monitor Started</b>\n\nMonitoring every 10 minutes\nReports every 6 hours")
        
        last_summary = datetime.now()
        
        while True:
            try:
                # Ping check каждые 10 минут
                self.ping_check()
                
                # Summary каждые 6 часов
                if datetime.now() - last_summary > timedelta(hours=6):
                    self.daily_summary()
                    last_summary = datetime.now()
                
                # Ждем 10 минут
                time.sleep(600)
                
            except KeyboardInterrupt:
                self.log("Monitor stopped by user")
                self.send_telegram("⏹️ <b>System Monitor Stopped</b>")
                break
            except Exception as e:
                self.log(f"Monitor error: {e}")
                time.sleep(60)  # При ошибке ждем минуту

if __name__ == "__main__":
    monitor = SystemMonitor()
    
    # Тест компонентов
    print("Testing monitor components...")
    print(f"Processes: {len(monitor.check_processes())}")
    print(f"Disk: {monitor.check_disk_space()}")
    print(f"Memory: {monitor.check_memory()}")
    print(f"Recent files: {len(monitor.check_recent_files())}")
    
    # Тест Telegram
    test_sent = monitor.send_telegram("🧪 Monitor test message")
    print(f"Telegram test: {'✅' if test_sent else '❌'}")
    
    print("\nTo start monitoring: python3 bot/system_monitor.py")
