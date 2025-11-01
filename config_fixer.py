#!/usr/bin/env python3
"""
Автоматическое исправление конфигурационных файлов
"""

import json
import os

def fix_signal_config():
    """Исправить signal_config.json"""
    default_config = {
        "futures_weight": 0.35,
        "options_weight": 0.45,
        "timing_weight": 0.20,
        "min_confidence": 0.60,
        "strong_threshold": 0.75,
        "min_data_sources": 2,
        "pcr_bullish_threshold": 0.8,
        "pcr_bearish_threshold": 1.2,
        "max_pain_threshold": 0.02,
        "vanna_threshold": 0
    }
    
    try:
        # Пробуем загрузить существующий конфиг
        if os.path.exists('signal_config.json'):
            with open('signal_config.json', 'r') as f:
                existing_config = json.load(f)
            
            # Обновляем недостающие параметры
            updated_config = {**default_config, **existing_config}
            
            with open('signal_config.json', 'w') as f:
                json.dump(updated_config, f, indent=4)
            
            print("✅ signal_config.json обновлен")
            return updated_config
        else:
            # Создаем новый конфиг
            with open('signal_config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
            print("✅ signal_config.json создан")
            return default_config
            
    except Exception as e:
        print(f"❌ Ошибка обновления signal_config.json: {e}")
        return None

def fix_backtest_config():
    """Исправить backtest_config.json"""
    default_config = {
        "test_period_days": 30,
        "assets": ["ETH", "BTC", "SOL"],
        "initial_balance": 10000,
        "position_size": 0.1,
        "commission": 0.001,
        "risk_free_rate": 0.02
    }
    
    try:
        if os.path.exists('backtest_config.json'):
            with open('backtest_config.json', 'r') as f:
                existing_config = json.load(f)
            
            updated_config = {**default_config, **existing_config}
            
            with open('backtest_config.json', 'w') as f:
                json.dump(updated_config, f, indent=4)
            
            print("✅ backtest_config.json обновлен")
            return updated_config
        else:
            with open('backtest_config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
            print("✅ backtest_config.json создан")
            return default_config
            
    except Exception as e:
        print(f"❌ Ошибка обновления backtest_config.json: {e}")
        return None

def main():
    print("🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ КОНФИГОВ")
    print("=" * 50)
    
    # Исправляем оба конфига
    signal_config = fix_signal_config()
    backtest_config = fix_backtest_config()
    
    print(f"\n📋 РЕЗУЛЬТАТЫ:")
    if signal_config:
        print(f"   ✅ signal_config: {len(signal_config)} параметров")
    else:
        print("   ❌ signal_config: ошибка")
        
    if backtest_config:
        print(f"   ✅ backtest_config: {len(backtest_config)} параметров")
    else:
        print("   ❌ backtest_config: ошибка")
    
    if signal_config and backtest_config:
        print(f"\n🎉 ВСЕ КОНФИГИ ИСПРАВЛЕНЫ!")
        print("   Запускайте тесты снова")
    else:
        print(f"\n⚠️  ЕСТЬ ПРОБЛЕМЫ С КОНФИГАМИ")
        print("   Проверьте права доступа к файлам")

if __name__ == "__main__":
    main()
