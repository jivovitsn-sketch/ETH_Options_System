#!/bin/bash
# РЕАЛЬНЫЕ КОМАНДЫ ДЛЯ ПРОВЕРКИ СИСТЕМЫ

echo "=== ПРОВЕРКА СТАТУСА СИСТЕМЫ ==="

echo "1. АКТИВНЫЕ PYTHON ПРОЦЕССЫ:"
ps aux | grep python | grep -v grep

echo ""
echo "2. ПРОВЕРКА ПОРТОВ:"
netstat -tlnp | grep python

echo ""
echo "3. ПОСЛЕДНИЕ ЛОГИ (если есть):"
ls -la logs/ 2>/dev/null || echo "Нет директории logs"
tail -20 logs/*.log 2>/dev/null || echo "Нет лог файлов"

echo ""
echo "4. СИСТЕМНЫЕ ЛОГИ PYTHON:"
journalctl -u python* --since "1 hour ago" --no-pager | tail -10

echo ""
echo "5. CRONTAB ЗАДАЧИ:"
crontab -l

echo ""
echo "6. СВОБОДНОЕ МЕСТО:"
df -h | grep -E "(/$|/home)"

echo ""
echo "7. ПАМЯТЬ:"
free -h

echo ""
echo "8. ПОСЛЕДНИЕ ФАЙЛЫ ДАННЫХ:"
find data/ -type f -mtime -1 -exec ls -la {} \; 2>/dev/null | head -10

echo ""
echo "9. ТЕСТ TELEGRAM (без прокси):"
curl -s "https://api.telegram.org/bot8465104192:AAHaKFyt6KzvhEo1YplPiFri8QF3hwj6-qM/getMe" | head -200

echo ""
echo "10. ТЕСТ TELEGRAM (через прокси):"
curl -s --proxy "http://uQnxk4:wgu4pJ@77.83.186.47:8000" "https://api.telegram.org/bot8465104192:AAHaKFyt6KzvhEo1YplPiFri8QF3hwj6-qM/getMe" | head -200

echo ""
echo "11. ПОСЛЕДНИЕ GIT ИЗМЕНЕНИЯ:"
git log --oneline -5

echo ""
echo "12. РАЗМЕР ФАЙЛОВ СИСТЕМЫ:"
du -sh * | sort -hr | head -10
