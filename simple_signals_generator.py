#!/usr/bin/env python3
"""МИНИМАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ СИГНАЛОВ"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def simple_signal_generator():
    print("🚀 ЗАПУСК ПРОСТОЙ ВЕРСИИ СИГНАЛОВ")
    
    symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
    
    for symbol in symbols:
        try:
            # Просто проверяем доступность данных
            conn = sqlite3.connect('data/futures_data.db')
            price_df = pd.read_sql_query(
                "SELECT last_price FROM spot_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", 
                conn, params=(f"{symbol}USDT",)
            )
            conn.close()
            
            if not price_df.empty:
                price = float(price_df.iloc[0]['last_price'])
                print(f"✅ {symbol}: ${price:.2f} - ДАННЫЕ ДОСТУПНЫ")
            else:
                print(f"❌ {symbol}: НЕТ ДАННЫХ")
                
        except Exception as e:
            print(f"❌ {symbol}: ОШИБКА - {e}")

if __name__ == "__main__":
    simple_signal_generator()
