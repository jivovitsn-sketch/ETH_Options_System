#!/usr/bin/env python3
import requests
import sqlite3
import time
import json
from datetime import datetime

class OISignalsSystem:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/oi_signals.db"
        self.assets = ['BTC', 'ETH', 'SOL', 'XRP']
        self.init_database()
        
        # КОНКРЕТНЫЕ ПРАВИЛА СИГНАЛОВ
        self.signal_rules = {
            'accumulation': {
                'min_oi_increase_pct': 30,  # 30%+ рост OI = накопление
                'min_volume_confirmation': 20,  # Минимальный объем
                'min_total_oi': 100  # Минимальный абсолютный OI
            },
            'breakdown': {
                'min_oi_decrease_pct': -25,  # 25%+ падение OI = разбор
                'min_volume_confirmation': 15,
                'min_previous_oi': 200  # Было крупно, стало меньше
            },
            'vol_spike': {
                'min_iv_increase_pct': 20,  # 20%+ рост IV
                'min_oi_for_vol_signal': 100
            }
        }
    
    def init_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_data (
                timestamp INTEGER,
                asset TEXT,
                symbol TEXT,
                strike REAL,
                option_type TEXT,
                open_interest REAL,
                volume_24h REAL,
                implied_vol REAL,
                spot_price REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                asset TEXT,
                signal_type TEXT,
                symbol TEXT,
                strike REAL,
                option_type TEXT,
                signal_strength REAL,
                message TEXT
            )
        """)
        
        self.conn.commit()
    
    def send_telegram_alert(self, message):
        """Отправка в Telegram"""
        try:
            with open('config/telegram.json', 'r') as f:
                config = json.load(f)
                bot_token = config.get('bot_token')
                chat_id = config.get('chat_id')
                
                if bot_token and chat_id:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = {'chat_id': chat_id, 'text': message}
                    requests.post(url, data=data)
        except:
            pass
    
    def collect_data(self, asset):
        """Быстрый сбор данных по активу"""
        timestamp = int(time.time())
        
        try:
            # Спот цена
            spot_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                       params={'category': 'spot', 'symbol': f'{asset}USDT'})
            spot_price = float(spot_response.json()['result']['list'][0]['lastPrice'])
            
            # Опционы
            instruments_response = requests.get(f"{self.base_url}/v5/market/instruments-info",
                                              params={'category': 'option', 'baseCoin': asset})
            
            if instruments_response.status_code != 200:
                return 0
            
            options = instruments_response.json()['result']['list']
            collected = 0
            
            for option in options[:50]:  # Ограничиваем для скорости
                symbol = option['symbol']
                parts = symbol.split('-')
                if len(parts) < 4:
                    continue
                
                try:
                    strike = float(parts[2])
                    option_type = 'Call' if parts[3] == 'C' else 'Put'
                except:
                    continue
                
                # Только близкие к спoту опционы
                distance_pct = abs((strike - spot_price) / spot_price)
                if distance_pct > 0.15:
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
                        
                        if oi > 10:  # Только значимые позиции
                            self.conn.execute("""
                                INSERT OR REPLACE INTO oi_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (timestamp, asset, symbol, strike, option_type, oi, volume, iv, spot_price))
                            collected += 1
                
                time.sleep(0.01)
            
            self.conn.commit()
            return collected
            
        except Exception as e:
            print(f"Error collecting {asset}: {e}")
            return 0
    
    def detect_signals(self, asset):
        """Поиск сигналов"""
        current_time = int(time.time())
        hour_ago = current_time - 3600
        
        # Текущие данные
        current_query = """
            SELECT symbol, strike, option_type, open_interest, volume_24h, implied_vol
            FROM oi_data 
            WHERE asset = ? AND timestamp = (SELECT MAX(timestamp) FROM oi_data WHERE asset = ?)
        """
        
        # Данные час назад
        previous_query = """
            SELECT symbol, strike, option_type, open_interest, volume_24h, implied_vol
            FROM oi_data 
            WHERE asset = ? AND timestamp >= ? AND timestamp < ?
        """
        
        current_data = {row[0]: row for row in self.conn.execute(current_query, (asset, asset)).fetchall()}
        previous_data = {}
        
        for row in self.conn.execute(previous_query, (asset, hour_ago, current_time)).fetchall():
            symbol = row[0]
            if symbol not in previous_data:
                previous_data[symbol] = row
        
        signals = []
        
        for symbol, current in current_data.items():
            if symbol not in previous_data:
                continue
            
            previous = previous_data[symbol]
            
            curr_oi = current[3]
            prev_oi = previous[3]
            curr_vol = current[4]
            curr_iv = current[5]
            prev_iv = previous[5]
            
            strike = current[1]
            option_type = current[2]
            
            # НАКОПЛЕНИЕ
            if prev_oi > 0:
                oi_change_pct = ((curr_oi - prev_oi) / prev_oi) * 100
                
                if (oi_change_pct >= self.signal_rules['accumulation']['min_oi_increase_pct'] and
                    curr_vol >= self.signal_rules['accumulation']['min_volume_confirmation'] and
                    curr_oi >= self.signal_rules['accumulation']['min_total_oi']):
                    
                    message = f"🔴 {asset} ACCUMULATION: {option_type} ${strike:.0f} OI: {prev_oi:.0f}→{curr_oi:.0f} (+{oi_change_pct:.1f}%) Vol:{curr_vol:.0f}"
                    
                    signals.append({
                        'asset': asset, 'signal_type': 'ACCUMULATION', 'symbol': symbol,
                        'strike': strike, 'option_type': option_type, 'signal_strength': oi_change_pct/10,
                        'message': message
                    })
            
            # РАЗБОР
            if (prev_oi >= self.signal_rules['breakdown']['min_previous_oi'] and prev_oi > 0):
                oi_change_pct = ((curr_oi - prev_oi) / prev_oi) * 100
                
                if (oi_change_pct <= self.signal_rules['breakdown']['min_oi_decrease_pct'] and
                    curr_vol >= self.signal_rules['breakdown']['min_volume_confirmation']):
                    
                    message = f"🟡 {asset} BREAKDOWN: {option_type} ${strike:.0f} OI: {prev_oi:.0f}→{curr_oi:.0f} ({oi_change_pct:.1f}%) Vol:{curr_vol:.0f}"
                    
                    signals.append({
                        'asset': asset, 'signal_type': 'BREAKDOWN', 'symbol': symbol,
                        'strike': strike, 'option_type': option_type, 'signal_strength': abs(oi_change_pct)/10,
                        'message': message
                    })
            
            # IV SPIKE
            if (prev_iv > 0 and curr_oi >= self.signal_rules['vol_spike']['min_oi_for_vol_signal']):
                iv_change_pct = ((curr_iv - prev_iv) / prev_iv) * 100
                
                if iv_change_pct >= self.signal_rules['vol_spike']['min_iv_increase_pct']:
                    message = f"⚡ {asset} IV SPIKE: {option_type} ${strike:.0f} IV: {prev_iv:.1f}%→{curr_iv:.1f}% (+{iv_change_pct:.1f}%) OI:{curr_oi:.0f}"
                    
                    signals.append({
                        'asset': asset, 'signal_type': 'IV_SPIKE', 'symbol': symbol,
                        'strike': strike, 'option_type': option_type, 'signal_strength': iv_change_pct/5,
                        'message': message
                    })
        
        return signals
    
    def run_analysis(self):
        """Полный анализ всех активов"""
        timestamp = int(time.time())
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        all_signals = []
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Analyzing OI changes...")
        
        for asset in self.assets:
            # Собираем данные
            collected = self.collect_data(asset)
            print(f"  {asset}: {collected} options collected")
            
            # Ищем сигналы
            signals = self.detect_signals(asset)
            
            # Сохраняем сигналы
            for signal in signals:
                self.conn.execute("""
                    INSERT INTO signals VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, date, signal['asset'], signal['signal_type'], signal['symbol'], 
                      signal['strike'], signal['option_type'], signal['signal_strength'], signal['message']))
                
                # Отправляем alert
                self.send_telegram_alert(signal['message'])
                print(f"  SIGNAL: {signal['message']}")
                
                all_signals.append(signal)
        
        self.conn.commit()
        return len(all_signals)
    
    def daemon_mode(self, interval_minutes=20):
        """Демон режим"""
        print(f"Starting OI Signals Daemon (every {interval_minutes}min)")
        
        while True:
            try:
                signals_count = self.run_analysis()
                
                if signals_count > 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generated {signals_count} signals")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No signals detected")
                
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("Daemon stopped by user")
                break
            except Exception as e:
                print(f"Daemon error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import sys
    
    system = OISignalsSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'daemon':
        system.daemon_mode(interval_minutes=20)
    else:
        signals = system.run_analysis()
        print(f"\nGenerated {signals} signals")
