#!/usr/bin/env python3
"""CLEAN BACKTEST - только что работает"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

def backtest_sma(days=365):
    """SMA 20/50 crossover - проверенная стратегия"""
    
    # Load data
    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
    files = sorted(data_dir.glob("*.csv"))[-days:]
    
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # 4H timeframe
    df = df.resample('4h').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    
    # Indicators
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    
    # Trading
    capital = 10000
    position = None
    trades = []
    
    for i in range(100, len(df)-18):
        price = df.iloc[i]['close']
        sma20 = df.iloc[i]['sma20']
        sma50 = df.iloc[i]['sma50']
        
        # Close after 18 periods (3 days)
        if position and (i - position['idx']) >= 18:
            exit_price = price
            pnl_pct = (exit_price - position['entry']) / position['entry']
            
            if position['side'] == 'LONG':
                pnl = position['size'] * pnl_pct
            else:
                pnl = position['size'] * -pnl_pct
            
            capital += pnl
            trades.append({
                'entry': position['entry'],
                'exit': exit_price,
                'side': position['side'],
                'pnl': pnl,
                'capital': capital
            })
            position = None
        
        # Open position
        if position is None and pd.notna(sma20) and pd.notna(sma50):
            if price > sma20 > sma50:
                position = {'idx': i, 'entry': price, 'side': 'LONG', 'size': capital * 0.05}
            elif price < sma20 < sma50:
                position = {'idx': i, 'entry': price, 'side': 'SHORT', 'size': capital * 0.05}
    
    # Results
    if not trades:
        print("No trades")
        return
    
    tdf = pd.DataFrame(trades)
    wins = len(tdf[tdf['pnl'] > 0])
    wr = wins / len(tdf)
    final = tdf.iloc[-1]['capital']
    ret = (final - 10000) / 10000
    
    print(f"\n{'='*60}")
    print(f"SMA 20/50 BACKTEST - {days} days")
    print(f"{'='*60}")
    print(f"Trades:        {len(tdf)}")
    print(f"Win Rate:      {wr*100:.1f}%")
    print(f"Total Return:  {ret*100:.1f}%")
    print(f"Final Capital: ${final:,.0f}")
    print(f"{'='*60}")
    
    tdf.to_csv('sma_trades.csv', index=False)
    print(f"Saved to sma_trades.csv")

if __name__ == "__main__":
    backtest_sma(365)
