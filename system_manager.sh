#!/bin/bash

case "$1" in
    start)
        echo "Запуск системы мониторинга..."
        nohup python3 futures_data_monitor.py >> logs/futures_data_monitor.log 2>&1 &
        nohup python3 liquidations_monitor.py >> logs/liquidations_monitor.log 2>&1 &
        nohup python3 funding_rate_monitor.py >> logs/funding_rate_monitor.log 2>&1 &
        nohup python3 unlimited_oi_monitor.py >> logs/unlimited_oi_monitor.py.log 2>&1 &
        nohup python3 orderbook_monitor.py >> logs/orderbook_monitor.log 2>&1 &
        nohup python3 advanced_signals_generator.py >> logs/advanced_signals_generator.log 2>&1 &
        nohup python3 process_monitor.py >> logs/process_monitor.log 2>&1 &
        echo "✅ Система запущена"
        ;;
    stop)
        echo "Остановка системы..."
        pkill -f "futures_data_monitor.py"
        pkill -f "liquidations_monitor.py"
        pkill -f "funding_rate_monitor.py"
        pkill -f "unlimited_oi_monitor.py"
        pkill -f "orderbook_monitor.py"
        pkill -f "advanced_signals_generator.py"
        pkill -f "process_monitor.py"
        echo "✅ Система остановлена"
        ;;
    status)
        echo "=== СТАТУС СИСТЕМЫ ==="
        echo "Время: $(date)"
        echo ""
        count=$(ps aux | grep -E "(futures_data|liquidations|funding_rate|unlimited_oi|process_monitor|advanced_signals|orderbook)" | grep -v grep | wc -l)
        echo "Работает процессов: $count"
        echo ""
        echo "Детальный статус:"
        ps aux | grep -E "(futures_data|liquidations|funding_rate|unlimited_oi|process_monitor|advanced_signals|orderbook)" | grep -v grep | awk '{print $11, $12, $13}'
        ;;
    restart)
        echo "Перезапуск системы..."
        $0 stop
        sleep 3
        $0 start
        ;;
    *)
        echo "Использование: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
