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
        
        # RSI - БОЛЕЕ АГРЕССИВНЫЕ ПОРОГИ
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        last_rsi = rsi.iloc[-1]
        
        # RSI < 40 (было 30) = BULLISH
        if last_rsi < 40:
            return {'prediction': 'BULLISH', 'confidence': 0.70, 'patterns_detected': ['oversold']}
        # RSI > 60 (было 70) = BEARISH
        elif last_rsi > 60:
            return {'prediction': 'BEARISH', 'confidence': 0.70, 'patterns_detected': ['overbought']}
        # Momentum
        elif len(df) > 20:
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
            if price_change > 0.03:
                return {'prediction': 'BULLISH', 'confidence': 0.65, 'patterns_detected': ['uptrend']}
            elif price_change < -0.03:
                return {'prediction': 'BEARISH', 'confidence': 0.65, 'patterns_detected': ['downtrend']}
        
        return {'prediction': 'NEUTRAL', 'confidence': 0.5, 'patterns_detected': []}

if __name__ == "__main__":
    print("Pattern Agent ready")
