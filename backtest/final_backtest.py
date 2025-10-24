#!/usr/bin/env python3
"""
FINAL BACKTEST - New ML models + SMA Fallback
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from ml.ensemble_combiner import EnsembleCombiner

print("╔════════════════════════════════════════════════╗")
print("║       FINAL BACKTEST WITH NEW MODELS          ║")
print("╚════════════════════════════════════════════════╝")

# Initialize Ensemble
ensemble = EnsembleCombiner()

# Load NEW models
model_path = Path(__file__).parent.parent / 'ml_agent_models_new.pkl'
if model_path.exists():
    ensemble.load_ml_models(str(model_path))
    print("✅ NEW ML models loaded")
else:
    print("⚠️  Using old models")
    ensemble.load_ml_models('ml_agent_models_multi.pkl')

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

print(f"✅ Loaded {len(df)} candles")

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

# Calculate indicators
hourly['sma20'] = hourly['close'].rolling(20).mean()
hourly['sma50'] = hourly['close'].rolling(50).mean()

print(f"📊 Hourly candles: {len(hourly)}")

# Trading
initial_capital = 10000
capital = initial_capital
position = None
trades = []

ml_signals = 0
sma_signals = 0

print(f"\n🚀 Starting backtest...")

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
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'direction': position['direction'],
            'pnl_pct': pnl_pct,
            'pnl_dollars': pnl_dollars,
            'capital': capital,
            'source': position['source']
        })
        
        position = None
    
    # Open new position
    if position is None:
        signal = None
        source = None
        
        # Try ML first
        try:
            window = hourly.iloc[max(0, i-100):i].copy()
            context = {'trend': 'NEUTRAL', 'astro_direction_str': 'NEUTRAL'}
            
            prediction = ensemble.predict(window, context)
            
            # VERY aggressive threshold
            if prediction['prediction'] != 'NEUTRAL' and prediction['confidence'] > 0.40:
                signal = prediction['prediction']
                source = 'ML'
                ml_signals += 1
        except:
            pass
        
        # Fallback to SMA
        if signal is None and pd.notna(sma20) and pd.notna(sma50):
            if current_price > sma20 > sma50:
                signal = 'BULLISH'
                source = 'SMA'
                sma_signals += 1
            elif current_price < sma20 < sma50:
                signal = 'BEARISH'
                source = 'SMA'
                sma_signals += 1
        
        if signal:
            position = {
                'entry_idx': i,
                'entry_price': current_price,
                'direction': signal,
                'size': capital * 0.05,
                'source': source
            }

# Results
print(f"\n{'='*70}")
print(f"📊 FINAL BACKTEST RESULTS")
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
    
    ml_trades = len(trades_df[trades_df['source'] == 'ML'])
    sma_trades = len(trades_df[trades_df['source'] == 'SMA'])
    
    print(f"Initial Capital:    ${initial_capital:,.2f}")
    print(f"Final Capital:      ${final_capital:,.2f}")
    print(f"Total P&L:          ${total_pnl:,.2f}")
    print(f"Total Return:       {total_return*100:.2f}%")
    print(f"\nTotal Trades:       {total_trades}")
    print(f"  ML (NEW models):  {ml_trades}")
    print(f"  SMA Fallback:     {sma_trades}")
    print(f"\nWinning Trades:     {winning}")
    print(f"Losing Trades:      {losing}")
    print(f"Win Rate:           {win_rate*100:.2f}%")
    print(f"{'='*70}")
    
    # Save
    trades_df.to_csv('final_trades.csv', index=False)
    print(f"\n💾 Saved to final_trades.csv")

print(f"\n🎯 ML Signals attempted: {ml_signals}")
print(f"🎯 SMA Fallback used: {sma_signals}")
