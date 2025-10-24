#!/usr/bin/env python3
"""FULL MATRIX - все активы, все стратегии"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import json
from indicators.smart_money.order_blocks import OrderBlocks

print("\n" + "="*80)
print("FULL ASSET MATRIX - SPOT ONLY (no SOL/XRP options on Deribit)")
print("="*80)

ob = OrderBlocks()

results = []

for asset in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']:
    print(f"\nTesting {asset}...")
    
    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / asset
    files = sorted(data_dir.glob("*.csv"))
    
    if not files:
        print(f"  No data")
        continue
    
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    df = df.resample('4h').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    df.reset_index(inplace=True)
    
    df = ob.find_order_blocks(df)
    
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
        
        if position is None and df.iloc[i]['bullish_ob']:
            position = {'idx': i, 'entry': price, 'size': capital * 0.05}
    
    if trades:
        tdf = pd.DataFrame(trades)
        wins = len(tdf[tdf['pnl'] > 0])
        
        result = {
            'asset': asset,
            'trades': len(tdf),
            'wr': wins / len(tdf),
            'return': (tdf.iloc[-1]['capital'] - 10000) / 10000,
            'final': tdf.iloc[-1]['capital']
        }
        
        results.append(result)
        
        print(f"  {result['trades']} trades, {result['wr']*100:.1f}% WR, {result['return']*100:+.1f}%")

results = sorted(results, key=lambda x: x['return'], reverse=True)

print("\n" + "="*80)
print("RESULTS")
print("="*80)

for i, r in enumerate(results, 1):
    print(f"{i}. {r['asset']:10s}: {r['trades']:3d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%")

with open('full_asset_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Saved to full_asset_results.json")
