#!/usr/bin/env python3
"""PERIOD ANALYSIS - проверка на разных периодах"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

def test_period(days):
    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
    files = sorted(data_dir.glob("*.csv"))[-days:]
    
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    df = df.resample('4h').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    
    capital = 10000
    position = None
    trades = []
    
    for i in range(100, len(df)-18):
        price = df.iloc[i]['close']
        sma20 = df.iloc[i]['sma20']
        sma50 = df.iloc[i]['sma50']
        
        if position and (i - position['idx']) >= 18:
            exit_price = price
            pnl_pct = (exit_price - position['entry']) / position['entry']
            if position['side'] == 'SHORT':
                pnl_pct = -pnl_pct
            
            pnl = position['size'] * pnl_pct
            capital += pnl
            trades.append({'pnl': pnl, 'capital': capital})
            position = None
        
        if position is None and pd.notna(sma20) and pd.notna(sma50):
            if price > sma20 > sma50:
                position = {'idx': i, 'entry': price, 'side': 'LONG', 'size': capital * 0.05}
            elif price < sma20 < sma50:
                position = {'idx': i, 'entry': price, 'side': 'SHORT', 'size': capital * 0.05}
    
    if not trades:
        return {'days': days, 'trades': 0, 'wr': 0, 'return': 0, 'final': 10000}
    
    tdf = pd.DataFrame(trades)
    wins = len(tdf[tdf['pnl'] > 0])
    wr = wins / len(tdf)
    final = tdf.iloc[-1]['capital']
    ret = (final - 10000) / 10000
    
    return {'days': days, 'trades': len(tdf), 'wr': wr, 'return': ret, 'final': final}

print("\n" + "="*70)
print("PERIOD ANALYSIS - SMA 20/50")
print("="*70)
print(f"{'Period':<12} {'Trades':>8} {'Win Rate':>10} {'Return':>12} {'Final':>12}")
print("-"*70)

for days in [30, 60, 90, 180, 365, 730]:
    result = test_period(days)
    print(f"{result['days']:>3d} days    {result['trades']:>8d} {result['wr']*100:>9.1f}% {result['return']*100:>11.1f}% ${result['final']:>10,.0f}")

print("="*70)
