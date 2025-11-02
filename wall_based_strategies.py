#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WALL-BASED STRATEGIES - Опционные стратегии для стенок
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class WallBasedStrategies:
    """Стратегии основанные на стенках экспираций"""
    
    def generate_wall_strategies(self, walls_data: Dict[str, Any], 
                                 spot_price: float) -> List[Dict[str, Any]]:
        """Генерация стратегий на основе стенок"""
        
        if not walls_data:
            return []
        
        magnetic = walls_data.get('magnetic_levels', {})
        
        call_wall = magnetic.get('call_wall')
        put_wall = magnetic.get('put_wall')
        call_wall_oi = magnetic.get('call_wall_oi', 0)
        put_wall_oi = magnetic.get('put_wall_oi', 0)
        
        if not call_wall or not put_wall:
            return []
        
        strategies = []
        
        # 1. Диапазонные стратегии между стенками
        if put_wall < spot_price < call_wall:
            strategies.append({
                'name': 'IRON_CONDOR_WALLS',
                'description': f'Iron Condor between walls ${put_wall:.0f}-${call_wall:.0f}',
                'logic': 'Range trading between major walls',
                'confidence_boost': 0.08,
                'walls_context': {
                    'call_wall': call_wall,
                    'put_wall': put_wall,
                    'position': 'BETWEEN_WALLS'
                }
            })
        
        # 2. Отскок от стенки
        distance_to_call = abs(spot_price - call_wall) / call_wall
        distance_to_put = abs(spot_price - put_wall) / put_wall
        
        if distance_to_call < 0.02:  # < 2% от call wall
            strategies.append({
                'name': 'BEAR_CALL_SPREAD_BOUNCE',
                'description': f'Bounce off call wall ${call_wall:.0f}',
                'logic': 'Expect bounce from resistance',
                'confidence_boost': min(0.15, call_wall_oi / 10000),
                'walls_context': {
                    'wall_strike': call_wall,
                    'wall_type': 'CALL',
                    'position': 'NEAR_WALL'
                }
            })
        
        if distance_to_put < 0.02:  # < 2% от put wall
            strategies.append({
                'name': 'BULL_PUT_SPREAD_BOUNCE',
                'description': f'Bounce off put wall ${put_wall:.0f}',
                'logic': 'Expect bounce from support',
                'confidence_boost': min(0.15, put_wall_oi / 10000),
                'walls_context': {
                    'wall_strike': put_wall,
                    'wall_type': 'PUT',
                    'position': 'NEAR_WALL'
                }
            })
        
        # 3. Пробой стенки
        if spot_price > call_wall:
            strategies.append({
                'name': 'LONG_CALL_BREAKTHROUGH',
                'description': f'Breakthrough call wall ${call_wall:.0f}',
                'logic': 'Continuation after resistance break',
                'confidence_boost': min(0.10, call_wall_oi / 15000),
                'walls_context': {
                    'wall_strike': call_wall,
                    'wall_type': 'CALL',
                    'position': 'ABOVE_WALL'
                }
            })
        
        if spot_price < put_wall:
            strategies.append({
                'name': 'LONG_PUT_BREAKTHROUGH',
                'description': f'Breakthrough put wall ${put_wall:.0f}',
                'logic': 'Continuation after support break',
                'confidence_boost': min(0.10, put_wall_oi / 15000),
                'walls_context': {
                    'wall_strike': put_wall,
                    'wall_type': 'PUT',
                    'position': 'BELOW_WALL'
                }
            })
        
        return strategies


def generate_wall_based_strategies(asset: str, spot_price: float, 
                                   walls_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Генератор стратегий для интеграции"""
    strategist = WallBasedStrategies()
    return strategist.generate_wall_strategies(walls_data, spot_price)


if __name__ == '__main__':
    print("🎯 WALL-BASED STRATEGIES TEST")
    print("=" * 60)
    
    # Тестовые данные
    test_walls = {
        'asset': 'BTC',
        'expiration': '2025-11-08',
        'magnetic_levels': {
            'call_wall': 120000,
            'put_wall': 110000,
            'call_wall_oi': 5000,
            'put_wall_oi': 3000
        }
    }
    
    strategist = WallBasedStrategies()
    
    for spot in [115000, 119000, 121000, 109000]:
        print(f"\n📊 Spot: ${spot:,.0f}")
        print("-" * 40)
        
        strategies = strategist.generate_wall_strategies(test_walls, spot)
        
        for strat in strategies:
            print(f"  🎯 {strat['name']}")
            print(f"     {strat['description']}")
            print(f"     Boost: +{strat['confidence_boost']:.2%}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
