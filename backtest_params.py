#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST PARAMETERS - Параметры для оптимизации в бэктесте
Stage 1.4.4 (Updated)
"""

BACKTEST_PARAMETERS = {
    # ===== ВЕСА ГРУПП =====
    'futures_weight': {
        'min': 0.20,
        'max': 0.50,
        'step': 0.05,
        'default': 0.35,
        'description': 'Вес фьючерсных индикаторов'
    },
    'options_weight': {
        'min': 0.30,
        'max': 0.60,
        'step': 0.05,
        'default': 0.45,
        'description': 'Вес опционных индикаторов'
    },
    'timing_weight': {
        'min': 0.10,
        'max': 0.40,
        'step': 0.05,
        'default': 0.20,
        'description': 'Вес тайминговых индикаторов'
    },
    
    # ===== ПОРОГИ ДЛЯ ИНДИКАТОРОВ =====
    'pcr_bullish_threshold': {
        'min': 0.6,
        'max': 1.0,
        'step': 0.1,
        'default': 0.8,
        'description': 'PCR ниже этого = бычий сигнал'
    },
    'pcr_bearish_threshold': {
        'min': 1.0,
        'max': 1.6,
        'step': 0.1,
        'default': 1.2,
        'description': 'PCR выше этого = медвежий сигнал'
    },
    'max_pain_threshold': {
        'min': 0.01,
        'max': 0.05,
        'step': 0.01,
        'default': 0.02,
        'description': 'Порог отклонения от Max Pain (%)'
    },
    'vanna_threshold': {
        'min': 0,
        'max': 1000,
        'step': 100,
        'default': 0,
        'description': 'Минимальное значение Vanna для учёта'
    },
    
    # ===== ФИЛЬТРЫ =====
    'min_confidence': {
        'min': 0.50,
        'max': 0.80,
        'step': 0.05,
        'default': 0.60,
        'description': 'Минимальная уверенность для генерации сигнала'
    },
    'strong_threshold': {
        'min': 0.70,
        'max': 0.95,
        'step': 0.05,
        'default': 0.75,
        'description': 'Порог для STRONG сигнала'
    },
    'min_data_sources': {
        'min': 2,
        'max': 7,
        'step': 1,
        'default': 2,
        'description': 'Минимум источников данных для генерации сигнала'
    }
}

def count_combinations():
    """Подсчет всех возможных комбинаций параметров"""
    total = 1
    for param, settings in BACKTEST_PARAMETERS.items():
        if 'min' in settings and 'max' in settings and 'step' in settings:
            count = int((settings['max'] - settings['min']) / settings['step']) + 1
            total *= count
    return total

def get_default_config():
    """Получить дефолтную конфигурацию совместимую с signal_analyzer.py"""
    config = {
        # Веса групп
        'futures_weight': 0.35,
        'options_weight': 0.45,
        'timing_weight': 0.20,
        
        # Пороги индикаторов
        'pcr_bullish_threshold': 0.8,
        'pcr_bearish_threshold': 1.2,
        'max_pain_threshold': 0.02,
        'vanna_threshold': 0,
        
        # Фильтры
        'min_confidence': 0.60,
        'strong_threshold': 0.75,
        'min_data_sources': 2,
        
        # Дополнительные параметры
        'require_futures_confirm': False,
        'require_options_confirm': True,
        'min_data_quality': 'ACCEPTABLE'
    }
    
    return config

def generate_random_config():
    """Генерация случайной валидной конфигурации для тестирования"""
    import random
    
    config = get_default_config()
    
    for param, settings in BACKTEST_PARAMETERS.items():
        if 'min' in settings and 'max' in settings and 'step' in settings:
            min_val = settings['min']
            max_val = settings['max']
            step = settings['step']
            
            steps_count = int((max_val - min_val) / step)
            random_steps = random.randint(0, steps_count)
            value = min_val + random_steps * step
            
            config[param] = value
    
    return config

if __name__ == '__main__':
    import json
    
    print("=" * 60)
    print("🔧 BACKTEST PARAMETERS (Updated)")
    print("=" * 60)
    print()
    print(f"Total combinations: {count_combinations():,}")
    print()
    print("Default config:")
    print(json.dumps(get_default_config(), indent=2))
    print()
    print("=" * 60)
