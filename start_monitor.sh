#!/bin/bash
# Запуск мониторинга в фоне

cd ~/ETH_Options_System

# Убиваем старый монитор если есть
pkill -f "system_monitor.py"

# Запускаем новый в фоне
nohup python3 bot/system_monitor.py > logs/monitor_output.log 2>&1 &

echo "Monitor started in background"
echo "PID: $!"
echo "Logs: logs/monitor_output.log"
echo ""
echo "To check status: ps aux | grep system_monitor"
echo "To stop: pkill -f system_monitor.py"
