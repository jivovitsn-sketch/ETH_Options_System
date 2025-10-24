#!/usr/bin/env python3
"""
GANN ANGLES
Time = Price концепция
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class GannAngles:
    """
    Gann Angles: 1x1 (45°), 1x2, 2x1, etc.
    """
    
    def __init__(self):
        # Углы Ганна в градусах
        self.angles = {
            '1x8': 7.5,    # очень пологий
            '1x4': 15,
            '1x3': 18.75,
            '1x2': 26.25,
            '1x1': 45,     # главный угол (время = цена)
            '2x1': 63.75,
            '3x1': 71.25,
            '4x1': 75,
            '8x1': 82.5    # очень крутой
        }
        
        print("✅ Gann Angles initialized")
    
    def calculate_gann_line(self, start_price: float, start_time: datetime, 
                           angle_name: str, periods: int) -> list:
        """
        Рассчитать линию Ганна
        
        angle_name: '1x1', '1x2', etc.
        periods: количество периодов вперёд
        """
        if angle_name not in self.angles:
            return []
        
        angle_deg = self.angles[angle_name]
        angle_rad = np.radians(angle_deg)
        
        # Slope (наклон)
        slope = np.tan(angle_rad)
        
        points = []
        for i in range(periods):
            price = start_price + (slope * i)
            points.append({
                'period': i,
                'price': price,
                'time': start_time + timedelta(hours=i)
            })
        
        return points
    
    def find_gann_support_resistance(self, df: pd.DataFrame, 
                                     pivot_price: float, pivot_time: datetime) -> dict:
        """
        Найти уровни поддержки/сопротивления по Ганну
        """
        current_time = df['timestamp'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        periods_elapsed = len(df)
        
        levels = {}
        
        for angle_name in ['1x1', '1x2', '2x1']:
            line = self.calculate_gann_line(pivot_price, pivot_time, 
                                           angle_name, periods_elapsed)
            
            if line:
                current_level = line[-1]['price']
                
                # Определяем Support или Resistance
                if current_level < current_price:
                    levels[f'{angle_name}_support'] = current_level
                else:
                    levels[f'{angle_name}_resistance'] = current_level
        
        return levels

if __name__ == "__main__":
    print("Gann Angles module ready")
