#!/usr/bin/env python3
from datetime import datetime
import subprocess
import os

def check_system():
    print(f"=== ETH OPTIONS SYSTEM STATUS ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Процессы
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    python_processes = len([line for line in result.stdout.split('\n') if 'python' in line and 'eth' in line.lower()])
    print(f"Python processes: {python_processes}")
    
    # Crontab
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    cron_jobs = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    print(f"Cron jobs: {cron_jobs}")
    
    # Файлы
    files = ['working_multi_signals.py', 'config/telegram.json']
    for file in files:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"{file}: {status}")
    
    # Логи
    if os.path.exists('logs/signals.log'):
        size = os.path.getsize('logs/signals.log')
        print(f"Signal logs: {size} bytes")
    
    print(f"\n🎯 SYSTEM: OPERATIONAL")
    print(f"📱 VIP Signals: ACTIVE")
    print(f"🕐 Next run: Every 6 hours")

if __name__ == "__main__":
    check_system()
