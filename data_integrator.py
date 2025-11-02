#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATA INTEGRATOR - Stage 1.4 (Full Integration)
Все 11 источников данных
"""

import logging
from datetime import datetime
from typing import Dict, Any
from data_integration import (
    get_futures_data,
    get_recent_liquidations,
    get_gamma_exposure,
    get_max_pain,
    get_pcr_data,
    get_vanna_data,
    get_iv_rank_data,
    get_option_vwap,
    get_pcr_rsi,
    get_gex_rsi,
    get_oi_macd
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIntegrator:
    """Объединяет ВСЕ источники данных"""
    
    def __init__(self):
        self.data_sources = {
            'futures': get_futures_data,
            'liquidations': get_recent_liquidations,
            'pcr': get_pcr_data,
            'max_pain': get_max_pain,
            'gex': get_gamma_exposure,
            'vanna': get_vanna_data,
            'iv_rank': get_iv_rank_data,
            'option_vwap': get_option_vwap,
            'pcr_rsi': get_pcr_rsi,
            'gex_rsi': get_gex_rsi,
            'oi_macd': get_oi_macd
        }
    
    def get_all_data(self, asset: str) -> Dict[str, Any]:
        """Собрать ВСЕ данные"""
        try:
            data = {
                'asset': asset,
                'timestamp': datetime.now(),
                'spot_price': None,
                'available_sources': []
            }
            
            for source_name, source_func in self.data_sources.items():
                try:
                    if source_name == 'liquidations':
                        result = source_func(asset, hours=4)
                    else:
                        result = source_func(asset)
                    
                    data[source_name] = result
                    
                    if result is not None:
                        data['available_sources'].append(source_name)
                    
                    # Spot price
                    if data['spot_price'] is None and result:
                        if isinstance(result, dict):
                            if 'spot_price' in result:
                                data['spot_price'] = result['spot_price']
                            elif 'price' in result:
                                data['spot_price'] = result['price']
                
                except Exception as e:
                    logger.warning(f"Failed {source_name} for {asset}: {e}")
                    data[source_name] = None
            
            data['quality'] = self.get_data_quality_report(data)
            return data
            
        except Exception as e:
            logger.error(f"Failed to integrate data for {asset}: {e}")
            return self._get_fallback_data(asset)
    
    def _get_fallback_data(self, asset: str) -> Dict[str, Any]:
        """Минимальные данные при ошибке"""
        try:
            futures = get_futures_data(asset)
            spot_price = futures.get('price') if futures else None
        except:
            spot_price = None
        
        return {
            'asset': asset,
            'timestamp': datetime.now(),
            'spot_price': spot_price,
            'available_sources': [],
            'quality': {'status': 'FALLBACK'}
        }
    
    def get_data_quality_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка качества"""
        total_sources = len(self.data_sources)
        available = len(data.get('available_sources', []))
        completeness = available / total_sources if total_sources > 0 else 0
        
        if completeness >= 0.8:
            status = 'EXCELLENT'
        elif completeness >= 0.6:
            status = 'GOOD'
        elif completeness >= 0.4:
            status = 'ACCEPTABLE'
        else:
            status = 'POOR'
        
        return {
            'status': status,
            'available_sources': available,
            'total_sources': total_sources,
            'completeness': completeness,
            'missing_sources': [s for s in self.data_sources.keys() 
                               if s not in data.get('available_sources', [])]
        }


if __name__ == '__main__':
    integrator = DataIntegrator()
    
    print("=" * 60)
    print("🧪 DATA INTEGRATOR - FULL (11 SOURCES)")
    print("=" * 60)
    
    for asset in ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']:
        print(f"\n📊 {asset}:")
        data = integrator.get_all_data(asset)
        
        quality = data.get('quality', {})
        print(f"  Quality: {quality.get('status')} ({quality.get('completeness', 0)*100:.0f}%)")
        print(f"  Sources: {quality.get('available_sources')}/{quality.get('total_sources')}")
        print(f"  Price: ${data.get('spot_price', 0):,.2f}")
        
        # Проверяем новые индикаторы
        if data.get('pcr_rsi'):
            print(f"  ✅ PCR RSI: {data['pcr_rsi']:.1f}")
        if data.get('gex_rsi'):
            print(f"  ✅ GEX RSI: {data['gex_rsi']:.1f}")
        if data.get('oi_macd'):
            print(f"  ✅ OI MACD: {data['oi_macd']['histogram']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE - ALL 11 SOURCES")
    print("=" * 60)
