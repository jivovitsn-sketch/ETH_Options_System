#!/usr/bin/env python3
import json
import os
from datetime import datetime

def analyze_signal_components():
    print("🔧 КОМПОНЕНТЫ СИГНАЛЬНОЙ СИСТЕМЫ:")
    print("")
    
    # 1. OI Dynamics Analysis
    print("1. 📈 OI DYNAMICS ANALYSIS:")
    oi_files = os.listdir("data/oi_dynamics") if os.path.exists("data/oi_dynamics") else []
    if oi_files:
        latest_oi = sorted(oi_files)[-1]
        print(f"   • Последний файл: {latest_oi}")
        with open(f"data/oi_dynamics/{latest_oi}", 'r') as f:
            oi_data = json.load(f)
        print(f"   • Тренд: {oi_data.get('trend_direction', 'N/A')}")
        print(f"   • Сила: {oi_data.get('trend_strength', 'N/A')}")
        print(f"   • Изменение OI: {oi_data.get('oi_change_24h', 'N/A')}%")
    else:
        print("   • ❌ Нет данных OI")
    
    # 2. Expiration Walls Analysis
    print("")
    print("2. 🧱 EXPIRATION WALLS ANALYSIS:")
    wall_files = os.listdir("data/expiration_walls") if os.path.exists("data/expiration_walls") else []
    if wall_files:
        latest_wall = sorted(wall_files)[-1]
        print(f"   • Последний файл: {latest_wall}")
        with open(f"data/expiration_walls/{latest_wall}", 'r') as f:
            wall_data = json.load(f)
        print(f"   • Call Wall: ${wall_data.get('call_wall', 'N/A')}")
        print(f"   • Put Wall: ${wall_data.get('put_wall', 'N/A')}")
        print(f"   • Max Pain: ${wall_data.get('max_pain', 'N/A')}")
    else:
        print("   • ❌ Нет данных стен")
    
    # 3. Signal Confidence Calculation
    print("")
    print("3. 🎯 CONFIDENCE CALCULATION:")
    print("   • OI Trend Weight: 40%")
    print("   • Walls Analysis Weight: 35%") 
    print("   • Volume Analysis Weight: 25%")
    print("   • Минимальный порог: 60%")
    print("   • Сильный сигнал: >75%")
    
    # 4. Signal Types
    print("")
    print("4. 📊 ТИПЫ СИГНАЛОВ:")
    print("   • BULLISH > 60% - Бычий сигнал")
    print("   • BEARISH > 60% - Медвежий сигнал") 
    print("   • STRONG_BULLISH > 75% - Сильный бычий")
    print("   • STRONG_BEARISH > 75% - Сильный медвежий")
    print("   • NO_SIGNAL < 60% - Нет сигнала")

if __name__ == "__main__":
    analyze_signal_components()
