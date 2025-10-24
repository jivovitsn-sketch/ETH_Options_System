#!/usr/bin/env python3
"""Analyze collected options"""
import pandas as pd
from pathlib import Path

# Load
latest = sorted(Path('data/options_history/BTC').glob("*.csv"))[-1]
df = pd.read_csv(latest)

print("\n" + "="*70)
print("СОБРАННЫЕ ОПЦИОННЫЕ ДАННЫЕ")
print("="*70)

print(f"\nАКТИВ: BTC")
print(f"Spot Price: ${df['underlying_price'].iloc[0]:,.2f}")
print(f"\nВСЕГО ОПЦИОНОВ: {len(df)}")

# Calls vs Puts
calls = len(df[df['option_type'] == 'call'])
puts = len(df[df['option_type'] == 'put'])
print(f"\nCalls: {calls}")
print(f"Puts:  {puts}")

# Expirations
df['expiration_date'] = pd.to_datetime(df['expiration'], unit='ms')
df['dte'] = (df['expiration_date'] - pd.Timestamp.now()).dt.days

print(f"\nЭКСПИРАЦИИ (DTE):")
exp_counts = df.groupby('dte').size().sort_index()
for dte, count in exp_counts.items():
    print(f"  {dte} дней: {count} опционов")

# Strikes
print(f"\nСТРАЙКИ:")
print(f"  Min: ${df['strike'].min():,.0f}")
print(f"  Max: ${df['strike'].max():,.0f}")
print(f"  Unique: {df['strike'].nunique()}")

# Open Interest
print(f"\nOPEN INTEREST:")
print(f"  Total: {df['oi'].sum():,.1f} BTC")
print(f"  Calls: {df[df['option_type']=='call']['oi'].sum():,.1f} BTC")
print(f"  Puts:  {df[df['option_type']=='put']['oi'].sum():,.1f} BTC")

# ВОЗМОЖНЫЕ КОНСТРУКЦИИ
print("\n" + "="*70)
print("ВОЗМОЖНЫЕ КОНСТРУКЦИИ (из этих опционов):")
print("="*70)

# Для каждой экспирации
for dte in sorted(df['dte'].unique()):
    exp_df = df[df['dte'] == dte]
    strikes = exp_df['strike'].nunique()
    
    # Bull Call Spreads = (strikes-1) для calls
    bull_calls = strikes - 1
    
    # Bear Put Spreads = (strikes-1) для puts
    bear_puts = strikes - 1
    
    # Iron Condors = комбинации call spread + put spread
    iron_condors = (strikes - 2) * (strikes - 2) if strikes > 2 else 0
    
    # Straddles = по одному на каждый страйк
    straddles = strikes
    
    # Butterflies = (strikes-2) для каждого типа
    butterflies = (strikes - 2) * 2 if strikes > 2 else 0
    
    total = bull_calls + bear_puts + iron_condors + straddles + butterflies
    
    print(f"\nDTE {dte} дней ({strikes} страйков):")
    print(f"  Bull Call Spreads:    {bull_calls:,}")
    print(f"  Bear Put Spreads:     {bear_puts:,}")
    print(f"  Iron Condors:         {iron_condors:,}")
    print(f"  Straddles:            {straddles:,}")
    print(f"  Butterflies:          {butterflies:,}")
    print(f"  ВСЕГО возможных:      {total:,}")

print("\n" + "="*70)
print(f"ИТОГО: Из {len(df)} опционов можно построить")
print(f"       ТЫСЯЧИ возможных конструкций!")
print("="*70)
