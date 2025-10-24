#!/usr/bin/env python3
"""VWAP"""
import pandas as pd

class VWAP:
    def __init__(self):
        print("✅ VWAP initialized")
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP"""
        df = df.copy()
        
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['tp_volume'] = df['typical_price'] * df['volume']
        
        df['vwap'] = df['tp_volume'].cumsum() / df['volume'].cumsum()
        
        return df
