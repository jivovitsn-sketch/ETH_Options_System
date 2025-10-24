#!/usr/bin/env python3
"""
NATAL CHART CALCULATOR
Натальная карта актива (позиции планет на момент рождения)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from datetime import datetime
from typing import Dict

from core.ephemeris_calculator import EphemerisCalculator

class NatalChart:
    """
    Натальная карта актива
    """
    
    def __init__(self, birth_date: datetime, name: str = "Asset"):
        self.birth_date = birth_date
        self.name = name
        self.ephemeris = EphemerisCalculator()
        
        # Calculate natal positions
        self.natal_positions = self.ephemeris.get_all_positions(birth_date)
        
        print(f"✅ Natal Chart created for {name}")
        print(f"   Birth: {birth_date}")
    
    def get_transits(self, date: datetime) -> Dict:
        """
        Получить транзиты (текущие позиции VS натальные)
        """
        current_positions = self.ephemeris.get_all_positions(date)
        
        transits = {}
        
        for planet, natal_pos in self.natal_positions.items():
            current_pos = current_positions[planet]
            
            # Угол между транзитной и натальной позицией
            diff = abs(current_pos - natal_pos)
            if diff > 180:
                diff = 360 - diff
            
            transits[planet] = {
                'natal': natal_pos,
                'current': current_pos,
                'angle': diff
            }
        
        return transits
    
    def find_natal_aspects(self, date: datetime) -> list:
        """
        Найти аспекты транзитных планет к натальным позициям
        """
        transits = self.get_transits(date)
        
        aspects_def = {
            'conjunction': {'angle': 0, 'orb': 10},
            'sextile': {'angle': 60, 'orb': 6},
            'square': {'angle': 90, 'orb': 10},
            'trine': {'angle': 120, 'orb': 10},
            'opposition': {'angle': 180, 'orb': 10}
        }
        
        natal_aspects = []
        
        for planet, transit in transits.items():
            angle = transit['angle']
            
            for aspect_name, aspect_def in aspects_def.items():
                target = aspect_def['angle']
                orb = aspect_def['orb']
                
                diff = abs(angle - target)
                
                if diff <= orb:
                    strength = 1.0 - (diff / orb)
                    
                    natal_aspects.append({
                        'planet': planet,
                        'aspect': aspect_name,
                        'strength': strength,
                        'angle': angle
                    })
        
        return natal_aspects
    
    def get_financial_signal(self, date: datetime) -> Dict:
        """
        Финансовая интерпретация транзитов
        """
        aspects = self.find_natal_aspects(date)
        
        if not aspects:
            return {
                'direction': 'NEUTRAL',
                'confidence': 0.5,
                'aspects_count': 0
            }
        
        # Финансовые интерпретации
        financial_impact = {
            'conjunction': {'trend': 0.3, 'weight': 1.5},
            'sextile': {'trend': 0.4, 'weight': 1.0},
            'square': {'trend': -0.3, 'weight': 1.2},
            'trine': {'trend': 0.5, 'weight': 1.3},
            'opposition': {'trend': -0.2, 'weight': 1.1}
        }
        
        # Веса планет
        planet_weights = {
            'sun': 1.5,
            'moon': 1.2,
            'mercury': 1.0,
            'venus': 1.1,
            'mars': 1.3,
            'jupiter': 1.4,
            'saturn': 1.2
        }
        
        total_trend = 0
        total_weight = 0
        
        for asp in aspects:
            if asp['strength'] < 0.6:
                continue
            
            aspect_name = asp['aspect']
            planet = asp['planet']
            strength = asp['strength']
            
            if aspect_name in financial_impact:
                impact = financial_impact[aspect_name]
                planet_weight = planet_weights.get(planet, 1.0)
                
                weighted_trend = impact['trend'] * strength * planet_weight * impact['weight']
                total_trend += weighted_trend
                total_weight += strength * planet_weight
        
        if total_weight == 0:
            return {
                'direction': 'NEUTRAL',
                'confidence': 0.5,
                'aspects_count': len(aspects)
            }
        
        avg_trend = total_trend / total_weight
        
        # Направление
        if avg_trend > 0.3:
            direction = 'BULLISH'
            confidence = min(0.6 + avg_trend * 0.2, 0.85)
        elif avg_trend < -0.3:
            direction = 'BEARISH'
            confidence = min(0.6 + abs(avg_trend) * 0.2, 0.85)
        else:
            direction = 'NEUTRAL'
            confidence = 0.5
        
        return {
            'direction': direction,
            'confidence': confidence,
            'aspects_count': len(aspects),
            'trend_score': avg_trend
        }


class NatalChartManager:
    """
    Управление натальными картами всех активов
    """
    
    def __init__(self):
        # Load assets config
        config_path = Path(__file__).parent.parent / 'configs' / 'assets.yaml'
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        self.natal_charts = {}
        
        # Create natal charts
        for symbol, data in config['assets'].items():
            if data.get('active', False):
                # Parse date WITHOUT timezone
                date_str = data['natal']['date'].replace('Z', '').replace('+00:00', '')
                birth_date = datetime.fromisoformat(date_str)
                self.natal_charts[symbol] = NatalChart(birth_date, symbol)
        
        print(f"✅ Natal Chart Manager initialized ({len(self.natal_charts)} assets)")
    
    def get_signal(self, symbol: str, date: datetime) -> Dict:
        """
        Получить сигнал для актива
        """
        if symbol not in self.natal_charts:
            return {'direction': 'NEUTRAL', 'confidence': 0.5}
        
        return self.natal_charts[symbol].get_financial_signal(date)


if __name__ == "__main__":
    # Test
    manager = NatalChartManager()
    
    today = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"NATAL TRANSITS for {today.date()}")
    print(f"{'='*60}")
    
    for symbol in ['BTCUSDT', 'ETHUSDT']:
        if symbol in manager.natal_charts:
            signal = manager.get_signal(symbol, today)
            
            print(f"\n{symbol}:")
            print(f"  Direction: {signal['direction']}")
            print(f"  Confidence: {signal['confidence']:.2%}")
            print(f"  Aspects: {signal['aspects_count']}")
            if 'trend_score' in signal:
                print(f"  Trend Score: {signal['trend_score']:.3f}")
