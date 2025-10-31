#!/usr/bin/env python3
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
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS futures_ticker (
                timestamp INTEGER, symbol TEXT, last_price REAL,
                volume_24h REAL, open_interest REAL, funding_rate REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spot_data (
                timestamp INTEGER, symbol TEXT, last_price REAL,
                volume_24h REAL, PRIMARY KEY (timestamp, symbol)
            )
        """)
        self.conn.commit()
        print("Database initialized")
    
    def fetch_ticker(self, symbol, category='linear'):
        try:
            url = self.base_url + "/v5/market/tickers"
            params = {'category': category, 'symbol': symbol}
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('retCode') == 0:
                    return data['result']['list'][0]
        except: pass
        return None
    
    def fetch_funding(self, symbol):
        try:
            url = self.base_url + "/v5/market/funding/history"
            params = {'category': 'linear', 'symbol': symbol, 'limit': 1}
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('retCode') == 0 and data['result']['list']:
                    return float(data['result']['list'][0]['fundingRate'])
        except: pass
        return 0
    
    def run_cycle(self):
        ts = int(datetime.now().timestamp())
        print("\n" + "="*80)
        print(datetime.now().strftime('[%H:%M:%S] Futures + Spot'))
        print("="*80)
        
        for symbol in self.symbols:
            ticker = self.fetch_ticker(symbol, 'linear')
            if ticker:
                funding = self.fetch_funding(symbol)
                price = float(ticker['lastPrice'])
                vol = float(ticker.get('volume24h', 0))
                oi = float(ticker.get('openInterest', 0))
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO futures_ticker 
                    (timestamp, symbol, last_price, volume_24h, open_interest, funding_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ts, symbol, price, vol, oi, funding))
                
                spot_ticker = self.fetch_ticker(symbol, 'spot')
                if spot_ticker:
                    spot_price = float(spot_ticker['lastPrice'])
                    spot_vol = float(spot_ticker.get('volume24h', 0))
                    
                    self.conn.execute("""
                        INSERT OR REPLACE INTO spot_data 
                        (timestamp, symbol, last_price, volume_24h)
                        VALUES (?, ?, ?, ?)
                    """, (ts, symbol, spot_price, spot_vol))
                    
                    basis = price - spot_price
                    basis_pct = (basis / spot_price) * 100 if spot_price > 0 else 0
                    
                    print("  %s | Fut: $%.2f | Spot: $%.2f | Basis: %+.2f%%" % 
                          (symbol, price, spot_price, basis_pct))
            time.sleep(0.2)
        
        self.conn.commit()
        print("="*80 + "\n")
    
    def run(self):
        print("Futures + Spot Monitor Started")
        while True:
            try:
                self.run_cycle()
                time.sleep(60)
            except KeyboardInterrupt:
                self.conn.close()
                break
            except Exception as e:
                print("Error:", e)
                time.sleep(30)

if __name__ == "__main__":
    monitor = FuturesDataMonitor()
    monitor.run()
