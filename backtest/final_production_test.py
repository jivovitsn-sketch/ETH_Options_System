#!/usr/bin/env python3
"""PRODUCTION TEST - ALL DATA (2040 days)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from indicators.smart_money.order_blocks import OrderBlocks
from strategies.options.all_spreads import AllOptionStrategies

print("╔════════════════════════════════════════════════╗")
print("║   PRODUCTION TEST - ALL DATA (2040 DAYS)      ║")
print("╚════════════════════════════════════════════════╝")

# Load ALL data
data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
files = sorted(data_dir.glob("*.csv"))

print(f"\n✅ Found {len(files)} days of data")

dfs = [pd.read_csv(f) for f in files]
df = pd.concat(dfs, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# Resample to 4H
resampled = df.resample('4h').agg({
    'open': 'first', 'high': 'max', 'low': 'min',
    'close': 'last', 'volume': 'sum'
}).dropna()
resampled.reset_index(inplace=True)

print(f"✅ Resampled to {len(resampled)} candles (4H)")

# Order Blocks + Bear Put
ob = OrderBlocks()
options = AllOptionStrategies()

df_ob = ob.find_order_blocks(resampled)

trades = []
position = None
capital = 10000
initial = 10000

for i in range(100, len(df_ob) - 18):
    price = df_ob.iloc[i]['close']
    
    # Close
    if position and (i - position['entry_idx']) >= 18:
        pnl = options.calculate_pnl(position['strategy'], price)
        capital += pnl
        trades.append({'pnl': pnl, 'capital': capital})
        position = None
    
    # Open - только Bearish Order Blocks
    if position is None and df_ob.iloc[i]['bearish_ob']:
        risk = capital * 0.05
        strategy = options.bear_put_spread(price, risk)
        position = {'entry_idx': i, 'strategy': strategy}

# Results
if trades:
    tdf = pd.DataFrame(trades)
    wins = len(tdf[tdf['pnl'] > 0])
    wr = wins / len(tdf)
    final = tdf.iloc[-1]['capital']
    ret = (final - initial) / initial
    
    print(f"\n{'='*70}")
    print(f"📊 PRODUCTION RESULTS (Order Blocks + Bear Put)")
    print(f"{'='*70}")
    print(f"Period:        2020-03-25 to 2025-09-28 (2040 days)")
    print(f"Timeframe:     4H")
    print(f"Hold Period:   3 days (18 candles)")
    print(f"")
    print(f"Total Trades:  {len(tdf)}")
    print(f"Win Rate:      {wr*100:.1f}%")
    print(f"Total Return:  {ret*100:.1f}%")
    print(f"Initial:       ${initial:,.0f}")
    print(f"Final:         ${final:,.0f}")
    print(f"Profit:        ${final-initial:,.0f}")
    print(f"{'='*70}")
    
    # Save
    tdf.to_csv('production_trades.csv', index=False)
    print(f"\n💾 Saved to production_trades.csv")
else:
    print("❌ No trades")
