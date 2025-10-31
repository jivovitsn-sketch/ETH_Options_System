#!/bin/bash
echo "⏰ Настройка CRON автоматизации..."

# Бэкап текущего crontab
crontab -l > ~/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# Создаём новый crontab
crontab -l 2>/dev/null > /tmp/new_cron

# Добавляем задачи если их нет
if ! grep -q "system_manager.py start" /tmp/new_cron; then
    cat >> /tmp/new_cron << 'ENDCRON'

# ===============================================
# ETH_Options_System - Автоматизация
# ===============================================

# Запуск всех мониторов при перезагрузке
@reboot cd /home/eth_trader/ETH_Options_System && python3 system_manager.py start >> logs/startup.log 2>&1

# Health check с автовосстановлением каждые 5 минут
*/5 * * * * cd /home/eth_trader/ETH_Options_System && python3 system_manager.py health >> logs/health_check.log 2>&1

# Запуск полной аналитики каждые 30 минут
*/30 * * * * cd /home/eth_trader/ETH_Options_System && python3 system_manager.py analytics >> logs/analytics.log 2>&1

# Автокоммит в GitHub каждые 6 часов
0 */6 * * * cd /home/eth_trader/ETH_Options_System && python3 system_manager.py git-sync >> logs/git_sync.log 2>&1

# Ежедневный бэкап баз данных в 2:00
0 2 * * * cd /home/eth_trader/ETH_Options_System && tar -czf backups/$(date +\%Y\%m\%d).tar.gz data/*.db >> logs/backup.log 2>&1

ENDCRON

    # Устанавливаем новый crontab
    crontab /tmp/new_cron
    echo "✅ Crontab обновлен!"
else
    echo "ℹ️ Автоматизация уже настроена"
fi

echo ""
echo "📋 Текущий crontab:"
crontab -l | grep -A 20 "ETH_Options_System"

rm -f /tmp/new_cron
