#!/bin/bash
echo "================================================"
echo "🚀 ЗАПУСК МОНИТОРИНГА И УВЕДОМЛЕНИЙ"
echo "================================================"

cd ~/ETH_Options_System

echo "1. Проверяем исправления..."
python3 -c "from telegram_sender import send_message; print('✅ Telegram sender работает')"

echo "2. Запускаем ежедневный отчет..."
python3 admin_daily_report.py

echo "3. Проверяем процессы..."
python3 -c "
import os
result = os.popen('ps aux').read()
processes = ['unlimited_oi_monitor.py', 'futures_data_monitor.py', 'liquidations_monitor.py', 'funding_rate_monitor.py']
for p in processes:
    if p in result:
        print(f'✅ {p} - ЗАПУЩЕН')
    else:
        print(f'❌ {p} - НЕ ЗАПУЩЕН')
"

echo "4. Проверяем последние сигналы..."
tail -5 logs/smart_signals.log | grep -E "(SENT|ERROR|signal_type)"

echo "5. Добавляем в cron ежедневные отчеты..."
(crontab -l 2>/dev/null; echo "0 9 * * * cd ~/ETH_Options_System && python3 admin_daily_report.py >> logs/admin_reports.log 2>&1") | crontab -

echo "6. Запускаем мониторинг процессов в фоне..."
nohup python3 process_monitor.py >> logs/process_monitor.log 2>&1 &

echo ""
echo "================================================"
echo "✅ МОНИТОРИНГ ЗАПУЩЕН!"
echo "================================================"
echo ""
echo "📊 ЧТО БУДЕТ РАБОТАТЬ:"
echo "   • Ежедневные отчеты в 9:00"
echo "   • Мгновенные уведомления о падении процессов"
echo "   • Исправлена отправка health monitor"
echo "   • Исправлена отправка сигналов"
echo ""
echo "🔍 ПРОВЕРКА ЧЕРЕЗ 5 МИНУТ:"
echo "   tail -f logs/health_monitor.log"
echo "   tail -f logs/smart_signals.log"
echo "   tail -f logs/process_monitor.log"
echo ""
echo "📱 ЖДИТЕ УВЕДОМЛЕНИЯ В АДМИНСКОМ КАНАЛЕ!"
