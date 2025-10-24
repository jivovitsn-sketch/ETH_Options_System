#!/usr/bin/env python3
"""
EPHEMERIS CALCULATOR
Позиции планет без PyEphem (встроенная астрономия)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class EphemerisCalculator:
    """
    Упрощённый расчёт позиций планет
    Используем приближённые орбиты
    """
    
    def __init__(self):
        # Орбитальные периоды (дней)
        self.periods = {
            'sun': 365.25,
            'moon': 27.32,
            'mercury': 87.97,
            'venus': 224.70,
            'mars': 686.98,
            'jupiter': 4332.59,
            'saturn': 10759.22
        }
        
        # Начальные позиции (градусы на 2020-01-01)
        self.epoch_positions = {
            'sun': 280.0,
            'moon': 150.0,
            'mercury': 250.0,
            'venus': 290.0,
            'mars': 200.0,
            'jupiter': 280.0,
            'saturn': 290.0
        }
        
        self.epoch = datetime(2020, 1, 1)
        
        print("✅ Ephemeris Calculator initialized")
    
    def calculate_position(self, planet: str, date: datetime) -> float:
        """
        Рассчитать позицию планеты в градусах (0-360)
        """
        if planet not in self.periods:
            return 0.0
        
        # Дней с эпохи
        days = (date - self.epoch).total_seconds() / 86400
        
        # Пройденных циклов
        cycles = days / self.periods[planet]
        
        # Текущая позиция
        position = (self.epoch_positions[planet] + cycles * 360) % 360
        
        return position
    
    def get_all_positions(self, date: datetime) -> Dict[str, float]:
        """
        Получить позиции всех планет
        """
        positions = {}
        
        for planet in self.periods.keys():
            positions[planet] = self.calculate_position(planet, date)
        
        return positions
    
    def get_moon_phase(self, date: datetime) -> str:
        """
        Фаза Луны
        """
        sun_pos = self.calculate_position('sun', date)
        moon_pos = self.calculate_position('moon', date)
        
        # Угол между Солнцем и Луной
        angle = (moon_pos - sun_pos) % 360
        
        if angle < 45:
            return 'new_moon'
        elif angle < 90:
            return 'waxing_crescent'
        elif angle < 135:
            return 'first_quarter'
        elif angle < 180:
            return 'waxing_gibbous'
        elif angle < 225:
            return 'full_moon'
        elif angle < 270:
            return 'waning_gibbous'
        elif angle < 315:
            return 'last_quarter'
        else:
            return 'waning_crescent'

if __name__ == "__main__":
    calc = EphemerisCalculator()
    
    # Test
    today = datetime.now()
    positions = calc.get_all_positions(today)
    
    print(f"\nPositions for {today.date()}:")
    for planet, pos in positions.items():
        print(f"  {planet:10s}: {pos:6.2f}°")
    
    print(f"\nMoon phase: {calc.get_moon_phase(today)}")
