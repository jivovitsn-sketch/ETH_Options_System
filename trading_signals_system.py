#!/usr/bin/env python3
import requests
import sqlite3
import time
import json
from datetime import datetime

class TradingSignalsSystem:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/trading_signals.db"
        self.assets = ["BTC", "ETH", "SOL", "XRP"]
        self.init_database()
    
    def init_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_snapshots (
                timestamp INTEGER,
                asset TEXT,
                symbol TEXT,
                strike REAL,
                option_type TEXT,
                open_interest REAL,
                volume_24h REAL,
                spot_price REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                asset TEXT,
                signal_type TEXT,
                strategy TEXT,
                entry_price REAL,
                strike1 REAL,
                strike2 REAL,
                reasoning TEXT
            )
        """)
        
        self.conn.commit()
    
    def collect_snapshot(self, asset):
        timestamp = int(time.time())
        
        try:
            spot_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                       params={"category": "spot", "symbol": f"{asset}USDT"})
            spot_price = float(spot_response.json()["result"]["list"][0]["lastPrice"])
            
            instruments_response = requests.get(f"{self.base_url}/v5/market/instruments-info",
                                              params={"category": "option", "baseCoin": asset})
            
            if instruments_response.status_code != 200:
                return 0
            
            options = instruments_response.json()["result"]["list"]
            collected = 0
            
            for option in options[:100]:  # Ограничиваем для скорости
                symbol = option["symbol"]
                parts = symbol.split("-")
                if len(parts) < 4:
                    continue
                
                try:
                    strike = float(parts[2])
                    option_type = "Call" if parts[3] == "C" else "Put"
                except:
                    continue
                
                distance_pct = abs((strike - spot_price) / spot_price)
                if distance_pct > 0.25:  # В пределах 25% от спота
                    continue
                
                ticker_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                             params={"category": "option", "symbol": symbol})
                
                if ticker_response.status_code == 200:
                    ticker_data = ticker_response.json()
                    if ticker_data["retCode"] == 0 and ticker_data["result"]["list"]:
                        ticker = ticker_data["result"]["list"][0]
                        
                        oi = float(ticker.get("openInterest", 0))
                        volume = float(ticker.get("volume24h", 0))
                        
                        if oi > 10:
                            self.conn.execute("""
                                INSERT OR REPLACE INTO oi_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (timestamp, asset, symbol, strike, option_type, oi, volume, spot_price))
                            collected += 1
                
                time.sleep(0.005)  # Быстрее
            
            self.conn.commit()
            return collected
            
        except Exception as e:
            print(f"Error collecting {asset}: {e}")
            return 0
    
    def analyze_signals(self, asset):
        current_time = int(time.time())
        hour_ago = current_time - 3600
        
        # Получаем изменения OI
        query = """
        SELECT c.symbol, c.strike, c.option_type, c.open_interest as curr_oi, 
               p.open_interest as prev_oi, c.volume_24h, c.spot_price
        FROM oi_snapshots c
        LEFT JOIN oi_snapshots p ON c.symbol = p.symbol AND p.timestamp >= ? AND p.timestamp < ?
        WHERE c.asset = ? AND c.timestamp = (SELECT MAX(timestamp) FROM oi_snapshots WHERE asset = ?)
        AND c.open_interest > 50
        """
        
        results = self.conn.execute(query, (hour_ago, current_time, asset, asset)).fetchall()
        
        signals = []
        spot_price = results[0][6] if results else 0
        
        for row in results:
            symbol, strike, option_type, curr_oi, prev_oi, volume, _ = row
            
            if prev_oi and prev_oi > 0:
                oi_change_pct = ((curr_oi - prev_oi) / prev_oi) * 100
                
                # Сигнал на накопление
                if oi_change_pct > 20 and volume > 5 and curr_oi > 100:
                    distance_pct = ((strike - spot_price) / spot_price) * 100
                    
                    if option_type == "Call" and 0 < distance_pct < 8:
                        signals.append({
                            "asset": asset,
                            "signal_type": "BULLISH_SETUP",
                            "strategy": f"Bull Call Spread ",
                            "entry_price": spot_price,
                            "strike1": spot_price * 0.99,
                            "strike2": strike,
                            "reasoning": f"Call OI +{oi_change_pct:.1f}% at , Vol {volume:.0f}"
                        })
                    
                    elif option_type == "Put" and -8 < distance_pct < 0:
                        signals.append({
                            "asset": asset,
                            "signal_type": "BEARISH_SETUP",
                            "strategy": f"Bear Put Spread ",
                            "entry_price": spot_price,
                            "strike1": strike,
                            "strike2": spot_price * 0.97,
                            "reasoning": f"Put OI +{oi_change_pct:.1f}% at , Vol {volume:.0f}"
                        })
        
        return signals
    
    def run_analysis(self):
        timestamp = int(time.time())
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[{datetime.now().strftime("%H:%M:%S")}] Running analysis...")
        
        all_signals = []
        
        for asset in self.assets:
            print(f"  {asset}:", end=" ")
            collected = self.collect_snapshot(asset)
            print(f"{collected} options", end=" ")
            
            if collected > 0:
                signals = self.analyze_signals(asset)
                print(f"-> {len(signals)} signals")
                
                for signal in signals:
                    print(f"    📈 {signal["strategy"]}: {signal["reasoning"]}")
                    
                    self.conn.execute("""
                        INSERT INTO trading_signals VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (timestamp, date, signal["asset"], signal["signal_type"], 
                          signal["strategy"], signal["entry_price"], signal["strike1"], 
                          signal["strike2"], signal["reasoning"]))
                    
                    all_signals.append(signal)
            else:
                print("-> 0 signals")
        
        self.conn.commit()
        return len(all_signals)
    
    def daemon_mode(self, interval_minutes=20):
        print(f"Daemon mode: checking every {interval_minutes} minutes")
        
        while True:
            try:
                signals_count = self.run_analysis()
                
                if signals_count > 0:
                    print(f"[{datetime.now().strftime("%H:%M:%S")}] Generated {signals_count} signals")
                
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("Stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import sys
    
    system = TradingSignalsSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        system.daemon_mode()
    else:
        signals = system.run_analysis()
        print(f"
Total: {signals} signals generated")
