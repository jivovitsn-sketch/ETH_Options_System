#!/bin/bash
# СТРОГИЙ ПЕРЕЗАПУСК СИСТЕМЫ

echo "🔄 СИСТЕМА ПЕРЕЗАПУСКА"
echo "="*50

# Kill all
echo "1. Останавливаем всё..."
killall python3 2>/dev/null
sleep 3

# Pre-flight
echo "2. Pre-flight check..."
if [ ! -f "data/unlimited_oi.db" ]; then
    echo "❌ База данных не найдена!"
    exit 1
fi

# Start monitors
echo "3. Запуск мониторов..."
nohup python3 futures_data_monitor.py > logs/futures_monitor.log 2>&1 &
sleep 2
nohup python3 unlimited_oi_monitor.py > logs/oi_monitor.log 2>&1 &
sleep 2
nohup python3 eth_options_collector.py > logs/eth_options.log 2>&1 &

# Validate
sleep 5
echo "4. Проверка..."
PROCS=$(ps aux | grep -E "futures_data_monitor|unlimited_oi_monitor|eth_options_collector" | grep -v grep | wc -l)

if [ $PROCS -eq 3 ]; then
    echo "✅ Все 3 монитора запущены"
else
    echo "❌ Запущено только $PROCS процессов!"
    exit 1
fi

echo "✅ СИСТЕМА ЗАПУЩЕНА"
