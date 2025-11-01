#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPTION VWAP CALCULATOR - Stage 1.4.6 (FIXED)
Расчет VWAP (Volume-Weighted Average Price) для опционов
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptionVWAPCalculator:
    """Расчет VWAP для опционных цен"""
    
    def __init__(self):
        self.db_path = './data/unlimited_oi.db'
        self.output_dir = Path('./data/option_vwap/')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_vwap(self, asset: str) -> Optional[Dict[str, Any]]:
        """Расчет VWAP для актива"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ИСПРАВЛЕНО: option_type вместо side, Call/Put с большой буквы
            cursor.execute('''
                SELECT strike, option_type, open_interest, spot_price
                FROM all_positions_tracking
                WHERE asset = ?
                AND open_interest > 0
                AND spot_price > 0
                ORDER BY strike
            ''', (asset,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                logger.warning(f"No data for {asset}")
                return None
            
            # Расчёт VWAP для calls и puts отдельно
            call_volume = 0
            call_weighted_sum = 0
            put_volume = 0
            put_weighted_sum = 0
            
            for strike, option_type, oi, price in rows:
                # Используем strike как "цену" опциона для VWAP
                volume = oi
                weighted_value = strike * oi
                
                if option_type == 'Call':
                    call_volume += volume
                    call_weighted_sum += weighted_value
                elif option_type == 'Put':
                    put_volume += volume
                    put_weighted_sum += weighted_value
            
            # Вычисляем VWAP
            call_vwap = call_weighted_sum / call_volume if call_volume > 0 else 0
            put_vwap = put_weighted_sum / put_volume if put_volume > 0 else 0
            
            # Общий VWAP
            total_volume = call_volume + put_volume
            total_weighted = call_weighted_sum + put_weighted_sum
            total_vwap = total_weighted / total_volume if total_volume > 0 else 0
            
            result = {
                'asset': asset,
                'timestamp': datetime.now().isoformat(),
                'call_vwap': round(call_vwap, 2),
                'put_vwap': round(put_vwap, 2),
                'total_vwap': round(total_vwap, 2),
                'call_volume': round(call_volume, 4),
                'put_volume': round(put_volume, 4),
                'total_volume': round(total_volume, 4),
                'vwap_ratio': round(call_vwap / put_vwap, 4) if put_vwap > 0 else 0
            }
            
            # Сохраняем в JSON
            self._save_to_json(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating VWAP for {asset}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_to_json(self, result: Dict[str, Any]):
        """Сохранение результата в JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{result['asset']}_vwap_{timestamp}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"✅ Saved: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
    
    def calculate_all(self, assets: list) -> Dict[str, Any]:
        """Расчет VWAP для всех активов"""
        results = {}
        
        for asset in assets:
            result = self.calculate_vwap(asset)
            if result:
                results[asset] = result
        
        return results


def get_option_vwap(asset: str) -> Optional[Dict[str, Any]]:
    """Функция для интеграции с data_integration.py"""
    calculator = OptionVWAPCalculator()
    return calculator.calculate_vwap(asset)


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 OPTION VWAP CALCULATOR TEST")
    print("=" * 60)
    
    calculator = OptionVWAPCalculator()
    
    # ВСЕ 6 АКТИВОВ!
    assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
    
    for asset in assets:
        print(f"\n📊 {asset}:")
        result = calculator.calculate_vwap(asset)
        
        if result:
            print(f"  Call VWAP: ${result['call_vwap']:,.2f}")
            print(f"  Put VWAP: ${result['put_vwap']:,.2f}")
            print(f"  Total VWAP: ${result['total_vwap']:,.2f}")
            print(f"  Total Volume: {result['total_volume']:.4f}")
        else:
            print(f"  ❌ No data")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
