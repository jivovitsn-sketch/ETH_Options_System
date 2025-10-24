#!/usr/bin/env python3
"""EMA"""
import pandas as pd

class EMA:
    def __init__(self, periods: list = [9, 21, 50, 200]):
        self.periods = periods
        print(f"✅ EMA initialized (periods={periods})")
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        for p in self.periods:
            df[f'ema{p}'] = df['close'].ewm(span=p).mean()
        
        # Crossovers
        if 9 in self.periods and 21 in self.periods:
            df['ema_bullish'] = (df['ema9'] > df['ema21']) & (df['ema9'].shift(1) <= df['ema21'].shift(1))
            df['ema_bearish'] = (df['ema9'] < df['ema21']) & (df['ema9'].shift(1) >= df['ema21'].shift(1))
        
        return df
