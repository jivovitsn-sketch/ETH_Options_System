#!/usr/bin/env python3
"""
Data Integrator - объединяет все индикаторы в единую систему
ИСПРАВЛЕННАЯ ВЕРСИЯ без рекурсии
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
    
    def _load_json_data(self, directory: str, asset: str, data_type: str) -> Dict[str, Any]:
        """Универсальный метод загрузки JSON данных"""
        try:
            file_path = f"{directory}/{asset}_{data_type}.json"
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading {data_type} data for {asset}: {e}")
        return {}
    
    def get_futures_data(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['futures'], asset, 'futures')
    
    def get_funding_rate(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['funding'], asset, 'funding')
    
    def get_liquidations(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['liquidations'], asset, 'liquidations')
    
    def get_pcr_data(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['pcr'], asset, 'pcr')
    
    def get_oi_data(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['oi'], asset, 'oi')
    
    def get_max_pain(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['max_pain'], asset, 'max_pain')
    
    def get_gamma_exposure(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['gex'], asset, 'gamma_exposure')
    
    def get_vanna_data(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['vanna'], asset, 'vanna')
    
    def get_iv_rank_data(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['iv_rank'], asset, 'iv_rank')
    
    def get_volatility_data(self, asset: str) -> Dict[str, Any]:
        return self._load_json_data(self.data_dirs['volatility'], asset, 'volatility_greeks')
    
    def _calculate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Рассчитать качество данных на основе уже собранных данных (без рекурсии!)"""
        available_sources = 0
        # Исключаем мета-поля из подсчета
        meta_fields = ['timestamp', 'asset', 'data_quality']
        data_fields = [k for k in data.keys() if k not in meta_fields]
        total_sources = len(data_fields)
        
        for key in data_fields:
            if data[key] and isinstance(data[key], dict) and len(data[key]) > 0:
                available_sources += 1
        
        quality_score = available_sources / total_sources if total_sources > 0 else 0
        
        return {
            'available_sources': available_sources,
            'total_sources': total_sources,
            'quality_score': round(quality_score, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_all_data(self, asset: str) -> Dict[str, Any]:
        """Получить ВСЕ данные для актива (исправленная версия)"""
        self.logger.info(f"Integrating data for {asset}")
        
        # Собираем все данные
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
            'asset': asset
        }
        
        # ТЕПЕРЬ вычисляем качество данных (без рекурсии!)
        data['data_quality'] = self._calculate_data_quality(data)
        
        return data

# Тестовый запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    integrator = DataIntegrator()
    
    # Протестируем на ETH
    test_data = integrator.get_all_data('ETH')
    print("✅ DataIntegrator создан и работает!")
    print(f"📊 Качество данных: {test_data['data_quality']}")
    print(f"📁 Доступные источники: {test_data['data_quality']['available_sources']}/{test_data['data_quality']['total_sources']}")
