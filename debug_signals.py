#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_signal_sources():
    print("🔍 ПРОВЕРКА ИСТОЧНИКОВ ДАННЫХ ДЛЯ СИГНАЛОВ:")
    
    # Проверяем наличие данных OI dynamics
    oi_dynamics_dir = "data/oi_dynamics"
    if os.path.exists(oi_dynamics_dir):
        oi_files = os.listdir(oi_dynamics_dir)
        print(f"✅ OI Dynamics файлов: {len(oi_files)}")
        if oi_files:
            latest_oi = sorted(oi_files)[-1]
            print(f"   Последний файл: {latest_oi}")
    else:
        print("❌ Нет данных OI Dynamics")
    
    # Проверяем наличие данных expiration walls
    walls_dir = "data/expiration_walls"
    if os.path.exists(walls_dir):
        wall_files = os.listdir(walls_dir)
        print(f"✅ Expiration Walls файлов: {len(wall_files)}")
        if wall_files:
            latest_wall = sorted(wall_files)[-1]
            print(f"   Последний файл: {latest_wall}")
    else:
        print("❌ Нет данных Expiration Walls")
    
    # Проверяем наличие других данных
    data_sources = [
        "data/futures_data.db",
        "data/liquidations.db", 
        "data/funding_rates.db"
    ]
    
    for source in data_sources:
        if os.path.exists(source):
            size = os.path.getsize(source)
            print(f"✅ {source}: {size} байт")
        else:
            print(f"❌ {source}: не найден")

if __name__ == "__main__":
    check_signal_sources()
    
    print("\n🎯 РЕКОМЕНДАЦИИ:")
    print("1. Если нет данных - проверьте работу futures_data_monitor.py")
    print("2. Если данные есть, но сигналов нет - проверьте advanced_signals_generator.py")
    print("3. Для отладки запустите: python3 advanced_signals_generator.py")
