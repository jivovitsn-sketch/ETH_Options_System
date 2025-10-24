#!/usr/bin/env python3
"""TEST: Проверяем что возвращает Ensemble"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from ml.ensemble_combiner import EnsembleCombiner

print("Loading Ensemble...")
ensemble = EnsembleCombiner()

# Load ML models
model_path = Path(__file__).parent.parent / 'ml_agent_models_multi.pkl'
if model_path.exists():
    ensemble.load_ml_models(str(model_path))

# Load data - БОЛЬШЕ ДНЕЙ!
data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
files = sorted(data_dir.glob("*.csv"))[-30:]  # Last 30 days

dfs = []
for file in files:
    df = pd.read_csv(file)
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp')

print(f"\n✅ Loaded {len(df)} candles")
print(f"   Time range: {df['timestamp'].min()} → {df['timestamp'].max()}")

# Test 10 predictions - МЕНЬШИЕ ОКНА
print(f"\n{'='*70}")
print("TESTING 10 PREDICTIONS:")
print(f"{'='*70}")

window_size = 50
step = 20

for i in range(10):
    start = i * step
    end = start + window_size
    
    if end >= len(df):
        break
    
    window = df.iloc[start:end].copy()
    
    context = {
        'trend': 'NEUTRAL',
        'astro_direction_str': 'NEUTRAL',
        'oi_pcr': 1.0,
        'iv': 0.5
    }
    
    result = ensemble.predict(window, context)
    
    price_start = window['close'].iloc[0]
    price_end = window['close'].iloc[-1]
    price_change = (price_end - price_start) / price_start
    
    print(f"\nTest {i+1} (candles {start}-{end}):")
    print(f"  Price: ${price_start:.0f} → ${price_end:.0f} ({price_change:+.2%})")
    print(f"  Signal: {result['prediction']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Consensus: {result['consensus']}")
    
    if result['prediction'] != 'NEUTRAL' and result['confidence'] > 0.50:
        print(f"  ✅ TRADEABLE SIGNAL!")

print(f"\n{'='*70}")
