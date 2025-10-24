#!/usr/bin/env python3
"""PATTERN AGENT - Технические паттерны"""

import pandas as pd
import numpy as np

class PatternAgent:
    def __init__(self):
        print("✅ Pattern Agent initialized")
    
    def analyze(self, df: pd.DataFrame):
        if len(df) < 5:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5, 'patterns_detected': []}
        
        # Простой RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        last_rsi = rsi.iloc[-1]
        
        if last_rsi < 30:
            return {'prediction': 'BULLISH', 'confidence': 0.65, 'patterns_detected': ['oversold']}
        elif last_rsi > 70:
            return {'prediction': 'BEARISH', 'confidence': 0.65, 'patterns_detected': ['overbought']}
        else:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5, 'patterns_detected': []}

if __name__ == "__main__":
    print("Pattern Agent ready")
