#!/bin/bash
# ДИАГНОСТИЧЕСКИЕ КОМАНДЫ

echo "=== ДИАГНОСТИКА TELEGRAM БОТА ==="

echo "1. Тест Telegram API (прямое подключение):"
curl -s "https://api.telegram.org/bot8465104192:AAHaKFyt6KzvhEo1YplPiFri8QF3hwj6-qM/getMe" | python3 -m json.tool

echo ""
echo "2. Тест Telegram API (через прокси):"
curl -s --proxy "http://uQnxk4:wgu4pJ@77.83.186.47:8000" \
  "https://api.telegram.org/bot8465104192:AAHaKFyt6KzvhEo1YplPiFri8QF3hwj6-qM/getMe" | python3 -m json.tool

echo ""
echo "3. Отправка тестового сообщения:"
python3 -c "
from bot.telegram_alerts_final import TelegramAlertsFinal
t = TelegramAlertsFinal()
result = t.send_message(t.channels['admin'], '🧪 Diagnostic test message')
print(f'Message sent: {result}')
"

echo ""
echo "4. Проверка активных соединений:"
netstat -an | grep :80

echo ""
echo "5. Проверка DNS:"
nslookup api.telegram.org

echo ""
echo "6. Проверка прокси:"
curl -s --proxy "http://uQnxk4:wgu4pJ@77.83.186.47:8000" "https://httpbin.org/ip"
