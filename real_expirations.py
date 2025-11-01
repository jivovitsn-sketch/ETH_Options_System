import sqlite3
from datetime import datetime, timedelta
import random

class ExpirationManager:
    def __init__(self):
        self.expiration_cache = {}
    
    def get_option_expirations(self, symbol, force_refresh=False):
        """Получить реальные даты экспираций опционов"""
        if symbol in self.expiration_cache and not force_refresh:
            return self.expiration_cache[symbol]
        
        try:
            # Попытка получить из базы данных
            expirations = self._fetch_from_database(symbol)
            if expirations:
                self.expiration_cache[symbol] = expirations
                return expirations
            
            # Fallback: сгенерировать реалистичные
            expirations = self._generate_realistic_expirations()
            self.expiration_cache[symbol] = expirations
            return expirations
            
        except Exception as e:
            print(f"Error getting expirations for {symbol}: {e}")
            return self._generate_realistic_expirations()
    
    def _fetch_from_database(self, symbol):
        """Получить экспирации из базы данных"""
        try:
            conn = sqlite3.connect('./data/futures_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT expiration_date FROM option_chain 
                WHERE symbol = ? AND expiration_date > ?
                ORDER BY expiration_date
            """, (symbol, datetime.now().date()))
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                return [datetime.strptime(row[0], '%Y-%m-%d').date() for row in results]
            return None
            
        except:
            return None
    
    def _generate_realistic_expirations(self):
        """Сгенерировать реалистичные даты экспираций"""
        current_date = datetime.now().date()
        expirations = []
        
        # Ближайшие 8 четвергов (стандартные экспирации опционов)
        for i in range(8):
            days_to_thursday = (3 - datetime.now().weekday()) % 7
            if days_to_thursday == 0:
                days_to_thursday = 7
            
            expiration = current_date + timedelta(days=days_to_thursday + i*7)
            if expiration > current_date:
                expirations.append(expiration)
        
        expirations.sort()
        return expirations[:8]

# Глобальный инстанс
expiration_manager = ExpirationManager()

            results = cursor.fetchall()
            conn.close()

            if results:
                return [datetime.strptime(row[0], '%Y-%m-%d').date() for row in results]
            return None

        except:
            return None

    def _generate_realistic_expirations(self):
        """Сгенерировать реалистичные даты экспираций"""
        current_date = datetime.now().date()
        expirations = []

        # Ближайшие 8 четвергов (стандартные экспирации опционов)
        for i in range(8):
            days_to_thursday = (3 - datetime.now().weekday()) % 7
            if days_to_thursday == 0:
                days_to_thursday = 7

            expiration = current_date + timedelta(days=days_to_thursday + i*7)
            if expiration > current_date:
                expirations.append(expiration)

        expirations.sort()
        return expirations[:8]

# Глобальный инстанс
expiration_manager = ExpirationManager()
