#!/usr/bin/env python3
import requests
import sqlite3
import time
from datetime import datetime

class OIStrikeAnalyzer:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.init_database()
    
    def init_database(self):
        """Создаем базу для хранения OI истории"""
        self.conn = sqlite3.connect('data/oi_history.db')
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_strikes (
                timestamp INTEGER,
                symbol TEXT,
                strike REAL,
                option_type TEXT,
                open_interest REAL,
                volume_24h REAL,
                bid REAL,
                ask REAL,
                iv REAL,
                delta REAL
            )
        """)
        self.conn.commit()
    
    def collect_eth_oi_data(self):
        """Собираем OI данные по ETH страйкам"""
        
        # Получаем все ETH опционы
        response = requests.get(f"{self.base_url}/v5/market/instruments-info",
                               params={'category': 'option', 'baseCoin': 'ETH'})
        
        if response.status_code != 200:
            return
        
        options = response.json()['result']['list']
        timestamp = int(time.time())
        
        print(f"Собираем OI для {len(options)} ETH опционов...")
        
        for opt in options:
            symbol = opt['symbol']
            
            # Получаем тикер данные
            ticker_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                         params={'category': 'option', 'symbol': symbol})
            
            if ticker_response.status_code == 200:
                ticker_data = ticker_response.json()
                if ticker_data['retCode'] == 0 and ticker_data['result']['list']:
                    ticker = ticker_data['result']['list'][0]
                    
                    # Парсим страйк из символа
                    parts = symbol.split('-')
                    if len(parts) >= 4:
                        strike = float(parts[2])
                        option_type = 'Call' if parts[3] == 'C' else 'Put'
                        
                        # Сохраняем в базу
                        self.conn.execute("""
                            INSERT INTO oi_strikes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            timestamp,
                            symbol,
                            strike,
                            option_type,
                            float(ticker.get('openInterest', 0)),
                            float(ticker.get('volume24h', 0)),
                            float(ticker.get('bid1Price', 0)),
                            float(ticker.get('ask1Price', 0)),
                            float(ticker.get('markIv', 0)),
                            float(ticker.get('delta', 0))
                        ))
            
            time.sleep(0.05)  # Не спамим API
        
        self.conn.commit()
        print(f"OI данные сохранены: {timestamp}")
    
    def analyze_oi_changes(self):
        """Анализ изменений OI для поиска стенок и накоплений"""
        
        cursor = self.conn.execute("""
            SELECT strike, option_type, open_interest, timestamp
            FROM oi_strikes 
            WHERE symbol LIKE 'ETH-%'
            ORDER BY timestamp DESC, strike
        """)
        
        # Здесь будет логика анализа изменений OI
        print("Анализ изменений OI...")

if __name__ == "__main__":
    analyzer = OIStrikeAnalyzer()
    analyzer.collect_eth_oi_data()
