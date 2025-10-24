#!/usr/bin/env python3
"""
LIQUIDITY ZONES
Зоны скопления стоп-лоссов
"""

import pandas as pd
import numpy as np

class LiquidityZones:
    """
    Liquidity Zones - где скапливаются стопы
    Обычно за swing highs/lows
    """
    
    def __init__(self, swing_length: int = 5, zone_buffer: float = 0.001):
        self.swing_length = swing_length
        self.zone_buffer = zone_buffer  # 0.1% буфер
        print(f"✅ Liquidity Zones initialized")
    
    def find_liquidity_zones(self, df: pd.DataFrame) -> dict:
        """
        Найти зоны ликвидности
        """
        highs = []
        lows = []
        
        # Найти swing points
        for i in range(self.swing_length, len(df) - self.swing_length):
            # Swing High
            is_high = True
            for j in range(1, self.swing_length + 1):
                if df.iloc[i]['high'] <= df.iloc[i-j]['high'] or \
                   df.iloc[i]['high'] <= df.iloc[i+j]['high']:
                    is_high = False
                    break
            
            if is_high:
                highs.append(df.iloc[i]['high'])
            
            # Swing Low
            is_low = True
            for j in range(1, self.swing_length + 1):
                if df.iloc[i]['low'] >= df.iloc[i-j]['low'] or \
                   df.iloc[i]['low'] >= df.iloc[i+j]['low']:
                    is_low = False
                    break
            
            if is_low:
                lows.append(df.iloc[i]['low'])
        
        current_price = df['close'].iloc[-1]
        
        # Зоны ликвидности = за swing points
        liquidity_above = []
        liquidity_below = []
        
        for high in highs[-10:]:  # Последние 10
            if high > current_price:
                liquidity_above.append({
                    'price': high,
                    'zone_low': high * (1 - self.zone_buffer),
                    'zone_high': high * (1 + self.zone_buffer),
                    'distance': (high - current_price) / current_price
                })
        
        for low in lows[-10:]:
            if low < current_price:
                liquidity_below.append({
                    'price': low,
                    'zone_low': low * (1 - self.zone_buffer),
                    'zone_high': low * (1 + self.zone_buffer),
                    'distance': (current_price - low) / current_price
                })
        
        return {
            'above': sorted(liquidity_above, key=lambda x: x['distance']),
            'below': sorted(liquidity_below, key=lambda x: x['distance'])
        }
    
    def get_nearest_liquidity(self, df: pd.DataFrame) -> dict:
        """
        Найти ближайшие зоны ликвидности
        """
        zones = self.find_liquidity_zones(df)
        
        nearest_above = zones['above'][0] if zones['above'] else None
        nearest_below = zones['below'][0] if zones['below'] else None
        
        return {
            'nearest_above': nearest_above,
            'nearest_below': nearest_below
        }

if __name__ == "__main__":
    print("Liquidity Zones module ready")
