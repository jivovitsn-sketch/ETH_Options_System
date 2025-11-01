#!/usr/bin/env python3
"""
Быстрый тест интеграции DataIntegrator + SignalAnalyzer
"""

import logging
from data_integrator import DataIntegrator
from signal_analyzer import SignalAnalyzer

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

print("🚀 БЫСТРЫЙ ТЕСТ ИНТЕГРАЦИИ STAGE 1.4")
print("=" * 50)

# Инициализируем компоненты
integrator = DataIntegrator()
analyzer = SignalAnalyzer()

# Получаем доступные активы
assets = integrator.get_available_assets()
print(f"📊 Доступные активы: {assets}")

# Тестируем на ETH (должен быть доступен)
test_asset = 'ETH' if 'ETH' in assets else assets[0] if assets else 'BTC'
print(f"🔍 Тестируем на {test_asset}...")

try:
    # 1. Собираем данные
    print("   🔄 Собираем данные...")
    data = integrator.get_all_data(test_asset)
    quality = data['data_quality']
    print(f"   ✅ Качество данных: {quality['quality_score']} ({quality['available_sources']}/{quality['total_sources']} источников)")
    
    # 2. Анализируем
    print("   🎯 Анализируем...")
    signal = analyzer.analyze(data)
    
    print(f"   📈 Результат:")
    print(f"      Сигнал: {signal['signal_type']}")
    print(f"      Уверенность: {signal['confidence']}")
    print(f"      Обоснование: {signal['reasoning']}")
    
    # 3. Показываем использованные индикаторы
    print(f"   🔧 Использованные компоненты:")
    for component, details in signal['components'].items():
        indicators = details.get('indicators_used', [])
        if indicators:
            print(f"      {component}: {indicators}")
    
    print(f"\n🎉 ИНТЕГРАЦИЯ РАБОТАЕТ! Stage 1.4 готов к использованию!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("💡 Совет: Проверьте что есть данные через diagnose_data.py")
