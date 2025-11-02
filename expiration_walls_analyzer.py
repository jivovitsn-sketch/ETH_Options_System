#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPIRATION WALLS ANALYZER - Анализ стенок опционов на экспирации
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from calendar import monthrange
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def get_last_friday_next_month() -> datetime:
    """Получить последнюю пятницу следующего месяца (экспирация 8:00 UTC)"""
    now = datetime.now()
    
    if now.month == 12:
        next_month = 1
        year = now.year + 1
    else:
        next_month = now.month + 1
        year = now.year
    
    last_day = monthrange(year, next_month)[1]
    last_date = datetime(year, next_month, last_day)
    
    while last_date.weekday() != 4:  # Friday
        last_date -= timedelta(days=1)
    
    last_date = last_date.replace(hour=8, minute=0, second=0, microsecond=0)
    return last_date

class ExpirationWallsAnalyzer:
    """Анализ стенок опционов на экспирации"""

    def __init__(self, db_path: str = './data/unlimited_oi.db'):
        self.db_path = db_path
        self.wall_threshold = 500  # Минимальный OI для стенки
        self.max_expiration = get_last_friday_next_month()

    def get_expiration_walls(self, asset: str) -> Optional[Dict[str, Any]]:
        """Получить стенки опционов для ближайшей экспирации"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Получаем данные по страйкам и экспирациям
            cutoff = int((datetime.now() - timedelta(hours=24)).timestamp())
            
            cursor.execute('''
                SELECT 
                    strike,
                    option_type,
                    expiry_date,
                    SUM(open_interest) as total_oi,
                    dte
                FROM all_positions_tracking
                WHERE asset = ? 
                  AND timestamp > ?
                  AND open_interest > 0
                  AND dte > 0
                  AND expiry_date <= ?
                  AND dte < 60
                GROUP BY strike, option_type, expiry_date
                HAVING total_oi > ?
                ORDER BY dte ASC, total_oi DESC
            ''', (asset, cutoff, self.max_expiration.strftime('%Y-%m-%d'), self.wall_threshold))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                logger.warning(f"No expiration walls found for {asset}")
                return None
            
            # Группируем по экспирациям
            expirations = {}
            for row in rows:
                strike, option_type, expiry, oi, dte = row
                
                if expiry not in expirations:
                    expirations[expiry] = {
                        'calls': [],
                        'puts': [],
                        'dte': dte
                    }
                
                wall_data = {'strike': strike, 'oi': oi}
                
                if option_type == 'Call':
                    expirations[expiry]['calls'].append(wall_data)
                else:
                    expirations[expiry]['puts'].append(wall_data)
            
            # Берём ближайшую экспирацию
            nearest_expiry = min(expirations.keys(), key=lambda x: expirations[x]['dte'])
            exp_data = expirations[nearest_expiry]
            
            # Анализируем стенки
            analysis = self._analyze_walls(
                exp_data['calls'][:10],
                exp_data['puts'][:10],
                asset,
                nearest_expiry,
                exp_data['dte']
            )
            
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing expiration walls for {asset}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _analyze_walls(self, call_walls: List, put_walls: List, 
                       asset: str, expiration: str, dte: int) -> Dict[str, Any]:
        """Анализ стенок и их влияния на цену"""
        
        # Сортируем по OI
        call_walls = sorted(call_walls, key=lambda x: x['oi'], reverse=True)
        put_walls = sorted(put_walls, key=lambda x: x['oi'], reverse=True)
        
        # Находим крупнейшие стенки
        largest_call = call_walls[0] if call_walls else None
        largest_put = put_walls[0] if put_walls else None

        # Рассчитываем общий OI
        total_call_oi = sum(wall['oi'] for wall in call_walls)
        total_put_oi = sum(wall['oi'] for wall in put_walls)

        # Определяем магнитные уровни
        magnetic_levels = {
            'call_wall': largest_call['strike'] if largest_call else None,
            'put_wall': largest_put['strike'] if largest_put else None,
            'call_wall_oi': largest_call['oi'] if largest_call else 0,
            'put_wall_oi': largest_put['oi'] if largest_put else 0
        }

        # Анализируем потенциальное давление
        pressure = self._calculate_pressure(magnetic_levels, total_call_oi, total_put_oi)

        return {
            'asset': asset,
            'expiration': expiration,
            'dte': dte,
            'timestamp': datetime.now().isoformat(),
            'magnetic_levels': magnetic_levels,
            'pressure_analysis': pressure,
            'call_walls': call_walls[:5],
            'put_walls': put_walls[:5],
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'wall_threshold': self.wall_threshold
        }

    def _calculate_pressure(self, magnetic_levels: Dict, 
                          total_call_oi: float, total_put_oi: float) -> Dict[str, Any]:
        """Расчет давления на цену от стенок"""
        
        call_wall_oi = magnetic_levels['call_wall_oi']
        put_wall_oi = magnetic_levels['put_wall_oi']

        analysis = {
            'direction': 'NEUTRAL',
            'confidence': 0.5,
            'reasoning': []
        }

        if call_wall_oi == 0 and put_wall_oi == 0:
            return analysis

        # Определяем направление давления
        if call_wall_oi > put_wall_oi * 1.5:
            analysis['direction'] = 'BEARISH'
            analysis['confidence'] = min(0.8, 0.5 + (call_wall_oi / (put_wall_oi + 1000) * 0.1))
            analysis['reasoning'].append(f"Strong call wall OI: {call_wall_oi:.0f}")
        elif put_wall_oi > call_wall_oi * 1.5:
            analysis['direction'] = 'BULLISH'
            analysis['confidence'] = min(0.8, 0.5 + (put_wall_oi / (call_wall_oi + 1000) * 0.1))
            analysis['reasoning'].append(f"Strong put wall OI: {put_wall_oi:.0f}")
        else:
            analysis['direction'] = 'RANGE_BOUND'
            analysis['confidence'] = 0.6
            analysis['reasoning'].append(f"Balanced walls")

        # Добавляем анализ общего OI
        if total_call_oi > total_put_oi * 1.2:
            analysis['reasoning'].append(f"Total call OI dominates: {total_call_oi:.0f}")
        elif total_put_oi > total_call_oi * 1.2:
            analysis['reasoning'].append(f"Total put OI dominates: {total_put_oi:.0f}")

        return analysis

    def save_analysis(self, analysis: Dict[str, Any]):
        """Сохранить анализ в JSON файл"""
        try:
            if not analysis:
                return

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            asset = analysis['asset']
            
            os.makedirs('data/expiration_walls', exist_ok=True)
            filename = f"data/expiration_walls/{asset}_walls_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)

            logger.info(f"✅ Walls analysis saved: {filename}")

        except Exception as e:
            logger.error(f"Error saving walls analysis: {e}")


def get_expiration_walls_data(asset: str) -> Optional[Dict[str, Any]]:
    """Функция для DataIntegrator"""
    analyzer = ExpirationWallsAnalyzer()
    analysis = analyzer.get_expiration_walls(asset)
    
    if analysis:
        analyzer.save_analysis(analysis)
    
    return analysis


if __name__ == '__main__':
    print("🧱 EXPIRATION WALLS ANALYZER TEST")
    print("=" * 60)
    
    analyzer = ExpirationWallsAnalyzer()
    
    for asset in ['BTC', 'ETH', 'XRP', 'SOL', 'DOGE', 'MNT']:
        print(f"\n📊 {asset}:")
        print("-" * 40)
        
        analysis = analyzer.get_expiration_walls(asset)
        
        if analysis:
            magnetic = analysis['magnetic_levels']
            pressure = analysis['pressure_analysis']
            
            print(f"  Expiration: {analysis['expiration']} (DTE: {analysis['dte']})")
            print(f"  Call Wall: ${magnetic['call_wall']:,.0f} (OI: {magnetic['call_wall_oi']:.0f})")
            print(f"  Put Wall: ${magnetic['put_wall']:,.0f} (OI: {magnetic['put_wall_oi']:.0f})")
            print(f"  Pressure: {pressure['direction']} ({pressure['confidence']:.0%})")
            
            if pressure['reasoning']:
                for reason in pressure['reasoning']:
                    print(f"    • {reason}")
        else:
            print(f"  ⚠️ No analysis available")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
