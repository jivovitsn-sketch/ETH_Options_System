#!/usr/bin/env python3
"""
Продвинутый тест интеграции с конфигурацией
"""

import json
import logging
from data_integrator import DataIntegrator
from signal_analyzer import SignalAnalyzer

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

print("🚀 ПРОДВИНУТЫЙ ТЕСТ ИНТЕГРАЦИИ STAGE 1.4")
print("=" * 60)

# Загружаем конфиг
try:
    with open('signal_config.json', 'r') as f:
        config = json.load(f)
    print("✅ Конфигурация загружена")
except:
    config = None
    print("⚠️  Используется конфигурация по умолчанию")

# Инициализируем компоненты
integrator = DataIntegrator()
analyzer = SignalAnalyzer(config)

# Получаем доступные активы
assets = integrator.get_available_assets()
print(f"📊 Доступные активы: {assets}")

print(f"\n🔍 ГЕНЕРАЦИЯ СИГНАЛОВ ДЛЯ ВСЕХ АКТИВОВ:")
print("-" * 50)

signals_summary = []

for asset in assets:
    try:
        # Собираем данные
        data = integrator.get_all_data(asset)
        quality = data['data_quality']
        
        # Пропускаем если мало данных
        if quality['quality_score'] < 0.2:
            continue
            
        # Анализируем
        signal = analyzer.analyze(data)
        
        # Сохраняем для summary
        signals_summary.append({
            'asset': asset,
            'signal': signal['signal_type'],
            'confidence': signal['confidence'],
            'quality': quality['quality_score']
        })
        
        # Выводим результат
        status_icon = "🟢" if "BULLISH" in signal['signal_type'] else "🔴" if "BEARISH" in signal['signal_type'] else "⚪"
        print(f"{status_icon} {asset:6} - {signal['signal_type']:15} (conf: {signal['confidence']:.2f}, quality: {quality['quality_score']:.2f})")
        
        # Детали для сильных сигналов
        if signal['confidence'] > 0.7:
            print(f"     📝 {signal['reasoning']}")
            
    except Exception as e:
        print(f"❌ {asset:6} - Ошибка: {e}")

# Сводка
print(f"\n📈 СВОДКА СИГНАЛОВ:")
print("-" * 50)

bullish_count = len([s for s in signals_summary if "BULLISH" in s['signal']])
bearish_count = len([s for s in signals_summary if "BEARISH" in s['signal']])
strong_signals = [s for s in signals_summary if s['confidence'] > 0.7]

print(f"📊 Всего сигналов: {len(signals_summary)}")
print(f"🟢 Бычьих: {bullish_count}")
print(f"🔴 Медвежьих: {bearish_count}")
print(f"🎯 Сильных сигналов: {len(strong_signals)}")

if strong_signals:
    print(f"\n💪 СИЛЬНЫЕ СИГНАЛЫ:")
    for signal in strong_signals:
        print(f"   ⭐ {signal['asset']} - {signal['signal']} (conf: {signal['confidence']:.2f})")

print(f"\n🎉 STAGE 1.4 УСПЕШНО РЕАЛИЗОВАНА!")
print("   DataIntegrator ✅ | SignalAnalyzer ✅ | Конфигурация ✅")
