#!/bin/bash
# Остановка всех мониторов

echo "🛑 Stopping all monitors..."

pkill -f "unlimited_oi_monitor.py" && echo "  ✅ Stopped Unlimited OI Monitor"
pkill -f "futures_data_monitor.py" && echo "  ✅ Stopped Futures Data Monitor"
pkill -f "liquidations_monitor.py" && echo "  ✅ Stopped Liquidations Monitor"
pkill -f "funding_rate_monitor.py" && echo "  ✅ Stopped Funding Rate Monitor"

echo ""
echo "✅ All monitors stopped!"
