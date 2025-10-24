#!/usr/bin/env python3
"""Test NEW ML models"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from ml.ensemble_combiner import EnsembleCombiner

print("="*70)
print("TESTING NEW ML MODELS")
print("="*70)

# Initialize
ensemble = EnsembleCombiner()

# Load NEW models
model_path = Path(__file__).parent.parent / 'ml_agent_models_new.pkl'
if model_path.exists():
    ensemble.load_ml_models(str(model_path))
else:
    print("❌ No new models found")
    sys.exit(1)

# Load data
data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
files = sorted(data_dir.glob("*.csv"))[-30:]

dfs = []
for file in files:
    df = pd.read_csv(file)
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp')

print(f"\n✅ Loaded {len(df)} candles")

# Test 10 predictions
print(f"\n{'='*70}")
print("PREDICTIONS:")
print(f"{'='*70}")

signals_found = 0
window_size = 100
step = 50

for i in range(10):
    start = i * step
    end = start + window_size
    
    if end >= len(df):
        break
    
    window = df.iloc[start:end].copy()
    
    context = {
        'trend': 'NEUTRAL',
        'astro_direction_str': 'NEUTRAL'
    }
    
    result = ensemble.predict(window, context)
    
    price_start = window['close'].iloc[0]
    price_end = window['close'].iloc[-1]
    price_change = (price_end - price_start) / price_start
    
    print(f"\nTest {i+1}:")
    print(f"  Price: ${price_start:.0f} → ${price_end:.0f} ({price_change:+.2%})")
    print(f"  Signal: {result['prediction']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    
    if result['prediction'] != 'NEUTRAL' and result['confidence'] > 0.50:
        print(f"  ✅ TRADEABLE!")
        signals_found += 1

print(f"\n{'='*70}")
print(f"📊 Signals found: {signals_found}/10")
print(f"{'='*70}")
