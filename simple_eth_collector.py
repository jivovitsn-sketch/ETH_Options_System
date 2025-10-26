#!/usr/bin/env python3
"""
УПРОЩЕННЫЙ ETH COLLECTOR - гарантированно работает
"""
import requests
import json
import sqlite3
from datetime import datetime

def test_deribit_connection():
    """Тест подключения к Deribit"""
    try:
        url = "https://www.deribit.com/api/v2/public/get_instruments"
        params = {'currency': 'ETH', 'kind': 'option', 'expired': 'false'}
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            instruments = data['result']
            print(f"✅ Deribit connected: {len(instruments)} instruments")
            
            # Показываем примеры
            for i, inst in enumerate(instruments[:5]):
                print(f"  {inst['instrument_name']}")
            
            return instruments
        else:
            print(f"❌ Deribit error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    return []

def create_simple_database():
    """Создание простой базы"""
    conn = sqlite3.connect('data/eth_options_simple.db')
    cursor = conn.cursor()
    
    cursor.execute('''DROP TABLE IF EXISTS options''')
    cursor.execute('''
        CREATE TABLE options (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            instrument TEXT,
            strike REAL,
            expiry TEXT,
            type TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Simple database created")

def collect_and_save():
    """Сбор и сохранение данных"""
    instruments = test_deribit_connection()
    
    if not instruments:
        print("❌ No data to save")
        return
    
    create_simple_database()
    
    conn = sqlite3.connect('data/eth_options_simple.db')
    cursor = conn.cursor()
    
    saved = 0
    
    for inst in instruments[:50]:  # Первые 50 для теста
        try:
            name = inst['instrument_name']
            # Парсим ETH-29NOV24-3200-C
            parts = name.split('-')
            if len(parts) == 4:
                strike = float(parts[2])
                expiry = parts[1]
                opt_type = 'CALL' if parts[3] == 'C' else 'PUT'
                
                cursor.execute('''
                    INSERT INTO options (timestamp, instrument, strike, expiry, type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), name, strike, expiry, opt_type))
                
                saved += 1
        
        except Exception as e:
            print(f"Error saving {inst.get('instrument_name', 'unknown')}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Saved {saved} options to database")
    return saved

if __name__ == "__main__":
    result = collect_and_save()
    
    # Проверяем что сохранилось
    conn = sqlite3.connect('data/eth_options_simple.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM options')
    count = cursor.fetchone()[0]
    print(f"Final count in DB: {count}")
    
    if count > 0:
        cursor.execute('SELECT instrument, strike, type FROM options LIMIT 5')
        samples = cursor.fetchall()
        print("Sample data:")
        for row in samples:
            print(f"  {row[0]}: ${row[1]} {row[2]}")
    
    conn.close()
