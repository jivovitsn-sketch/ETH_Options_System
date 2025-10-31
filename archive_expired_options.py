#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""АРХИВАЦИЯ EXPIRED ОПЦИОНОВ - ГОРЯЧЕЕ/ХОЛОДНОЕ ХРАНИЛИЩЕ"""

import sqlite3, logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

HOT_DB = 'data/unlimited_oi.db'
COLD_DB = 'data/archive/unlimited_oi_archive.db'

def archive_expired_options():
    """Перемещает истекшие опционы (dte <= 0) в архив для бэктестов"""
    
    Path('data/archive').mkdir(parents=True, exist_ok=True)
    
    # Подключаемся к горячей БД
    hot_conn = sqlite3.connect(HOT_DB)
    hot_cursor = hot_conn.cursor()
    
    # Подключаемся к холодной БД
    cold_conn = sqlite3.connect(COLD_DB)
    cold_cursor = cold_conn.cursor()
    
    # Создаем таблицу архива (если нет)
    cold_cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_positions_tracking_archive (
            timestamp INTEGER, asset TEXT, symbol TEXT, expiry TEXT, expiry_date DATE,
            dte INTEGER, strike REAL, option_type TEXT, open_interest REAL,
            volume_24h REAL, spot_price REAL, distance_pct REAL, time_category TEXT,
            archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Найти все expired опционы
    hot_cursor.execute("SELECT * FROM all_positions_tracking WHERE dte <= 0")
    expired_rows = hot_cursor.fetchall()
    
    if expired_rows:
        logger.info(f"📦 Found {len(expired_rows)} expired options to archive")
        
        # Копируем в архив
        cold_cursor.executemany("""
            INSERT INTO all_positions_tracking_archive 
            (timestamp, asset, symbol, expiry, expiry_date, dte, strike, option_type,
             open_interest, volume_24h, spot_price, distance_pct, time_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, expired_rows)
        
        # Удаляем из горячей БД
        hot_cursor.execute("DELETE FROM all_positions_tracking WHERE dte <= 0")
        
        hot_conn.commit()
        cold_conn.commit()
        
        logger.info(f"✅ Archived {len(expired_rows)} expired options")
        logger.info(f"   HOT DB: {HOT_DB}")
        logger.info(f"   COLD DB (backtest): {COLD_DB}")
    else:
        logger.info("✅ No expired options to archive")
    
    hot_conn.close()
    cold_conn.close()

if __name__ == "__main__":
    print("="*80)
    print("📦 ARCHIVE EXPIRED OPTIONS")
    print("="*80 + "\n")
    archive_expired_options()
    print("\n" + "="*80)
    print("✅ ARCHIVING COMPLETE!")
    print("="*80)
