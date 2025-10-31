#!/usr/bin/env python3
import requests
import sqlite3
import time
from datetime import datetime

class OrderbookMonitor:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/futures_data.db"
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'MNTUSDT']
        self.init_database()
    
    def init_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS orderbook_snapshots (
                timestamp INTEGER, symbol TEXT,
                bid1_price REAL, bid1_size REAL, bid2_price REAL, bid2_size REAL,
                bid3_price REAL, bid3_size REAL, bid4_price REAL, bid4_size REAL,
                bid5_price REAL, bid5_size REAL,
                ask1_price REAL, ask1_size REAL, ask2_price REAL, ask2_size REAL,
                ask3_price REAL, ask3_size REAL, ask4_price REAL, ask4_size REAL,
                ask5_price REAL, ask5_size REAL,
                spread_bps REAL, mid_price REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_time ON orderbook_snapshots(symbol, timestamp)")
        self.conn.commit()
        print("Database initialized")
    
    def fetch_orderbook(self, symbol):
        try:
            url = self.base_url + "/v5/market/orderbook"
            params = {'category': 'linear', 'symbol': symbol, 'limit': 5}
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('retCode') == 0:
                    return data['result']
        except: pass
        return None
    
    def save_orderbook(self, symbol, ob):
        try:
            bids = ob.get('b', [])
            asks = ob.get('a', [])
            if not bids or not asks:
                return False
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            mid = (best_bid + best_ask) / 2
            spread_bps = ((best_ask - best_bid) / mid) * 10000
            ts = int(datetime.now().timestamp())
            vals = [ts, symbol]
            for i in range(5):
                if i < len(bids):
                    vals.extend([float(bids[i][0]), float(bids[i][1])])
                else:
                    vals.extend([0, 0])
            for i in range(5):
                if i < len(asks):
                    vals.extend([float(asks[i][0]), float(asks[i][1])])
                else:
                    vals.extend([0, 0])
            vals.extend([spread_bps, mid])
            self.conn.execute("INSERT INTO orderbook_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", vals)
            return True
        except:
            return False
    
    def run_cycle(self):
        print("\n" + "="*80)
        print("[%s] Orderbook Monitor" % datetime.now().strftime('%H:%M:%S'))
        print("="*80)
        collected = 0
        for symbol in self.symbols:
            ob = self.fetch_orderbook(symbol)
            if ob and self.save_orderbook(symbol, ob):
                bids = ob.get('b', [])
                asks = ob.get('a', [])
                if bids and asks:
                    best_bid = float(bids[0][0])
                    best_ask = float(asks[0][0])
                    spread = ((best_ask - best_bid) / ((best_bid + best_ask)/2)) * 10000
                    print("  OK %s | Bid: $%.2f | Ask: $%.2f | Spread: %.2fbps" % (symbol, best_bid, best_ask, spread))
                    collected += 1
            time.sleep(0.2)
        self.conn.commit()
        print("="*80)
        print("Collected: %d/%d\n" % (collected, len(self.symbols)))
    
    def run(self):
        print("Orderbook Monitor Started")
        print("Tracking:", ', '.join(self.symbols))
        while True:
            try:
                self.run_cycle()
                time.sleep(30)
            except KeyboardInterrupt:
                self.conn.close()
                break
            except Exception as e:
                print("Error:", e)
                time.sleep(10)

if __name__ == "__main__":
    monitor = OrderbookMonitor()
    monitor.run()
