#!/usr/bin/env python3
"""
Data Integrator - объединяет все индикаторы в единую систему
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class DataIntegrator:
    def __init__(self):
        self.logger = logging.getLogger('DataIntegrator')
        self.data_dirs = {
            'funding': 'data/funding_rate',
            'liquidations': 'data/liquidations', 
            'futures': 'data/futures_oi',
            'pcr': 'data/pcr',
            'oi': 'data/oi',
            'max_pain': 'data/max_pain',
            'gex': 'data/gamma_exposure',
            'vanna': 'data/vanna',
            'iv_rank': 'data/iv_rank',
            'volatility': 'data/volatility_greeks'
        }
    
    def get_futures_data(self, asset: str) -> Dict[str, Any]:
        """Получить фьючерсные данные"""
        try:
            futures_file = f"{self.data_dirs['futures']}/{asset}_futures.json"
            if os.path.exists(futures_file):
                with open(futures_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading futures data for {asset}: {e}")
        return {}
    
    def get_funding_rate(self, asset: str) -> Dict[str, Any]:
        """Получить funding rate"""
        try:
            funding_file = f"{self.data_dirs['funding']}/{asset}_funding.json"
            if os.path.exists(funding_file):
                with open(funding_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading funding data for {asset}: {e}")
        return {}
    
    def get_liquidations(self, asset: str) -> Dict[str, Any]:
        """Получить ликвидации"""
        try:
            liq_file = f"{self.data_dirs['liquidations']}/{asset}_liquidations.json"
            if os.path.exists(liq_file):
                with open(liq_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading liquidations for {asset}: {e}")
        return {}
    
    def get_pcr_data(self, asset: str) -> Dict[str, Any]:
        """Получить PCR данные"""
        try:
            pcr_file = f"{self.data_dirs['pcr']}/{asset}_pcr.json"
            if os.path.exists(pcr_file):
                with open(pcr_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading PCR data for {asset}: {e}")
        return {}
    
    def get_all_data(self, asset: str) -> Dict[str, Any]:
        """Получить ВСЕ данные для актива"""
        self.logger.info(f"Integrating data for {asset}")
        
        data = {
            # Фьючерсные данные
            'futures': self.get_futures_data(asset),
            'funding': self.get_funding_rate(asset),
            'liquidations': self.get_liquidations(asset),
            
            # Опционные данные
            'pcr': self.get_pcr_data(asset),
            'oi': self.get_oi_data(asset),
            'max_pain': self.get_max_pain(asset),
            'gex': self.get_gamma_exposure(asset),
            'vanna': self.get_vanna_data(asset),
            'iv_rank': self.get_iv_rank_data(asset),
            'volatility': self.get_volatility_data(asset),
            
            # Метаданные
            'timestamp': datetime.now().isoformat(),
            'asset': asset,
            'data_quality': self._calculate_data_quality(asset)
        }
        
        return data
    
    def get_oi_data(self, asset: str) -> Dict[str, Any]:
        """Получить OI данные (заглушка)"""
        # TODO: Реализовать
        return {}
    
    def get_max_pain(self, asset: str) -> Dict[str, Any]:
        """Получить Max Pain (заглушка)"""
        # TODO: Реализовать
        return {}
    
    def get_gamma_exposure(self, asset: str) -> Dict[str, Any]:
        """Получить Gamma Exposure (заглушка)"""
        # TODO: Реализовать
        return {}
    
    def get_vanna_data(self, asset: str) -> Dict[str, Any]:
        """Получить Vanna данные (заглушка)"""
        # TODO: Реализовать
        return {}
    
    def get_iv_rank_data(self, asset: str) -> Dict[str, Any]:
        """Получить IV Rank данные (заглушка)"""
        # TODO: Реализовать
        return {}
    
    def get_volatility_data(self, asset: str) -> Dict[str, Any]:
        """Получить Volatility данные (заглушка)"""
        # TODO: Реализовать
        return {}
    
    def _calculate_data_quality(self, asset: str) -> Dict[str, Any]:
        """Рассчитать качество данных"""
        data = self.get_all_data(asset)
        available_sources = 0
        total_sources = len([k for k in data.keys() if k not in ['timestamp', 'asset', 'data_quality']])
        
        for key, value in data.items():
            if key not in ['timestamp', 'asset', 'data_quality'] and value:
                available_sources += 1
        
        quality_score = available_sources / total_sources if total_sources > 0 else 0
        
        return {
            'available_sources': available_sources,
            'total_sources': total_sources,
            'quality_score': round(quality_score, 2),
            'timestamp': datetime.now().isoformat()
        }

# Тестовый запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    integrator = DataIntegrator()
    
    # Протестируем на ETH
    test_data = integrator.get_all_data('ETH')
    print("✅ DataIntegrator создан!")
    print(f"📊 Качество данных: {test_data['data_quality']}")
