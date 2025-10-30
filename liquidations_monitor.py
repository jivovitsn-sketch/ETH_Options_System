#!/usr/bin/env python3
"""
🔥 LIQUIDATIONS MONITOR - Real-time мониторинг ликвидаций
"""
import websocket
import json
import sqlite3
import time
import threading
from datetime import datetime

class LiquidationsMonitor:
    def __init__(self):
        self.db_path = "data/futures_data.db"
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'MNTUSDT']
        self.ws_url = "wss://stream.bybit.com/v5/public/linear"
        self.ws = None
        self.conn = None
        self.running = True
        self.liquidations_count = {symbol: 0 for symbol in self.symbols}
        self.init_database()
    
    def init_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS liquidations (
                timestamp INTEGER, symbol TEXT, side TEXT,
                price REAL, quantity REAL, value REAL
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_liquidations_symbol_time 
            ON liquidations(symbol, timestamp)
        """)
        self.conn.commit()
        print("Database initialized")
    
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if 'topic' in data and 'liquidation' in data['topic']:
                self.handle_liquidation(data)
        except Exception as e:
            print("Error:", e)
    
    def handle_liquidation(self, data):
        try:
            topic = data['topic']
            symbol = topic.split('.')[1]
            liq_data = data['data']
            timestamp = int(datetime.now().timestamp())
            side = liq_data.get('side', 'Unknown')
            price = float(liq_data.get('price', 0))
            quantity = float(liq_data.get('size', 0))
            value = price * quantity
            
            self.conn.execute("""
                INSERT INTO liquidations 
                (timestamp, symbol, side, price, quantity, value)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, symbol, side, price, quantity, value))
            self.conn.commit()
            
            self.liquidations_count[symbol] = self.liquidations_count.get(symbol, 0) + 1
            
            if value > 10000:
                print("LARGE LIQUIDATION: %s %s $%.0f @ $%.2f" % (symbol, side, value, price))
        except Exception as e:
            print("Error:", e)
    
    def on_error(self, ws, error):
        print("WS error:", error)
    
    def on_close(self, ws, close_status_code, close_msg):
        print("WS closed - reconnecting...")
        if self.running:
            time.sleep(5)
            self.connect()
    
    def on_open(self, ws):
        print("WS connected")
        for symbol in self.symbols:
            ws.send(json.dumps({"op": "subscribe", "args": ["liquidation.%s" % symbol]}))
            print("  Subscribed to", symbol)
    
    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
    
    def print_stats(self):
        while self.running:
            time.sleep(300)
            print("\n" + "="*80)
            print("[%s] Liquidations Stats" % datetime.now().strftime('%H:%M:%S'))
            print("="*80)
            total = 0
            for symbol, count in sorted(self.liquidations_count.items()):
                print("  %s | %d liquidations" % (symbol, count))
                total += count
            print("Total: %d\n" % total)
    
    def run(self):
        print("Liquidations Monitor Started")
        print("Tracking:", ', '.join(self.symbols))
        self.connect()
        stats_thread = threading.Thread(target=self.print_stats)
        stats_thread.daemon = True
        stats_thread.start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            self.running = False
            if self.ws:
                self.ws.close()
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    monitor = LiquidationsMonitor()
    monitor.run()
