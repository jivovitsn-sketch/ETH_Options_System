#!/usr/bin/env python3
"""
🔥 FUTURES DATA MONITOR - Сбор фьючерсных данных
Собирает: цена, объём, OI, Funding Rate, спот, стакан
Активы: BTC, ETH, SOL, XRP, DOGE, MNT
"""
import requests
import sqlite3
import time
from datetime import datetime

class FuturesDataMonitor:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/futures_data.db"
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'MNTUSDT']
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Таблица фьючерсов
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS futures_ticker (
                timestamp INTEGER,
                symbol TEXT,
                last_price REAL,
                volume_24h REAL,
                open_interest REAL,
                funding_rate REAL,
                next_funding_time INTEGER,
                bid_price REAL,
                ask_price REAL,
                spread_pct REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        
        # Таблица спота
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spot_data (
                timestamp INTEGER,
                symbol TEXT,
                last_price REAL,
                volume_24h REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        
        # Таблица ликвидаций (для будущего WebSocket)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS futures_liquidations (
                timestamp INTEGER,
                symbol TEXT,
                side TEXT,
                price REAL,
                quantity REAL,
                value REAL
            )
        """)
        
        self.conn.commit()
        print("✅ База данных futures_data.db инициализирована")
    
    def fetch_futures_ticker(self, symbol):
        """Получение ticker данных фьючерса"""
        try:
            url = f"{self.base_url}/v5/public/tickers"
            params = {'category': 'linear', 'symbol': symbol}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0 and data['result']['list']:
                    return data['result']['list'][0]
        except Exception as e:
            print(f"  ⚠️ Error fetching {symbol} ticker: {e}")
        return None
    
    def fetch_funding_rate(self, symbol):
        """Получение Funding Rate"""
        try:
            url = f"{self.base_url}/v5/public/funding/history"
            params = {'category': 'linear', 'symbol': symbol, 'limit': 1}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0 and data['result']['list']:
                    return data['result']['list'][0]
        except Exception as e:
            print(f"  ⚠️ Error fetching {symbol} funding: {e}")
        return None
    
    def fetch_spot_ticker(self, symbol):
        """Получение спотовых данных"""
        try:
            url = f"{self.base_url}/v5/public/tickers"
            params = {'category': 'spot', 'symbol': symbol}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0 and data['result']['list']:
                    return data['result']['list'][0]
        except Exception as e:
            print(f"  ⚠️ Error fetching {symbol} spot: {e}")
        return None
    
    def run_cycle(self):
        """Основной цикл сбора данных"""
        timestamp = int(datetime.now().timestamp())
        print(f"\n{'='*80}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Futures Data Cycle")
        print(f"{'='*80}")
        
        for symbol in self.symbols:
            try:
                # Фьючерсы
                ticker = self.fetch_futures_ticker(symbol)
                funding = self.fetch_funding_rate(symbol)
                
                if ticker:
                    bid = float(ticker.get('bid1Price', 0))
                    ask = float(ticker.get('ask1Price', 0))
                    last = float(ticker['lastPrice'])
                    spread_pct = ((ask - bid) / last * 100) if last > 0 else 0
                    
                    funding_rate = float(funding['fundingRate']) if funding else 0
                    next_funding = int(funding['fundingRateTimestamp']) if funding else 0
                    
                    self.conn.execute("""
                        INSERT INTO futures_ticker 
                        (timestamp, symbol, last_price, volume_24h, open_interest, 
                         funding_rate, next_funding_time, bid_price, ask_price, spread_pct)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp, symbol, last,
                        float(ticker.get('volume24h', 0)),
                        float(ticker.get('openInterest', 0)),
                        funding_rate, next_funding,
                        bid, ask, spread_pct
                    ))
                    
                    print(f"  ✅ {symbol:8} | ${last:8.2f} | Funding: {funding_rate:+.6f}% | OI: ${float(ticker.get('openInterest', 0))/1e6:.1f}M")
                
                # Спот
                spot = self.fetch_spot_ticker(symbol)
                if spot:
                    self.conn.execute("""
                        INSERT INTO spot_data (timestamp, symbol, last_price, volume_24h)
                        VALUES (?, ?, ?, ?)
                    """, (
                        timestamp, symbol,
                        float(spot['lastPrice']),
                        float(spot.get('volume24h', 0))
                    ))
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error processing {symbol}: {e}")
        
        self.conn.commit()
        print(f"{'='*80}\n")
    
    def run(self):
        """Запуск непрерывного мониторинга"""
        print("🚀 Futures Data Monitor Started")
        print(f"📊 Tracking: {', '.join(self.symbols)}")
        print(f"💾 Database: {self.db_path}")
        print(f"⏰ Update interval: 60 seconds\n")
        
        while True:
            try:
                self.run_cycle()
                time.sleep(60)  # 1 минута между циклами
            except KeyboardInterrupt:
                print("\n🛑 Stopping monitor...")
                self.conn.close()
                break
            except Exception as e:
                print(f"❌ Cycle error: {e}")
                time.sleep(30)

if __name__ == "__main__":
    monitor = FuturesDataMonitor()
    monitor.run()
