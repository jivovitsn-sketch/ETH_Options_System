#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОНИТОРИНГ ПАДЕНИЯ ПРОЦЕССОВ
Отслеживает критические процессы и отправляет уведомления при падении
"""

import os
import time
import logging
from datetime import datetime
from telegram_sender import send_admin_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessMonitor:
    def __init__(self):
        self.critical_processes = [
            'unlimited_oi_monitor.py',
            'futures_data_monitor.py', 
            'liquidations_monitor.py',
            'funding_rate_monitor.py'
        ]
        
        self.process_states = {}  # Хранит последнее состояние каждого процесса
        
    def check_processes(self):
        """Проверка состояния процессов"""
        current_states = {}
        
        try:
            result = os.popen('ps aux').read()
            
            for process in self.critical_processes:
                is_running = process in result
                current_states[process] = is_running
                
                # Проверяем изменение состояния
                if process in self.process_states:
                    was_running = self.process_states[process]
                    if was_running and not is_running:
                        self.send_alert(f"🚨 ПРОЦЕСС УПАЛ: {process}")
                    elif not was_running and is_running:
                        self.send_alert(f"✅ ПРОЦЕСС ЗАПУЩЕН: {process}")
                
                self.process_states[process] = is_running
                
            return current_states
            
        except Exception as e:
            logger.error(f"Process check failed: {e}")
            return {}
    
    def send_alert(self, message):
        """Отправка алерта"""
        try:
            full_message = f"{message}\\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            send_admin_alert("Process Alert", full_message)
            logger.info(f"Alert sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def run_monitoring(self):
        """Запуск мониторинга"""
        logger.info("Starting process monitoring...")
        
        while True:
            try:
                states = self.check_processes()
                
                # Логируем текущее состояние
                running = sum(states.values())
                total = len(self.critical_processes)
                logger.info(f"Processes: {running}/{total} running")
                
                time.sleep(60)  # Проверка каждую минуту
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(30)

if __name__ == '__main__':
    monitor = ProcessMonitor()
    monitor.run_monitoring()
