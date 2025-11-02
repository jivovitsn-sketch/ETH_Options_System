#!/bin/bash
# DEPLOYMENT SCRIPT - Signal System V2

echo "================================================"
echo "🚀 DEPLOYING SIGNAL SYSTEM V2"
echo "================================================"
echo ""

# Проверка что мы в правильной директории
if [ ! -f "send_smart_signal_v2.py" ]; then
    echo "❌ Error: send_smart_signal_v2.py not found!"
    echo "   Run this script from ~/ETH_Options_System/"
    exit 1
fi

echo "📋 Pre-deployment checks:"
echo ""

# 1. Тест v2
echo "1️⃣ Testing V2..."
python3 send_smart_signal_v2.py > /tmp/v2_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ V2 runs successfully"
else
    echo "   ❌ V2 has errors!"
    echo "   Check /tmp/v2_test.log"
    exit 1
fi

# 2. Проверка что есть сигналы
signals=$(grep "SIGNAL:" /tmp/v2_test.log | wc -l)
echo "   📊 Generated $signals signals"

# 3. Бэкап старой версии
echo ""
echo "2️⃣ Backing up old version..."
if [ -f "send_smart_signal.py" ]; then
    cp send_smart_signal.py send_smart_signal_v1_backup_$(date +%Y%m%d_%H%M%S).py
    echo "   ✅ Backup created"
else
    echo "   ⚠️ No old version found (new installation)"
fi

# 4. Деплой
echo ""
echo "3️⃣ Deploying V2..."
cp send_smart_signal_v2.py send_smart_signal.py
echo "   ✅ V2 deployed as main version"

# 5. Обновление cron
echo ""
echo "4️⃣ Checking cron..."
crontab -l > /tmp/current_cron.txt 2>/dev/null
if grep -q "send_smart_signal.py" /tmp/current_cron.txt; then
    echo "   ✅ Cron already configured for send_smart_signal.py"
    echo "   📅 Current schedule:"
    grep "send_smart_signal.py" /tmp/current_cron.txt | sed 's/^/      /'
else
    echo "   ⚠️ No cron job found"
    echo "   💡 Add manually:"
    echo "      0 */4 * * * cd ~/ETH_Options_System && python3 send_smart_signal.py"
fi

echo ""
echo "================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================"
echo ""
echo "🎯 WHAT'S NEW:"
echo "  • OI Dynamics integration ✅"
echo "  • Walls Analysis integration ✅"
echo "  • 4 new signal types ✅"
echo "  • Enhanced confidence (+15-25%) ✅"
echo ""
echo "📊 NEXT STEPS:"
echo "  1. Monitor logs/smart_signals.log"
echo "  2. Check Telegram for new signals"
echo "  3. Compare with old signals (if any)"
echo ""
echo "🚀 System is live!"
echo "================================================"
