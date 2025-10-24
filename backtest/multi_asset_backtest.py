#!/usr/bin/env python3
"""MULTI ASSET BACKTEST - все активы + индикаторы"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from indicators.smart_money.order_blocks import OrderBlocks
from indicators.smart_money.fair_value_gaps import FairValueGaps
from indicators.technical.rsi import RSI
from indicators.technical.vwap import VWAP
from indicators.technical.bollinger import BollingerBands

def backtest_asset(asset: str, indicator: str):
    """Backtest one asset with one indicator"""
    
    # Load data
    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / asset
    files = sorted(data_dir.glob("*.csv"))
    
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # 4H timeframe
    df = df.resample('4h').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    df.reset_index(inplace=True)
    
    # Add indicators
    if indicator == 'ob':
        ob = OrderBlocks()
        df = ob.find_order_blocks(df)
        signal_col = 'bullish_ob'
    elif indicator == 'fvg':
        fvg = FairValueGaps()
        df = fvg.find_fvg(df)
        signal_col = 'fvg_bullish'
    elif indicator == 'rsi':
        rsi = RSI()
        df = rsi.calculate(df)
        signal_col = 'bullish_div'
    
    # Backtest
    capital = 10000
    position = None
    trades = []
    
    for i in range(100, len(df)-18):
        price = df.iloc[i]['close']
        
        # Close
        if position and (i - position['idx']) >= 18:
            pnl_pct = (price - position['entry']) / position['entry']
            pnl = position['size'] * pnl_pct
            capital += pnl
            trades.append({'pnl': pnl, 'capital': capital})
            position = None
        
        # Open
        if position is None and df.iloc[i][signal_col]:
            position = {'idx': i, 'entry': price, 'size': capital * 0.05}
    
    if not trades:
        return None
    
    tdf = pd.DataFrame(trades)
    wins = len(tdf[tdf['pnl'] > 0])
    
    return {
        'asset': asset,
        'indicator': indicator,
        'trades': len(tdf),
        'wr': wins / len(tdf),
        'return': (tdf.iloc[-1]['capital'] - 10000) / 10000,
        'final': tdf.iloc[-1]['capital']
    }

print("\n" + "="*80)
print("MULTI-ASSET BACKTEST")
print("="*80)

assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
indicators = ['ob', 'fvg', 'rsi']

results = []

for asset in assets:
    for ind in indicators:
        print(f"Testing {asset} + {ind}...", end=' ')
        r = backtest_asset(asset, ind)
        if r:
            results.append(r)
            print(f"{r['trades']} trades, {r['wr']*100:.1f}% WR, {r['return']*100:+.1f}%")
        else:
            print("No trades")

print("\n" + "="*80)
print("TOP 10 COMBINATIONS")
print("="*80)

results = sorted(results, key=lambda x: x['return'], reverse=True)

for r in results[:10]:
    print(f"{r['asset']:10s} + {r['indicator']:5s}: {r['trades']:3d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%")
