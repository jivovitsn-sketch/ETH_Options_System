#!/usr/bin/env python3
"""FINAL TEST - ENSEMBLE V3 (ML + NATAL ASTRO)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from ml.ensemble_v3 import EnsembleV3

def run_backtest():
    print("╔════════════════════════════════════════════════╗")
    print("║   FINAL TEST: ENSEMBLE V3 (ML + NATAL)       ║")
    print("╚════════════════════════════════════════════════╝")
    
    # Load Ensemble
    ensemble = EnsembleV3(ml_weight=0.50, astro_weight=0.50)
    ensemble.load_ml_models('ml_agent_models_new.pkl')
    
    # Load data
    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
    files = sorted(data_dir.glob("*.csv"))[-60:]
    
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    df = pd.concat(dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Resample to 4H
    df.set_index('timestamp', inplace=True)
    resampled = df.resample('4h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'turnover': 'sum'
    }).dropna()
    resampled.reset_index(inplace=True)
    
    print(f"\n✅ {len(resampled)} candles (4H timeframe)")
    
    # Trading
    initial_capital = 10000
    capital = initial_capital
    position = None
    trades = []
    
    hold_periods = 18  # 3 days
    
    for i in range(100, len(resampled) - hold_periods):
        current_price = resampled.iloc[i]['close']
        current_date = resampled.iloc[i]['timestamp']
        
        # Close position
        if position and (i - position['entry_idx']) >= hold_periods:
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
            else:
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
                'pnl_pct': pnl_pct,
                'pnl_dollars': pnl_dollars,
                'capital': capital,
                'direction': position['direction']
            })
            
            position = None
        
        # Open position
        if position is None:
            try:
                window = resampled.iloc[max(0, i-100):i].copy()
                prediction = ensemble.predict(window, symbol='BTCUSDT', date=current_date)
                
                # Более низкий порог благодаря Natal Astro
                if prediction['prediction'] != 'NEUTRAL' and prediction['confidence'] > 0.52:
                    position = {
                        'entry_idx': i,
                        'entry_price': current_price,
                        'direction': prediction['prediction'],
                        'size': capital * 0.05
                    }
            except Exception as e:
                print(f"⚠️  Error: {e}")
    
    # Results
    if not trades:
        print(f"\n❌ No trades")
        return
    
    trades_df = pd.DataFrame(trades)
    
    total_trades = len(trades_df)
    winning = len(trades_df[trades_df['pnl_dollars'] > 0])
    win_rate = winning / total_trades
    
    final_capital = trades_df.iloc[-1]['capital']
    total_return = (final_capital - initial_capital) / initial_capital
    
    print(f"\n{'='*70}")
    print(f"📊 ENSEMBLE V3 RESULTS")
    print(f"{'='*70}")
    print(f"Trades:         {total_trades}")
    print(f"Win Rate:       {win_rate*100:.1f}%")
    print(f"Return:         {total_return*100:+.1f}%")
    print(f"Final Capital:  ${final_capital:,.0f}")
    print(f"{'='*70}")
    
    print(f"\n📊 COMPARISON:")
    print(f"  Baseline SMA:    49 trades | 57.1% WR | +32.4%")
    print(f"  ML only:         53 trades | 47.2% WR | +7.1%")
    print(f"  ML + Natal:      {total_trades:2d} trades | {win_rate*100:4.1f}% WR | {total_return*100:+5.1f}%")
    
    if win_rate > 0.50 and total_return > 0.10:
        print(f"\n✅ SUCCESS! Better than random!")
    else:
        print(f"\n⚠️  Still needs improvement")

if __name__ == "__main__":
    run_backtest()
