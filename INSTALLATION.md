# Installation Guide - ETH Options System

## 🛠️ Quick Setup

### 1. Clone & Setup
```bash
cd ~/
git clone [repo-url] ETH_Options_System
cd ETH_Options_System
```

### 2. Install Dependencies
```bash
pip install pandas numpy requests pyyaml --break-system-packages
```

### 3. Initialize System
```bash
python3 paper_trading_journal.py
```

### 4. Setup Automation
```bash
# Add to crontab
echo "0 */6 * * * cd ~/ETH_Options_System && python3 working_multi_signals.py >> logs/signals.log 2>&1" | crontab -
echo "0 8,16 * * * cd ~/ETH_Options_System && python3 strategy_selector.py >> logs/strategy_recommendations.log 2>&1" | crontab -
```

### 5. Configure Telegram (Optional)
```bash
# Edit config/telegram.json with your bot token
{
  "bot_token": "YOUR_BOT_TOKEN",
  "channels": {
    "vip": "YOUR_CHANNEL_ID"
  }
}
```

## ✅ Verification

### Test Commands
```bash
# Check system status
python3 trading_dashboard.py

# Test signal generation
python3 working_multi_signals.py

# Verify backtest data
python3 strategy_ranking.py
```

### Expected Output
```
=== PAPER TRADING DASHBOARD ===
💰 Portfolio Value: $50,000
📊 ROI: 0.0%
🔄 Open Positions: 0
```

## 🚨 Troubleshooting

### Common Issues
1. **Permission denied**: Use `--break-system-packages` for pip
2. **Cron not working**: Check crontab with `crontab -l`
3. **Missing files**: Initialize with `paper_trading_journal.py`

### File Structure Check
```bash
ls -la data/
# Should show: paper_trades.csv, portfolio_status.json, fixed_backtest_results.csv
```
