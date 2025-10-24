#!/usr/bin/env python3
"""
ASPECTS CALCULATOR
11 типов аспектов с финансовой интерпретацией
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from datetime import datetime
from typing import Dict, List, Tuple

from core.ephemeris_calculator import EphemerisCalculator

class AspectsCalculator:
    """
    Расчёт аспектов между планетами
    """
    
    def __init__(self):
        # Load config
        config_path = Path(__file__).parent.parent / 'configs' / 'astro.yaml'
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.ephemeris = EphemerisCalculator()
        
        # Aspect definitions
        self.aspects = {
            'conjunction': {'angle': 0, 'orb': 10, 'nature': 'neutral'},
            'sextile': {'angle': 60, 'orb': 6, 'nature': 'positive'},
            'square': {'angle': 90, 'orb': 10, 'nature': 'negative'},
            'trine': {'angle': 120, 'orb': 10, 'nature': 'positive'},
            'opposition': {'angle': 180, 'orb': 10, 'nature': 'negative'},
            'semisextile': {'angle': 30, 'orb': 3, 'nature': 'minor'},
            'semisquare': {'angle': 45, 'orb': 3, 'nature': 'minor'},
            'sesquisquare': {'angle': 135, 'orb': 3, 'nature': 'minor'},
            'quincunx': {'angle': 150, 'orb': 3, 'nature': 'minor'},
            'quintile': {'angle': 72, 'orb': 2, 'nature': 'creative'},
            'biquintile': {'angle': 144, 'orb': 2, 'nature': 'creative'}
        }
        
        # Financial interpretation
        self.financial_impact = {
            'conjunction': {'volatility': 1.5, 'trend': 0},
            'sextile': {'volatility': 0.8, 'trend': 0.3},
            'square': {'volatility': 1.8, 'trend': -0.2},
            'trine': {'volatility': 0.7, 'trend': 0.5},
            'opposition': {'volatility': 2.0, 'trend': 0}
        }
        
        print("✅ Aspects Calculator initialized")
    
    def calculate_angle(self, pos1: float, pos2: float) -> float:
        """
        Угол между двумя позициями
        """
        diff = abs(pos1 - pos2)
        if diff > 180:
            diff = 360 - diff
        return diff
    
    def find_aspect(self, angle: float) -> Tuple[str, float]:
        """
        Найти аспект по углу
        Returns: (aspect_name, strength)
        """
        for name, props in self.aspects.items():
            target_angle = props['angle']
            orb = props['orb']
            
            diff = abs(angle - target_angle)
            
            if diff <= orb:
                # Strength: 1.0 at exact, 0.0 at orb limit
                strength = 1.0 - (diff / orb)
                return name, strength
        
        return None, 0.0
    
    def get_all_aspects(self, date: datetime) -> List[Dict]:
        """
        Найти все аспекты на дату
        """
        # Get positions
        positions = self.ephemeris.get_all_positions(date)
        
        aspects_found = []
        planets = list(positions.keys())
        
        # Check all pairs
        for i, planet1 in enumerate(planets):
            for planet2 in planets[i+1:]:
                pos1 = positions[planet1]
                pos2 = positions[planet2]
                
                angle = self.calculate_angle(pos1, pos2)
                aspect_name, strength = self.find_aspect(angle)
                
                if aspect_name and strength > 0.5:  # Only strong aspects
                    aspects_found.append({
                        'planet1': planet1,
                        'planet2': planet2,
                        'aspect': aspect_name,
                        'strength': strength,
                        'angle': angle,
                        'nature': self.aspects[aspect_name]['nature']
                    })
        
        return aspects_found
    
    def get_market_direction(self, date: datetime) -> Dict:
        """
        Финансовая интерпретация аспектов
        """
        aspects = self.get_all_aspects(date)
        
        if not aspects:
            return {
                'direction': 'NEUTRAL',
                'strength': 0.5,
                'volatility': 1.0
            }
        
        # Aggregate
        total_trend = 0
        total_volatility = 0
        count = 0
        
        for asp in aspects:
            aspect_name = asp['aspect']
            strength = asp['strength']
            
            if aspect_name in self.financial_impact:
                impact = self.financial_impact[aspect_name]
                total_trend += impact['trend'] * strength
                total_volatility += impact['volatility'] * strength
                count += 1
        
        if count == 0:
            return {
                'direction': 'NEUTRAL',
                'strength': 0.5,
                'volatility': 1.0
            }
        
        avg_trend = total_trend / count
        avg_volatility = total_volatility / count
        
        # Direction
        if avg_trend > 0.2:
            direction = 'BULLISH'
            confidence = min(0.5 + avg_trend * 0.3, 0.8)
        elif avg_trend < -0.2:
            direction = 'BEARISH'
            confidence = min(0.5 + abs(avg_trend) * 0.3, 0.8)
        else:
            direction = 'NEUTRAL'
            confidence = 0.5
        
        return {
            'direction': direction,
            'strength': confidence,
            'volatility': avg_volatility,
            'aspects_count': len(aspects)
        }

if __name__ == "__main__":
    calc = AspectsCalculator()
    
    # Test
    today = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"ASPECTS for {today.date()}")
    print(f"{'='*60}")
    
    aspects = calc.get_all_aspects(today)
    
    print(f"\nFound {len(aspects)} aspects:")
    for asp in aspects[:10]:  # Top 10
        print(f"  {asp['planet1']:10s} {asp['aspect']:15s} {asp['planet2']:10s} | {asp['strength']:.2f}")
    
    # Market direction
    market = calc.get_market_direction(today)
    print(f"\n{'='*60}")
    print(f"MARKET DIRECTION:")
    print(f"  Direction: {market['direction']}")
    print(f"  Strength: {market['strength']:.2%}")
    print(f"  Volatility: {market['volatility']:.2f}x")
    print(f"{'='*60}")
