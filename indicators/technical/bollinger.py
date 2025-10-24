#!/usr/bin/env python3
"""Bollinger Bands"""
import pandas as pd

class BollingerBands:
    def __init__(self, period: int = 20, std: float = 2.0):
        self.period = period
        self.std = std
        print(f"✅ Bollinger Bands initialized (period={period}, std={std})")
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df = df.copy()
        
        df['bb_middle'] = df['close'].rolling(window=self.period).mean()
        df['bb_std'] = df['close'].rolling(window=self.period).std()
        
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * self.std)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * self.std)
        
        # Squeeze detection (low volatility)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(100).quantile(0.25)
        
        return df
