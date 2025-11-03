#!/usr/bin/env python3
import time
import logging
import subprocess
import psutil
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/process_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROCESSES = [
    {
        'name': 'Futures Data Monitor',
        'cmd': ['python3', 'futures_data_monitor.py'],
        'restart_cmd': ['nohup', 'python3', 'futures_data_monitor.py', '>>', 'logs/futures_data_monitor.log', '2>&1', '&']
    },
    {
        'name': 'Liquidations Monitor', 
        'cmd': ['python3', 'liquidations_monitor.py'],
        'restart_cmd': ['nohup', 'python3', 'liquidations_monitor.py', '>>', 'logs/liquidations_monitor.log', '2>&1', '&']
    },
    {
        'name': 'Funding Rate Monitor',
        'cmd': ['python3', 'funding_rate_monitor.py'],
        'restart_cmd': ['nohup', 'python3', 'funding_rate_monitor.py', '>>', 'logs/funding_rate_monitor.log', '2>&1', '&']
    },
    {
        'name': 'Unlimited OI Monitor',
        'cmd': ['python3', 'unlimited_oi_monitor.py'],
        'restart_cmd': ['nohup', 'python3', 'unlimited_oi_monitor.py', '>>', 'logs/unlimited_oi_monitor.py.log', '2>&1', '&']
    }
]

def check_process(process_info):
    name = process_info['name']
    cmd = process_info['cmd']
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and ' '.join(proc.info['cmdline']) == ' '.join(cmd):
                return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            continue
    return False, None

def restart_process(process_info):
    name = process_info['name']
    restart_cmd = process_info['restart_cmd']
    
    try:
        subprocess.Popen(restart_cmd, shell=False)
        logger.info(f"✅ Restarted {name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to restart {name}: {e}")
        return False

def main():
    logger.info("🔄 Starting SILENT process monitor (no Telegram)...")
    
    while True:
        try:
            running_count = 0
            issues = []
            
            for process in PROCESSES:
                is_running, pid = check_process(process)
                if is_running:
                    running_count += 1
                else:
                    issues.append(process['name'])
                    logger.warning(f"⚠️ Process {process['name']} is not running")
                    restart_success = restart_process(process)
                    if restart_success:
                        issues.append(f"{process['name']} - restarted")
                    else:
                        issues.append(f"{process['name']} - restart failed")
            
            logger.info(f"Processes: {running_count}/{len(PROCESSES)} running")
            
            # НЕ отправляем в Telegram пока не настроены chat_id
            if issues:
                logger.warning(f"ISSUES: {', '.join(issues)}")
            
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in process monitor: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
