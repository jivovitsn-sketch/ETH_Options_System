#!/bin/bash
# ПРОВЕРКА ЗДОРОВЬЯ СИСТЕМЫ

echo "🏥 HEALTH CHECK"
echo "="*50

# 1. Процессы
PROCS=$(ps aux | grep -E "futures_data_monitor|unlimited_oi_monitor|eth_options_collector" | grep -v grep | wc -l)
if [ $PROCS -eq 3 ]; then
    echo "✅ Процессы: 3/3"
else
    echo "❌ Процессы: $PROCS/3"
fi

# 2. Данные
python3 << 'ENDPY'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/unlimited_oi.db')
cursor = conn.cursor()
cursor.execute("SELECT MAX(timestamp) FROM all_positions_tracking")
ts = cursor.fetchone()[0]
mins = (datetime.now() - datetime.fromtimestamp(ts)).total_seconds() / 60

if mins < 15:
    print(f"✅ Данные: {mins:.1f} мин (свежие)")
else:
    print(f"❌ Данные: {mins:.1f} мин (устарели)")
conn.close()
ENDPY

# 3. Место
FREE=$(df -h . | tail -1 | awk '{print $4}')
echo "✅ Место: $FREE свободно"

# 4. Git
if git diff --quiet; then
    echo "✅ Git: синхронизирован"
else
    echo "⚠️  Git: есть несохранённые изменения"
fi

echo "="*50
