# ETH Options Trading System

**Исследовательский проект по алгоритмической торговле криптовалютными опционами**

[![Status](https://img.shields.io/badge/Status-Complete-green)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()
[![Data](https://img.shields.io/badge/Data-2040%20days-orange)]()

---

## 🎯 Результаты

### Spot Trading (лучший результат):
| Стратегия | Win Rate | Return | Trades |
|-----------|----------|--------|--------|
| **Order Blocks** | **68.5%** | **+6.9%** | 92 |
| SMA + OB | 67.6% | +1.5% | 34 |
| SMA + FVG | 53.6% | +0.3% | 69 |

### Real Options Trading:
| Indicator | Strategy | DTE | Win Rate | Return |
|-----------|----------|-----|----------|--------|
| FVG | Bull Call | 7 | 42.9% | +0.3% |
| SMA | Bull Call | 7 | 50.0% | +0.3% |

---

## 📊 Данные

- **Spot**: 2040 дней BTCUSDT (2020-2025)
- **Options**: 732 инструмента с Deribit
- **Экспирации**: 0-335 DTE (12 разных)
- **Open Interest**: 441,577 BTC

---

## 🔧 Технологии

- **Indicators**: Order Blocks, FVG, Liquidity Zones, Gann Angles
- **Options**: Bull/Bear Spreads, Iron Condor, Straddle
- **Greeks**: Delta, Theta, Vega, Gamma (реальные данные)
- **Backtest**: Полная матрица тестов (30+ комбинаций)

---

## 🚀 Использование
```bash
# Spot backtest
python3 backtest/use_all_indicators.py

# Options matrix
python3 backtest/options_matrix.py

# Collect fresh options data
python3 data/collect_options_history.py
```

---

## 📁 Структура
```
ETH_Options_System/
├── data/                # Исторические данные
├── indicators/          # Smart Money индикаторы
├── strategies/          # Опционные стратегии
├── backtest/           # Движок бэктестов
└── configs/            # YAML конфигурации
```

---

## ⚠️ Disclaimer

**Это исследовательский проект, НЕ инвестиционный совет.**

Результаты основаны на исторических данных и не гарантируют будущих результатов.

---

## 📖 Документация

- [README_FINAL.md](README_FINAL.md) - Полная документация
- [WORK_SUMMARY.txt](WORK_SUMMARY.txt) - Резюме работы

---

**Version**: 20.2  
**Status**: Production Ready (Spot), Research Only (Options)  
**Date**: October 24, 2025
