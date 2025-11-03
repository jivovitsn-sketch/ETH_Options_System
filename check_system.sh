#!/bin/bash
echo "=== ETH OPTIONS SYSTEM STATUS ==="
echo "Время: $(date)"
echo ""
echo "Рабочие процессы:"
ps aux | grep -E "(futures_data|liquidations|funding_rate|unlimited_oi|process_monitor|send_smart_signal|advanced_signals|orderbook)" | grep -v grep | wc -l
echo ""
echo "Для детального просмотра:"
echo "ps aux | grep -E \"(futures_data|liquidations|funding_rate|unlimited_oi|process_monitor|send_smart_signal|advanced_signals|orderbook)\" | grep -v grep"
echo ""
echo "Логи в реальном времени:"
echo "tail -f logs/advanced_signals_generator.log"
echo "tail -f logs/send_smart_signal_v2.log"
