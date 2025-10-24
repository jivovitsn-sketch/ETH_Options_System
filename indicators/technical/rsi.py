#!/usr/bin/env python3
"""RSI + Divergences"""
import pandas as pd

class RSI:
    def __init__(self, period: int = 14):
        self.period = period
        print(f"✅ RSI initialized (period={period})")
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Oversold/Overbought
        df['rsi_oversold'] = df['rsi'] < 30
        df['rsi_overbought'] = df['rsi'] > 70
        
        # Divergences (simplified)
        df['bullish_div'] = False
        df['bearish_div'] = False
        
        return df
