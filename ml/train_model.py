#!/usr/bin/env python3
"""ML MODEL - обучение и тест"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

print("\n" + "="*80)
print("ML MODEL TRAINING")
print("="*80)

# Load data
data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'ETHUSDT'
files = sorted(data_dir.glob("*.csv"))

dfs = [pd.read_csv(f) for f in files]
df = pd.concat(dfs, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

df = df.resample('4h').agg({
    'open': 'first', 'high': 'max', 'low': 'min',
    'close': 'last', 'volume': 'sum'
}).dropna()

print(f"\nData: {len(df)} candles")

# Features
df['returns'] = df['close'].pct_change()
df['sma20'] = df['close'].rolling(20).mean()
df['sma50'] = df['close'].rolling(50).mean()
df['rsi'] = 100 - (100 / (1 + df['returns'].rolling(14).apply(lambda x: x[x>0].sum() / abs(x[x<0].sum()), raw=True)))
df['volume_ma'] = df['volume'].rolling(20).mean()

# Target: будет ли +5% в следующие 18 периодов
df['future_return'] = df['close'].shift(-18).pct_change(18)
df['target'] = (df['future_return'] > 0.05).astype(int)

# Remove NaN
df = df.dropna()

# Train/test split
X = df[['returns', 'sma20', 'sma50', 'rsi', 'volume', 'volume_ma']].values
y = df['target'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)

print(f"\nTrain: {len(X_train)} samples")
print(f"Test:  {len(X_test)} samples")

# Train
print("\nTraining Random Forest...")
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# Test
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)

print(f"\nTrain Accuracy: {train_score*100:.1f}%")
print(f"Test Accuracy:  {test_score*100:.1f}%")

# Save
model_dir = Path(__file__).parent / 'models'
model_dir.mkdir(exist_ok=True)

model_path = model_dir / 'rf_eth_model.pkl'
joblib.dump(model, model_path)

print(f"\n✅ Model saved to {model_path}")

# Feature importance
importance = pd.DataFrame({
    'feature': ['returns', 'sma20', 'sma50', 'rsi', 'volume', 'volume_ma'],
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(importance)
