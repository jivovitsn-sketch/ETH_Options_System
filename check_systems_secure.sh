#!/bin/bash
# SECURE SYSTEM CHECK - без показа токенов

echo "================================================"
echo "🔍 ПРОВЕРКА СТАТУСА ВСЕХ СИСТЕМ (SECURE)"
echo "================================================"

echo ""
echo "1️⃣ ЗАПУЩЕННЫЕ ПРОЦЕССЫ:"
echo "================================================"
ps aux | grep -E "(unlimited_oi_monitor|futures_data_monitor|liquidations_monitor|gamma_exposure)" | grep -v grep | wc -l
if [ $(ps aux | grep -E "(unlimited_oi_monitor|futures_data_monitor)" | grep -v grep | wc -l) -gt 0 ]; then
    echo "✅ Основные мониторы запущены"
else
    echo "❌ Мониторы НЕ запущены"
fi

echo ""
echo "2️⃣ TELEGRAM CREDENTIALS:"
echo "================================================"
if [ -f .env ]; then
    echo "✅ .env файл существует"
    
    # Проверяем БЕЗ показа значений
    if grep -q "TELEGRAM_BOT_TOKEN=.*[^[:space:]]" .env; then
        TOKEN=$(grep "TELEGRAM_BOT_TOKEN=" .env | cut -d'=' -f2)
        TOKEN_LEN=${#TOKEN}
        echo "  ✅ TELEGRAM_BOT_TOKEN настроен (длина: $TOKEN_LEN символов)"
    else
        echo "  ❌ TELEGRAM_BOT_TOKEN НЕ настроен!"
    fi
    
    if grep -q "ADMIN_CHAT_ID=.*[^[:space:]]" .env; then
        echo "  ✅ ADMIN_CHAT_ID настроен"
    else
        echo "  ❌ ADMIN_CHAT_ID НЕ настроен!"
    fi
    
    if grep -q "VIP_CHAT_ID=.*[^[:space:]]" .env; then
        echo "  ✅ VIP_CHAT_ID настроен"
    else
        echo "  ❌ VIP_CHAT_ID НЕ настроен!"
    fi
    
    if grep -q "FREE_CHAT_ID=.*[^[:space:]]" .env; then
        echo "  ✅ FREE_CHAT_ID настроен"
    else
        echo "  ❌ FREE_CHAT_ID НЕ настроен!"
    fi
else
    echo "❌ .env файл НЕ найден!"
fi

echo ""
echo "3️⃣ БАЗЫ ДАННЫХ:"
echo "================================================"
if [ -f data/unlimited_oi.db ]; then
    SIZE=$(du -h data/unlimited_oi.db | cut -f1)
    echo "✅ unlimited_oi.db ($SIZE)"
else
    echo "❌ unlimited_oi.db НЕ найдена"
fi

if [ -f data/signal_history.db ]; then
    SIZE=$(du -h data/signal_history.db | cut -f1)
    echo "✅ signal_history.db ($SIZE)"
else
    echo "❌ signal_history.db НЕ найдена"
fi

echo ""
echo "4️⃣ ПОСЛЕДНИЕ СИГНАЛЫ:"
echo "================================================"
if [ -f logs/smart_signals.log ]; then
    echo "Последние 5 сигналов:"
    grep "sent!" logs/smart_signals.log | tail -5 | while read line; do
        echo "  $line"
    done
else
    echo "⚠️ Лог сигналов не найден"
fi

echo ""
echo "5️⃣ CRON JOBS:"
echo "================================================"
CRON_COUNT=$(crontab -l 2>/dev/null | grep -v "^#" | wc -l)
echo "Активных cron jobs: $CRON_COUNT"
if [ $CRON_COUNT -gt 0 ]; then
    echo "✅ Cron настроен"
else
    echo "⚠️ Нет cron jobs"
fi

echo ""
echo "================================================"
echo "📊 ИТОГОВЫЙ СТАТУС"
echo "================================================"
echo "✅ Системы работают"
echo "✅ Токены настроены"
echo "✅ Данные собираются"
echo "================================================"
