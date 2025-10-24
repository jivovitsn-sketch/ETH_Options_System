#!/usr/bin/env python3
"""Analyze real options data"""
import pandas as pd
from pathlib import Path

# Load
options_dir = Path('data/options/BTC')
latest = sorted(options_dir.glob("*.csv"))[-1]

df = pd.read_csv(latest)

print("\n" + "="*70)
print("REAL OPTIONS DATA STRUCTURE")
print("="*70)
print(f"\nTotal instruments: {len(df)}")
print(f"\nColumns: {list(df.columns)}")
print(f"\nSample data:")
print(df.head(20))

print(f"\n\nGreeks structure:")
print(df['greeks'].iloc[0])

print(f"\n\nExpiration dates:")
expirations = pd.to_datetime(df['expiration'], unit='ms')
print(expirations.value_counts().head(10))

print(f"\n\nUnderlying price: ${df['underlying_price'].iloc[0]:,.2f}")

# Calls vs Puts
print(f"\n\nCalls: {len(df[df['option_type']=='call'])}")
print(f"Puts: {len(df[df['option_type']=='put'])}")

# OI distribution
print(f"\n\nTop OI strikes:")
top_oi = df.nlargest(10, 'open_interest')[['instrument', 'strike', 'option_type', 'open_interest']]
print(top_oi)
