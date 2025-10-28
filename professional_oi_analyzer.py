#!/usr/bin/env python3
import requests
import sqlite3
import time
import json
import os
from datetime import datetime

class ProfessionalOIAnalyzer:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/professional_oi.db"
        self.assets = ['BTC', 'ETH', 'SOL', 'XRP']
        
        self.analysis_config = {
            'accumulation_threshold': 0.20,
            'breakdown_threshold': -0.25,
            'volume_confirmation': 5,
            'min_oi_significance': 50,
            'wall_threshold': 200,
            'distance_filter': 0.15,
            'lookback_hours': 2,
        }
        
        self.init_database()
    
    def init_database(self):
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_tracking (
                timestamp INTEGER,
                asset TEXT,
                symbol TEXT,
                expiry TEXT,
                strike REAL,
                option_type TEXT,
                open_interest REAL,
                volume_24h REAL,
                implied_vol REAL,
                spot_price REAL,
                distance_pct REAL,
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
                confidence REAL,
                strike1 REAL,
                strike2 REAL,
                reasoning TEXT
            )
        """)
        
        self.conn.commit()
        print(f"Database initialized: {self.db_path}")
    
    def get_spot_price(self, asset):
        try:
            response = requests.get(f"{self.base_url}/v5/market/tickers",
                                  params={'category': 'spot', 'symbol': f'{asset}USDT'})
            if response.status_code == 200:
                return float(response.json()['result']['list'][0]['lastPrice'])
        except Exception as e:
            print(f"Error getting {asset} spot: {e}")
        return None
    
    def collect_options_data(self, asset):
        timestamp = int(time.time())
        spot_price = self.get_spot_price(asset)
        if not spot_price:
            return 0
        
        try:
            response = requests.get(f"{self.base_url}/v5/market/instruments-info",
                                  params={'category': 'option', 'baseCoin': asset})
            
            if response.status_code != 200:
                return 0
            
            options = response.json()['result']['list']
            collected = 0
            
            for option in options:
                symbol = option['symbol']
                parts = symbol.split('-')
                if len(parts) < 4:
                    continue
                
                try:
                    expiry = parts[1]
                    strike = float(parts[2])
                    option_type = 'Call' if parts[3] == 'C' else 'Put'
                except:
                    continue
                
                distance_pct = abs((strike - spot_price) / spot_price)
                if distance_pct > self.analysis_config['distance_filter']:
                    continue
                
                ticker_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                             params={'category': 'option', 'symbol': symbol})
                
                if ticker_response.status_code == 200:
                    ticker_data = ticker_response.json()
                    if ticker_data['retCode'] == 0 and ticker_data['result']['list']:
                        ticker = ticker_data['result']['list'][0]
                        
                        oi = float(ticker.get('openInterest', 0))
                        volume = float(ticker.get('volume24h', 0))
                        iv = float(ticker.get('markIv', 0))
                        
                        if oi >= self.analysis_config['min_oi_significance']:
                            self.conn.execute("""
                                INSERT OR REPLACE INTO oi_tracking VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (timestamp, asset, symbol, expiry, strike, option_type, 
                                  oi, volume, iv, spot_price, distance_pct))
                            collected += 1
                
                time.sleep(0.01)
            
            self.conn.commit()
            return collected
            
        except Exception as e:
            print(f"Error collecting {asset}: {e}")
            return 0
    
    def analyze_signals(self, asset):
        current_time = int(time.time())
        lookback_time = current_time - (self.analysis_config['lookback_hours'] * 3600)
        
        current_query = """
            SELECT symbol, strike, option_type, open_interest, volume_24h, spot_price, expiry
            FROM oi_tracking 
            WHERE asset = ? AND timestamp = (SELECT MAX(timestamp) FROM oi_tracking WHERE asset = ?)
        """
        
        historical_query = """
            SELECT symbol, strike, option_type, open_interest, volume_24h
            FROM oi_tracking 
            WHERE asset = ? AND timestamp >= ? AND timestamp < ?
            ORDER BY timestamp DESC
        """
        
        current_data = {row[0]: row for row in self.conn.execute(current_query, (asset, asset)).fetchall()}
        historical_data = {}
        
        for row in self.conn.execute(historical_query, (asset, lookback_time, current_time)).fetchall():
            symbol = row[0]
            if symbol not in historical_data:
                historical_data[symbol] = row
        
        signals = []
        
        if not current_data:
            return signals
        
        spot_price = list(current_data.values())[0][5]
        
        for symbol, current in current_data.items():
            if symbol not in historical_data:
                continue
            
            historical = historical_data[symbol]
            
            curr_oi = current[3]
            hist_oi = historical[3]
            curr_vol = current[4]
            strike = current[1]
            option_type = current[2]
            expiry = current[6]
            
            if hist_oi == 0:
                continue
            
            oi_change_pct = (curr_oi - hist_oi) / hist_oi
            distance_from_spot = (strike - spot_price) / spot_price
            
            # Accumulation signals
            if (oi_change_pct >= self.analysis_config['accumulation_threshold'] and
                curr_vol >= self.analysis_config['volume_confirmation']):
                
                if option_type == 'Call' and 0.02 < distance_from_spot < 0.08:
                    # Bull Call Spread
                    long_strike = spot_price * 1.01
                    short_strike = strike
                    
                    signal = {
                        'asset': asset,
                        'signal_type': 'BULLISH_ACCUMULATION',
                        'strategy': 'Bull Call Spread',
                        'confidence': min(oi_change_pct * 2, 1.0),
                        'strike1': long_strike,
                        'strike2': short_strike,
                        'expiry': expiry,
                        'spot_price': spot_price,
                        'reasoning': f"Call OI +{oi_change_pct*100:.1f}% at ${strike:.0f}, Vol {curr_vol:.0f}"
                    }
                    signals.append(signal)
                
                elif option_type == 'Put' and -0.08 < distance_from_spot < -0.02:
                    # Bear Put Spread
                    long_strike = strike
                    short_strike = spot_price * 0.97
                    
                    signal = {
                        'asset': asset,
                        'signal_type': 'BEARISH_ACCUMULATION',
                        'strategy': 'Bear Put Spread',
                        'confidence': min(oi_change_pct * 2, 1.0),
                        'strike1': long_strike,
                        'strike2': short_strike,
                        'expiry': expiry,
                        'spot_price': spot_price,
                        'reasoning': f"Put OI +{oi_change_pct*100:.1f}% at ${strike:.0f}, Vol {curr_vol:.0f}"
                    }
                    signals.append(signal)
        
        return signals
    
    def format_signal(self, signal):
        entry_low = signal['spot_price'] * 0.999
        entry_high = signal['spot_price'] * 1.001
        
        if signal['signal_type'] == 'BULLISH_ACCUMULATION':
            tp1 = signal['strike2'] * 1.02
            tp2 = signal['strike2'] * 1.04
            tp3 = signal['strike2'] * 1.06
            sl = signal['spot_price'] * 0.985
        else:
            tp1 = signal['strike1'] * 0.98
            tp2 = signal['strike1'] * 0.96
            tp3 = signal['strike1'] * 0.94
            sl = signal['spot_price'] * 1.015
        
        confidence_emoji = "🔥" if signal['confidence'] > 0.6 else "⚡" if signal['confidence'] > 0.3 else "📊"
        
        return f"""
{confidence_emoji} {signal['asset']} SIGNAL

Strategy: {signal['strategy']}
Confidence: {signal['confidence']*100:.1f}%

Entry: ${entry_low:.0f} - ${entry_high:.0f}
Current: ${signal['spot_price']:.0f}

Targets:
🎯 TP1: ${tp1:.0f}
🎯 TP2: ${tp2:.0f}
🎯 TP3: ${tp3:.0f}
🛑 SL: ${sl:.0f}

Strikes: ${signal['strike1']:.0f} / ${signal['strike2']:.0f}
Expiry: {signal['expiry']}

Analysis: {signal['reasoning']}
        """.strip()
    
    def run_analysis(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running OI analysis...")
        
        total_signals = 0
        
        for asset in self.assets:
            collected = self.collect_options_data(asset)
            print(f"  {asset}: {collected} options collected")
            
            if collected > 0:
                signals = self.analyze_signals(asset)
                
                for signal in signals:
                    timestamp = int(time.time())
                    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.conn.execute("""
                        INSERT INTO trading_signals VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (timestamp, date, signal['asset'], signal['signal_type'], 
                          signal['strategy'], signal['confidence'], signal['strike1'], 
                          signal['strike2'], signal['reasoning']))
                    
                    print(self.format_signal(signal))
                    print("-" * 50)
                    total_signals += 1
        
        self.conn.commit()
        return total_signals
    
    def daemon_mode(self, interval_minutes=20):
        print(f"Starting daemon mode (every {interval_minutes} minutes)")
        
        while True:
            try:
                signals = self.run_analysis()
                
                if signals > 0:
                    print(f"Generated {signals} signals")
                else:
                    print("No signals detected")
                
                print(f"Next analysis in {interval_minutes} minutes...\n")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("Daemon stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import sys
    
    analyzer = ProfessionalOIAnalyzer()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'daemon':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        analyzer.daemon_mode(interval)
    else:
        signals = analyzer.run_analysis()
        print(f"\nTotal signals: {signals}")
