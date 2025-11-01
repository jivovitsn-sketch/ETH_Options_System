#!/usr/bin/env python3
"""
Системный health check для Stage 1.4 + 1.5
"""

import json
import logging
from data_integrator import DataIntegrator
from signal_analyzer import SignalAnalyzer
from backtest_engine import BacktestEngine

def main():
    print("🔧 SYSTEM HEALTH CHECK - STAGE 1.4 + 1.5")
    print("=" * 60)
    
    # 1. Проверка конфигурации
    print("\n1. 📋 ПРОВЕРКА КОНФИГУРАЦИИ")
    try:
        with open('signal_config.json', 'r') as f:
            config = json.load(f)
        required_params = [
            'futures_weight', 'options_weight', 'timing_weight',
            'min_confidence', 'strong_threshold', 'min_data_sources',
            'pcr_bullish_threshold', 'pcr_bearish_threshold', 
            'max_pain_threshold', 'vanna_threshold'
        ]
        
        missing_params = [p for p in required_params if p not in config]
        if missing_params:
            print(f"   ❌ Отсутствуют параметры: {missing_params}")
        else:
            print(f"   ✅ Все {len(required_params)} параметров присутствуют")
            
    except Exception as e:
        print(f"   ❌ Ошибка загрузки конфига: {e}")
    
    # 2. Проверка DataIntegrator
    print("\n2. 🔄 ПРОВЕРКА DATA INTEGRATOR")
    try:
        integrator = DataIntegrator()
        assets = integrator.get_available_assets()
        print(f"   ✅ Найдено активов: {len(assets)}")
        
        # Проверяем данные для ETH
        eth_data = integrator.get_all_data('ETH')
        quality = eth_data['data_quality']
        print(f"   📊 Качество данных ETH: {quality['quality_score']} ({quality['available_sources']}/{quality['total_sources']} источников)")
        
        # Показываем какие данные найдены
        found_sources = []
        for key, value in eth_data.items():
            if key not in ['timestamp', 'asset', 'data_quality'] and value and len(value) > 0:
                non_meta_fields = [k for k in value.keys() if not k.startswith('_')]
                if non_meta_fields:
                    found_sources.append(key)
        
        print(f"   📁 Найдены индикаторы: {', '.join(found_sources)}")
        
    except Exception as e:
        print(f"   ❌ Ошибка DataIntegrator: {e}")
    
    # 3. Проверка SignalAnalyzer
    print("\n3. 🎯 ПРОВЕРКА SIGNAL ANALYZER")
    try:
        analyzer = SignalAnalyzer(config)
        signal = analyzer.analyze(eth_data)
        print(f"   ✅ Сигнал сгенерирован: {signal['signal_type']}")
        print(f"   🎯 Уверенность: {signal['confidence']}")
        print(f"   🧠 Обоснование: {signal['reasoning']}")
        
        # Проверяем метрики
        metrics = analyzer.get_performance_metrics()
        print(f"   📈 Метрики производительности: {metrics}")
        
    except Exception as e:
        print(f"   ❌ Ошибка SignalAnalyzer: {e}")
    
    # 4. Проверка Backtest Engine
    print("\n4. 📊 ПРОВЕРКА BACKTEST ENGINE")
    try:
        engine = BacktestEngine()
        results = engine.run_backtest()
        print(f"   ✅ Backtest engine работает")
        print(f"   📈 Смоделировано trades: {results['total_trades']}")
        
        # Проверка оптимизации
        param_ranges = {
            'min_confidence': [0.55, 0.60, 0.65],
            'futures_weight': [0.3, 0.35, 0.4]
        }
        optimization = engine.optimize_parameters(param_ranges)
        print(f"   🤖 Оптимизация готова: {len(optimization)} результатов")
        
    except Exception as e:
        print(f"   ❌ Ошибка Backtest Engine: {e}")
    
    # 5. Итоговая оценка
    print("\n5. 🎯 ИТОГОВАЯ ОЦЕНКА СИСТЕМЫ")
    print("=" * 60)
    
    # Проверяем готовность к Stage 1.5
    requirements = {
        "DataIntegrator работает": integrator is not None,
        "SignalAnalyzer генерирует сигналы": 'signal' in locals(),
        "Конфигурация загружена": 'config' in locals() and len(config) >= 10,
        "Backtest Engine работает": 'engine' in locals(),
        "Есть исторические данные": eth_data['data_quality']['available_sources'] >= 3
    }
    
    passed = sum(requirements.values())
    total = len(requirements)
    
    print(f"   ✅ Выполнено: {passed}/{total} требований")
    
    for req, status in requirements.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {req}")
    
    if passed == total:
        print(f"\n🎉 СИСТЕМА ГОТОВА К STAGE 1.5!")
        print("   Можно начинать бэктест и ML оптимизацию!")
    else:
        print(f"\n⚠️  СИСТЕМА ТРЕБУЕТ ДОРАБОТОК")
        print("   Нужно исправить указанные выше проблемы")

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)  # Уменьшаем логи для чистоты вывода
    main()
