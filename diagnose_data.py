#!/usr/bin/env python3
"""
Диагностика данных системы - показывает что реально доступно
"""

import os
import glob
import json
from datetime import datetime

def analyze_directory(directory, name):
    """Проанализировать директорию с данными"""
    if not os.path.exists(directory):
        return {"name": name, "status": "MISSING", "files": 0, "assets": []}
    
    files = glob.glob(f"{directory}/*.json")
    assets = set()
    
    for file in files:
        filename = os.path.basename(file)
        parts = filename.split('_')
        if len(parts) >= 2:
            assets.add(parts[0])
    
    return {
        "name": name,
        "status": "ACTIVE" if files else "EMPTY",
        "files": len(files),
        "assets": sorted(list(assets)),
        "latest_files": files[:3]  # Показать несколько примеров
    }

def main():
    print("🔍 ДИАГНОСТИКА ДАННЫХ СИСТЕМЫ")
    print("=" * 60)
    
    directories = {
        'funding_rate': 'data/funding_rate',
        'liquidations': 'data/liquidations',
        'futures_oi': 'data/futures_oi',
        'pcr': 'data/pcr',
        'oi': 'data/oi',
        'max_pain': 'data/max_pain',
        'gamma_exposure': 'data/gamma_exposure',
        'vanna': 'data/vanna',
        'iv_rank': 'data/iv_rank',
        'volatility_greeks': 'data/volatility_greeks'
    }
    
    results = []
    for name, path in directories.items():
        result = analyze_directory(path, name)
        results.append(result)
    
    # Выводим результаты
    print("\n📊 СТАТУС ИНДИКАТОРОВ:")
    for result in results:
        status_icon = "✅" if result['status'] == 'ACTIVE' else "❌" if result['status'] == 'MISSING' else "⚠️"
        print(f"   {status_icon} {result['name']:20} - {result['files']:3d} файлов, активы: {result['assets'][:3]}{'...' if len(result['assets']) > 3 else ''}")
    
    # Анализ по активам
    print(f"\n🎯 ОБЗОР ПО АКТИВАМ:")
    all_assets = set()
    for result in results:
        if result['assets']:
            all_assets.update(result['assets'])
    
    for asset in sorted(all_assets):
        asset_indicators = []
        for result in results:
            if asset in result['assets']:
                asset_indicators.append(result['name'])
        
        print(f"   📈 {asset}: {len(asset_indicators)} индикаторов - {', '.join(asset_indicators[:3])}{'...' if len(asset_indicators) > 3 else ''}")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    
    active_indicators = [r for r in results if r['status'] == 'ACTIVE']
    if len(active_indicators) >= 5:
        print("   ✅ Хорошее покрытие данных! Можно начинать интеграцию.")
    else:
        print("   ⚠️  Мало активных индикаторов. Нужно настроить сбор данных.")
    
    # Проверяем конкретно для Stage 1.4
    critical_indicators = ['pcr', 'gamma_exposure', 'max_pain', 'vanna']
    available_critical = [r for r in results if r['name'] in critical_indicators and r['status'] == 'ACTIVE']
    
    print(f"   🎯 Для Stage 1.4 доступно {len(available_critical)}/{len(critical_indicators)} критических индикаторов")
    
    if len(available_critical) >= 2:
        print("   ✅ Достаточно данных для начала Stage 1.4!")
    else:
        print("   ❌ Нужно настроить больше индикаторов перед Stage 1.4")

if __name__ == "__main__":
    main()
