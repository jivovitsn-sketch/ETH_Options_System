#!/bin/bash
# Запуск всех мониторов данных

cd /home/eth_trader/ETH_Options_System

echo "🚀 Starting all data monitors..."

# Unlimited OI Monitor
if ! pgrep -f "unlimited_oi_monitor.py" > /dev/null; then
    echo "  Starting Unlimited OI Monitor..."
    nohup python3 unlimited_oi_monitor.py >> logs/unlimited_oi.log 2>&1 &
    echo "  ✅ Started"
else
    echo "  ℹ️  Unlimited OI Monitor already running"
fi

# Futures Data Monitor
if ! pgrep -f "futures_data_monitor.py" > /dev/null; then
    echo "  Starting Futures Data Monitor..."
    nohup python3 futures_data_monitor.py >> logs/futures_data.log 2>&1 &
    echo "  ✅ Started"
else
    echo "  ℹ️  Futures Data Monitor already running"
fi

# Liquidations Monitor
if ! pgrep -f "liquidations_monitor.py" > /dev/null; then
    echo "  Starting Liquidations Monitor..."
    nohup python3 liquidations_monitor.py >> logs/liquidations.log 2>&1 &
    echo "  ✅ Started"
else
    echo "  ℹ️  Liquidations Monitor already running"
fi

# Funding Rate Monitor
if ! pgrep -f "funding_rate_monitor.py" > /dev/null; then
    echo "  Starting Funding Rate Monitor..."
    nohup python3 funding_rate_monitor.py >> logs/funding_rate.log 2>&1 &
    echo "  ✅ Started"
else
    echo "  ℹ️  Funding Rate Monitor already running"
fi

echo ""
echo "✅ All monitors checked/started!"
