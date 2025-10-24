#!/usr/bin/env python3
"""COMPLETE BACKTEST MATRIX"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from indicators.smart_money.order_blocks import OrderBlocks
from indicators.smart_money.fair_value_gaps import FairValueGaps

def test_combo(asset: str, indicator: str):
    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / asset
    files = sorted(data_dir.glob("*.csv"))
    
    if not files:
        return None
    
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    df = df.resample('4h').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    df.reset_index(inplace=True)
    
    # SMA
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    
    # Indicators
    if indicator == 'ob':
        ob = OrderBlocks()
        df = ob.find_order_blocks(df)
        signal_col = 'bullish_ob'
    elif indicator == 'fvg':
        fvg = FairValueGaps()
        df = fvg.find_fvg(df)
        signal_col = 'fvg_bullish'
    elif indicator == 'sma':
        signal_col = None
    else:
        return None
    
    # Backtest
    capital = 10000
    position = None
    trades = []
    
    for i in range(100, len(df)-18):
        price = df.iloc[i]['close']
        
        if position and (i - position['idx']) >= 18:
            pnl_pct = (price - position['entry']) / position['entry']
            pnl = position['size'] * pnl_pct
            capital += pnl
            trades.append({'pnl': pnl, 'capital': capital})
            position = None
        
        if position is None:
            signal = False
            
            if indicator == 'sma':
                if pd.notna(df.iloc[i]['sma20']) and pd.notna(df.iloc[i]['sma50']):
                    signal = price > df.iloc[i]['sma20'] > df.iloc[i]['sma50']
            else:
                signal = df.iloc[i][signal_col]
            
            if signal:
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
print("COMPLETE BACKTEST MATRIX - ALL ASSETS")
print("="*80)

assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
indicators = ['ob', 'fvg', 'sma']

results = []

for asset in assets:
    for ind in indicators:
        print(f"Testing {asset:10s} + {ind:5s}...", end=' ')
        r = test_combo(asset, ind)
        if r:
            results.append(r)
            print(f"{r['trades']:3d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%")
        else:
            print("No data/trades")

print("\n" + "="*80)
print("RESULTS SORTED BY RETURN")
print("="*80)

results = sorted(results, key=lambda x: x['return'], reverse=True)

for i, r in enumerate(results, 1):
    print(f"{i:2d}. {r['asset']:10s} + {r['indicator']:5s}: "
          f"{r['trades']:3d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%")
