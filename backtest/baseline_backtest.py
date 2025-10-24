#!/usr/bin/env python3
"""
BASELINE BACKTEST - Простая стратегия на SMA
Для проверки что бэктест-движок работает
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

print("╔════════════════════════════════════════════════╗")
print("║       BASELINE BACKTEST (SMA Strategy)        ║")
print("╚════════════════════════════════════════════════╝")

# Load data
data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
files = sorted(data_dir.glob("*.csv"))[-60:]  # 60 days

dfs = []
for file in files:
    df = pd.read_csv(file)
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

print(f"\n✅ Loaded {len(df)} candles")

# Resample to hourly
df.set_index('timestamp', inplace=True)
hourly = df.resample('1h').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()
hourly.reset_index(inplace=True)

print(f"📊 Hourly candles: {len(hourly)}")

# Calculate SMA
hourly['sma20'] = hourly['close'].rolling(20).mean()
hourly['sma50'] = hourly['close'].rolling(50).mean()

# Trading
initial_capital = 10000
capital = initial_capital
position = None
trades = []

print(f"\n🚀 Starting backtest...")
print(f"Initial capital: ${capital:,.2f}")

for i in range(100, len(hourly) - 24):
    current_price = hourly.iloc[i]['close']
    sma20 = hourly.iloc[i]['sma20']
    sma50 = hourly.iloc[i]['sma50']
    
    # Close position after 24h
    if position and (i - position['entry_idx']) >= 24:
        exit_price = current_price
        price_change = (exit_price - position['entry_price']) / position['entry_price']
        
        if position['direction'] == 'BULLISH':
            if price_change > 0.02:
                pnl_pct = 1.0
            elif price_change > 0.01:
                pnl_pct = 0.5
            elif price_change < -0.01:
                pnl_pct = -0.5
            else:
                pnl_pct = price_change * 20
        else:  # BEARISH
            if price_change < -0.02:
                pnl_pct = 1.0
            elif price_change < -0.01:
                pnl_pct = 0.5
            elif price_change > 0.01:
                pnl_pct = -0.5
            else:
                pnl_pct = -price_change * 20
        
        pnl_dollars = position['size'] * pnl_pct
        capital += pnl_dollars
        
        trades.append({
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'direction': position['direction'],
            'pnl_pct': pnl_pct,
            'pnl_dollars': pnl_dollars,
            'capital': capital
        })
        
        position = None
    
    # Open new position - SIMPLE STRATEGY
    if position is None and pd.notna(sma20) and pd.notna(sma50):
        signal = None
        
        # BULLISH: price > SMA20 > SMA50
        if current_price > sma20 > sma50:
            signal = 'BULLISH'
        # BEARISH: price < SMA20 < SMA50
        elif current_price < sma20 < sma50:
            signal = 'BEARISH'
        
        if signal:
            position = {
                'entry_idx': i,
                'entry_price': current_price,
                'direction': signal,
                'size': capital * 0.05
            }

# Results
print(f"\n{'='*70}")
print(f"📊 BASELINE BACKTEST RESULTS")
print(f"{'='*70}")

if not trades:
    print("❌ No trades executed")
else:
    trades_df = pd.DataFrame(trades)
    
    total_trades = len(trades_df)
    winning = len(trades_df[trades_df['pnl_dollars'] > 0])
    losing = len(trades_df[trades_df['pnl_dollars'] < 0])
    
    win_rate = winning / total_trades if total_trades > 0 else 0
    total_pnl = trades_df['pnl_dollars'].sum()
    final_capital = trades_df.iloc[-1]['capital']
    total_return = (final_capital - initial_capital) / initial_capital
    
    print(f"Initial Capital:    ${initial_capital:,.2f}")
    print(f"Final Capital:      ${final_capital:,.2f}")
    print(f"Total P&L:          ${total_pnl:,.2f}")
    print(f"Total Return:       {total_return*100:.2f}%")
    print(f"\nTotal Trades:       {total_trades}")
    print(f"Winning Trades:     {winning}")
    print(f"Losing Trades:      {losing}")
    print(f"Win Rate:           {win_rate*100:.2f}%")
    print(f"{'='*70}")
    
    trades_df.to_csv('baseline_trades.csv', index=False)
    print(f"\n💾 Saved to baseline_trades.csv")
