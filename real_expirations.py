#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REAL EXPIRATIONS - Получение реальных дат экспираций из собранных данных
"""

import sqlite3
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpirationManager:
    def __init__(self):
        self.oi_db = './data/unlimited_oi.db'
        self.expiration_cache = {}

    def get_option_expirations(self, symbol, force_refresh=False):
        """Получить РЕАЛЬНЫЕ даты экспираций из БД"""
        if symbol in self.expiration_cache and not force_refresh:
            return self.expiration_cache[symbol]

        try:
            conn = sqlite3.connect(self.oi_db)
            cursor = conn.cursor()

            # Получаем уникальные экспирации из реальных данных
            cursor.execute("""
                SELECT DISTINCT expiry_date
                FROM all_positions_tracking
                WHERE asset = ? AND expiry_date > date('now')
                ORDER BY expiry_date
                LIMIT 20
            """, (symbol,))

            results = cursor.fetchall()
            conn.close()

            if results:
                expirations = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in results]
                self.expiration_cache[symbol] = expirations
                logger.info(f"✅ {symbol}: Найдено {len(expirations)} реальных экспираций")
                return expirations
            
            # Fallback: генерируем стандартные четверги
            logger.warning(f"⚠️ {symbol}: Нет данных, генерируем четверги")
            return self._generate_thursdays()

        except Exception as e:
            logger.error(f"❌ Ошибка получения экспираций для {symbol}: {e}")
            return self._generate_thursdays()

    def _generate_thursdays(self):
        """Генерация стандартных четвергов (fallback)"""
        current_date = datetime.now().date()
        expirations = []

        for i in range(8):
            days_to_thursday = (3 - datetime.now().weekday()) % 7
            if days_to_thursday == 0:
                days_to_thursday = 7

            expiration = current_date + timedelta(days=days_to_thursday + i*7)
            if expiration > current_date:
                expirations.append(expiration)

        return expirations[:8]

    def get_best_expiration(self, symbol, signal_type, min_days=7, max_days=60):
        """Получить ЛУЧШУЮ экспирацию для стратегии"""
        expirations = self.get_option_expirations(symbol)
        
        current_date = datetime.now().date()
        suitable = []
        
        for exp_date in expirations:
            dte = (exp_date - current_date).days
            
            # Фильтруем по типу сигнала
            if signal_type == "BULLISH" and 30 <= dte <= max_days:
                suitable.append((exp_date, dte))
            elif signal_type == "BEARISH" and min_days <= dte <= 30:
                suitable.append((exp_date, dte))
            elif signal_type == "NEUTRAL" and 21 <= dte <= 45:
                suitable.append((exp_date, dte))
        
        if suitable:
            # Возвращаем первую подходящую
            return suitable[0][1]  # возвращаем DTE
        
        # Fallback: средние значения
        if signal_type == "BULLISH":
            return 45
        elif signal_type == "BEARISH":
            return 14
        else:
            return 30


# Глобальный инстанс
expiration_manager = ExpirationManager()
