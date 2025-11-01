#!/usr/bin/env python3
"""
Data Integrator v2 - работает с реальными файлами системы
"""

import os
import json
import logging
import glob
from datetime import datetime
from typing import Dict, Any, List

class DataIntegrator:
    def __init__(self):
        self.logger = logging.getLogger('DataIntegrator')
        self.base_data_dir = 'data'
        
        # Соответствие между типами данных и папками
        self.data_mapping = {
            'funding': 'funding_rate',
            'liquidations': 'liquidations',
            'futures': 'futures_oi', 
            'pcr': 'pcr',
            'oi': 'oi',
            'max_pain': 'max_pain',
            'gex': 'gamma_exposure',
            'vanna': 'vanna',
            'iv_rank': 'iv_rank',
            'volatility': 'volatility_greeks'
        }
    
    def _get_latest_file(self, directory: str, asset: str, pattern: str = None) -> str:
        """Найти самый свежий файл для актива в директории"""
        if not os.path.exists(directory):
            return None
            
        if pattern:
            search_pattern = f"{directory}/{asset}_{pattern}*.json"
        else:
            search_pattern = f"{directory}/{asset}_*.json"
        
        files = glob.glob(search_pattern)
        if not files:
            return None
            
        # Возвращаем самый новый файл (по времени изменения)
        return max(files, key=os.path.getmtime)
    
    def _load_latest_data(self, data_type: str, asset: str) -> Dict[str, Any]:
        """Загрузить самые свежие данные для типа и актива"""
        directory_key = self.data_mapping.get(data_type)
        if not directory_key:
            self.logger.warning(f"Unknown data type: {data_type}")
            return {}
            
        directory = os.path.join(self.base_data_dir, directory_key)
        latest_file = self._get_latest_file(directory, asset)
        
        if not latest_file:
            self.logger.debug(f"No data found for {asset} in {directory}")
            return {}
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
                # Добавляем метаданные о файле
                data['_metadata'] = {
                    'file_path': latest_file,
                    'file_timestamp': datetime.fromtimestamp(os.path.getmtime(latest_file)).isoformat(),
                    'data_type': data_type
                }
                return data
        except Exception as e:
            self.logger.error(f"Error loading {latest_file}: {e}")
            return {}
    
    def get_futures_data(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('futures', asset)
    
    def get_funding_rate(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('funding', asset)
    
    def get_liquidations(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('liquidations', asset)
    
    def get_pcr_data(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('pcr', asset)
    
    def get_oi_data(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('oi', asset)
    
    def get_max_pain(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('max_pain', asset)
    
    def get_gamma_exposure(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('gex', asset)
    
    def get_vanna_data(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('vanna', asset)
    
    def get_iv_rank_data(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('iv_rank', asset)
    
    def get_volatility_data(self, asset: str) -> Dict[str, Any]:
        return self._load_latest_data('volatility', asset)
    
    def _calculate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Рассчитать качество данных на основе уже собранных данных"""
        available_sources = 0
        meta_fields = ['timestamp', 'asset', 'data_quality', '_metadata']
        data_fields = [k for k in data.keys() if k not in meta_fields]
        total_sources = len(data_fields)
        
        for key in data_fields:
            if data[key] and isinstance(data[key], dict) and len(data[key]) > 0:
                # Проверяем что есть хотя бы одно не-мета поле
                non_meta_fields = [k for k in data[key].keys() if not k.startswith('_')]
                if non_meta_fields:
                    available_sources += 1
        
        quality_score = available_sources / total_sources if total_sources > 0 else 0
        
        return {
            'available_sources': available_sources,
            'total_sources': total_sources,
            'quality_score': round(quality_score, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_all_data(self, asset: str) -> Dict[str, Any]:
        """Получить ВСЕ данные для актива"""
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
        
        # Вычисляем качество данных
        data['data_quality'] = self._calculate_data_quality(data)
        
        return data
    
    def get_available_assets(self) -> List[str]:
        """Получить список активов, для которых есть данные"""
        assets = set()
        
        for data_type, directory in self.data_mapping.items():
            dir_path = os.path.join(self.base_data_dir, directory)
            if os.path.exists(dir_path):
                files = glob.glob(f"{dir_path}/*.json")
                for file in files:
                    # Извлекаем имя актива из文件名 (первая часть до _)
                    filename = os.path.basename(file)
                    asset = filename.split('_')[0]
                    assets.add(asset)
        
        return sorted(list(assets))

# Тестовый запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    integrator = DataIntegrator()
    
    print("🧪 DataIntegrator v2 - ТЕСТ С РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 50)
    
    # Получаем доступные активы
    available_assets = integrator.get_available_assets()
    print(f"📊 Найдены активы: {available_assets}")
    
    # Тестируем на каждом доступном активе
    for asset in available_assets[:3]:  # Первые 3 чтобы не перегружать
        print(f"\n🔍 Тестируем {asset}...")
        try:
            data = integrator.get_all_data(asset)
            quality = data['data_quality']
            print(f"   ✅ {asset}: {quality['available_sources']}/{quality['total_sources']} источников (качество: {quality['quality_score']})")
            
            # Показываем какие данные найдены
            found_sources = []
            for key, value in data.items():
                if key not in ['timestamp', 'asset', 'data_quality'] and value and len(value) > 0:
                    non_meta_fields = [k for k in value.keys() if not k.startswith('_')]
                    if non_meta_fields:
                        found_sources.append(key)
            
            if found_sources:
                print(f"   📁 Найдены: {', '.join(found_sources)}")
            
        except Exception as e:
            print(f"   ❌ Ошибка для {asset}: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 DataIntegrator v2 готов к работе!")
