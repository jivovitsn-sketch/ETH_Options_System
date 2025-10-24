# 🚀 ETH Options Trading System

**Production-ready algorithmic trading system for crypto options**

[![Status](https://img.shields.io/badge/Status-Production-green)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()
[![Win Rate](https://img.shields.io/badge/Win%20Rate-80.8%25-brightgreen)]()

---

## 🏆 Results

### ETH Options (60 DTE Bull Call Spread)
- **Return:** +15.9% (100 days)
- **Win Rate:** 80.8%
- **Cost:** $88.63 per contract
- **Leverage:** 44x
- **Trades:** 26

### ETH Spot (for comparison)
- **Return:** +2.9% (100 days)
- **Win Rate:** 64.7%
- **Cost:** $3,939 per ETH
- **Trades:** 17

**Options outperformed Spot by 5.5x!**

---

## 📊 Real Data

All results use **real options prices from Deribit API:**

| Asset | DTE | Cost | Max Profit | ROI | Contracts ($10k) |
|-------|-----|------|------------|-----|------------------|
| **ETH** | **60** | **$88.63** | **$200** | **+125.6%** | **112** |
| ETH | 30 | $89.42 | $200 | +123.7% | 111 |
| BTC | 60 | $2,744.71 | $6,000 | +118.6% | 3.64 |

---

## 🔧 Features

- **Real Options Data** - Deribit API integration
- **Greeks** - Delta, Theta, Vega, Gamma
- **Smart Exit** - Opposite signal + time value capture
- **Multiple Assets** - BTC, ETH, SOL, XRP
- **Indicators** - Order Blocks, FVG, RSI, EMA
- **Dashboard** - HTML visualization
- **Discord Alerts** - Real-time notifications

---

## 🚀 Quick Start
```bash
# 1. Download data
python3 data/universal_downloader.py

# 2. Run backtest
python3 backtest/options_real_prices.py

# 3. View dashboard
open dashboard/index.html
```

---

## 📁 Structure
```
ETH_Options_System/
├── data/                    # Market data
│   ├── raw/                # Spot prices (BTC, ETH, SOL, XRP)
│   └── options_history/    # Options snapshots (1546 instruments)
├── indicators/             # Trading indicators
│   ├── smart_money/       # Order Blocks, FVG
│   └── technical/         # RSI, EMA, Bollinger
├── strategies/            # Options strategies
├── backtest/             # Backtest engine
├── dashboard/            # HTML dashboard
└── bot/                  # Discord alerts
```

---

## 📈 Performance

### Options vs Spot (100 days)

| Metric | Options | Spot | Winner |
|--------|---------|------|--------|
| Return | +15.9% | +2.9% | **Options 5.5x** |
| Win Rate | 80.8% | 64.7% | **Options** |
| Capital/Unit | $88.63 | $3,939 | **Options 44x** |
| Leverage | 44x | 1x | **Options** |

---

## ⚠️ Risk Disclosure

- Options trading carries **significant risk**
- Past performance **≠ future results**
- Only trade with **capital you can afford to lose**
- This is **research**, not financial advice

---

## 📝 License

MIT License - See LICENSE file

---

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** October 25, 2025
