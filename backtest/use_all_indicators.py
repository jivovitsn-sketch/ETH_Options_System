#!/usr/bin/env python3
"""ALL INDICATORS TEST - используем ВСЁ что создали"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from indicators.smart_money.fair_value_gaps import FairValueGaps
from indicators.smart_money.order_blocks import OrderBlocks

def test_strategy(name, days=365):
    # Load
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
    
    # Indicators
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    
    if name in ['fvg', 'sma_fvg']:
        fvg = FairValueGaps()
        df = fvg.find_fvg(df)
    
    if name in ['ob', 'sma_ob']:
        ob = OrderBlocks()
        df = ob.find_order_blocks(df)
    
    # Trading
    capital = 10000
    position = None
    trades = []
    
    for i in range(100, len(df)-18):
        price = df.iloc[i]['close']
        
        # Close
        if position and (i - position['idx']) >= 18:
            pnl_pct = (price - position['entry']) / position['entry']
            if position['side'] == 'SHORT':
                pnl_pct = -pnl_pct
            pnl = position['size'] * pnl_pct
            capital += pnl
            trades.append({'pnl': pnl, 'capital': capital})
            position = None
        
        # Open
        if position is None:
            signal = None
            
            if name == 'sma':
                if pd.notna(df.iloc[i]['sma20']) and pd.notna(df.iloc[i]['sma50']):
                    if price > df.iloc[i]['sma20'] > df.iloc[i]['sma50']:
                        signal = 'LONG'
                    elif price < df.iloc[i]['sma20'] < df.iloc[i]['sma50']:
                        signal = 'SHORT'
            
            elif name == 'fvg':
                if df.iloc[i]['fvg_bullish']:
                    signal = 'LONG'
                elif df.iloc[i]['fvg_bearish']:
                    signal = 'SHORT'
            
            elif name == 'ob':
                if df.iloc[i]['bullish_ob']:
                    signal = 'LONG'
                elif df.iloc[i]['bearish_ob']:
                    signal = 'SHORT'
            
            elif name == 'sma_fvg':
                sma_sig = None
                fvg_sig = None
                
                if pd.notna(df.iloc[i]['sma20']) and pd.notna(df.iloc[i]['sma50']):
                    if price > df.iloc[i]['sma20'] > df.iloc[i]['sma50']:
                        sma_sig = 'LONG'
                    elif price < df.iloc[i]['sma20'] < df.iloc[i]['sma50']:
                        sma_sig = 'SHORT'
                
                if df.iloc[i]['fvg_bullish']:
                    fvg_sig = 'LONG'
                elif df.iloc[i]['fvg_bearish']:
                    fvg_sig = 'SHORT'
                
                if sma_sig and sma_sig == fvg_sig:
                    signal = sma_sig
            
            elif name == 'sma_ob':
                sma_sig = None
                ob_sig = None
                
                if pd.notna(df.iloc[i]['sma20']) and pd.notna(df.iloc[i]['sma50']):
                    if price > df.iloc[i]['sma20'] > df.iloc[i]['sma50']:
                        sma_sig = 'LONG'
                    elif price < df.iloc[i]['sma20'] < df.iloc[i]['sma50']:
                        sma_sig = 'SHORT'
                
                if df.iloc[i]['bullish_ob']:
                    ob_sig = 'LONG'
                elif df.iloc[i]['bearish_ob']:
                    ob_sig = 'SHORT'
                
                if sma_sig and sma_sig == ob_sig:
                    signal = sma_sig
            
            if signal:
                position = {
                    'idx': i,
                    'entry': price,
                    'side': signal,
                    'size': capital * 0.05
                }
    
    if not trades:
        return {'name': name, 'trades': 0, 'wr': 0, 'return': 0, 'final': 10000}
    
    tdf = pd.DataFrame(trades)
    wins = len(tdf[tdf['pnl'] > 0])
    wr = wins / len(tdf)
    final = tdf.iloc[-1]['capital']
    ret = (final - 10000) / 10000
    
    return {'name': name, 'trades': len(tdf), 'wr': wr, 'return': ret, 'final': final}

print("\n" + "="*80)
print("ALL INDICATORS TEST - 365 days")
print("="*80)
print(f"{'Strategy':<15} {'Trades':>8} {'Win Rate':>10} {'Return':>12} {'Final':>12}")
print("-"*80)

strategies = ['sma', 'fvg', 'ob', 'sma_fvg', 'sma_ob']

results = []
for strat in strategies:
    print(f"Testing {strat}...", end=' ')
    r = test_strategy(strat, 365)
    results.append(r)
    print(f"Done")

results = sorted(results, key=lambda x: x['return'], reverse=True)

for r in results:
    print(f"{r['name']:<15} {r['trades']:>8d} {r['wr']*100:>9.1f}% {r['return']*100:>11.1f}% ${r['final']:>10,.0f}")

print("="*80)

best = results[0]
print(f"\n🏆 BEST: {best['name']} with {best['return']*100:.1f}% return, {best['wr']*100:.1f}% WR")
