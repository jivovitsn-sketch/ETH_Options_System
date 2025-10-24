#!/usr/bin/env python3
"""
TEST ENSEMBLE V2 (ML + ASTRO)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from ml.ensemble_v2 import EnsembleV2

def run_backtest(timeframe: str, hold_periods: int):
    """Run backtest with Ensemble V2"""
    
    print(f"\n{'='*70}")
    print(f"📊 ENSEMBLE V2 TEST: {timeframe} (hold {hold_periods} periods)")
    print(f"{'='*70}")
    
    # Load Ensemble
    ensemble = EnsembleV2(ml_weight=0.60, astro_weight=0.40)
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
    
    # Resample
    df.set_index('timestamp', inplace=True)
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'turnover': 'sum'
    }).dropna()
    resampled.reset_index(inplace=True)
    
    print(f"✅ {len(resampled)} {timeframe} candles")
    
    # Trading
    initial_capital = 10000
    capital = initial_capital
    position = None
    trades = []
    
    signals = 0
    
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
                prediction = ensemble.predict(window, current_date)
                
                if prediction['prediction'] != 'NEUTRAL' and prediction['confidence'] > 0.55:
                    position = {
                        'entry_idx': i,
                        'entry_price': current_price,
                        'direction': prediction['prediction'],
                        'size': capital * 0.05
                    }
                    signals += 1
            except Exception as e:
                pass
    
    # Results
    if not trades:
        print(f"❌ No trades")
        return None
    
    trades_df = pd.DataFrame(trades)
    
    total_trades = len(trades_df)
    winning = len(trades_df[trades_df['pnl_dollars'] > 0])
    win_rate = winning / total_trades
    
    final_capital = trades_df.iloc[-1]['capital']
    total_return = (final_capital - initial_capital) / initial_capital
    
    print(f"\n📈 RESULTS:")
    print(f"   Trades: {total_trades}")
    print(f"   Win Rate: {win_rate*100:.1f}%")
    print(f"   Return: {total_return*100:.1f}%")
    print(f"   Final Capital: ${final_capital:,.0f}")
    
    return {
        'timeframe': timeframe,
        'trades': total_trades,
        'win_rate': win_rate,
        'return': total_return,
        'final_capital': final_capital
    }

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════╗")
    print("║       ENSEMBLE V2 TEST (ML + ASTRO)          ║")
    print("╚════════════════════════════════════════════════╝")
    
    results = []
    
    # Test timeframes
    results.append(run_backtest('1h', hold_periods=24))
    results.append(run_backtest('4h', hold_periods=18))
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY")
    print(f"{'='*70}")
    
    for r in results:
        if r:
            print(f"{r['timeframe']:5s} | Trades: {r['trades']:3d} | WR: {r['win_rate']*100:5.1f}% | Return: {r['return']*100:6.1f}%")
    
    # Compare with baseline
    print(f"\n📊 COMPARISON:")
    print(f"  Baseline SMA:     49 trades | 57.1% WR | +32.4%")
    print(f"  ML only:          53 trades | 47.2% WR | +7.1%")
    if results[0]:
        print(f"  ML + Astro (1H):  {results[0]['trades']:2d} trades | {results[0]['win_rate']*100:4.1f}% WR | {results[0]['return']*100:+5.1f}%")
