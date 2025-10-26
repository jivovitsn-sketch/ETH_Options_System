#!/usr/bin/env python3
"""
РЕАЛЬНЫЙ СБОРЩИК ETH ОПЦИОНОВ - Deribit API
"""
import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os

class ETHOptionsCollector:
    def __init__(self):
        self.deribit_url = "https://www.deribit.com/api/v2/public"
        self.db_file = "data/eth_options.db"
        self.log_file = "logs/options_collector.log"
        
        # Создаем базу данных
        self.init_database()
        
        # Telegram config
        with open('config/telegram.json') as f:
            config = json.load(f)
        self.token = config['bot_token']
        self.channels = config['channels'] 
        self.proxies = config['proxy']
        
        self.log("ETH Options Collector initialized")
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(self.log_file, 'a') as f:
            f.write(log_line + '\n')
    
    def init_database(self):
        """Создание базы данных для опционов"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eth_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                instrument_name TEXT,
                strike REAL,
                expiration_date DATE,
                option_type TEXT,
                mark_price REAL,
                bid_price REAL,
                ask_price REAL,
                underlying_price REAL,
                implied_volatility REAL,
                delta REAL,
                theta REAL,
                gamma REAL,
                vega REAL,
                open_interest INTEGER,
                volume_24h REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        self.log("Database initialized")
    
    def get_eth_instruments(self):
        """Получение списка ETH опционов"""
        try:
            url = f"{self.deribit_url}/get_instruments"
            params = {
                'currency': 'ETH',
                'kind': 'option',
                'expired': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                instruments = data['result']
                self.log(f"Found {len(instruments)} ETH options")
                return instruments
            else:
                self.log(f"Error getting instruments: {response.status_code}")
                
        except Exception as e:
            self.log(f"Instruments error: {e}")
        
        return []
    
    def get_option_data(self, instrument_name):
        """Получение данных конкретного опциона"""
        try:
            # Получаем цену и Greeks
            url = f"{self.deribit_url}/get_order_book"
            params = {'instrument_name': instrument_name}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()['result']
                
                return {
                    'instrument_name': instrument_name,
                    'mark_price': data.get('mark_price', 0),
                    'bid_price': data['best_bid_price'] if data.get('best_bid_price') else 0,
                    'ask_price': data['best_ask_price'] if data.get('best_ask_price') else 0,
                    'underlying_price': data.get('underlying_price', 0),
                    'implied_volatility': data.get('mark_iv', 0),
                    'delta': data.get('greeks', {}).get('delta', 0),
                    'theta': data.get('greeks', {}).get('theta', 0),
                    'gamma': data.get('greeks', {}).get('gamma', 0),
                    'vega': data.get('greeks', {}).get('vega', 0),
                    'open_interest': data.get('open_interest', 0),
                    'volume_24h': data.get('stats', {}).get('volume', 0)
                }
                
        except Exception as e:
            self.log(f"Option data error for {instrument_name}: {e}")
        
        return None
    
    def parse_instrument_name(self, name):
        """Парсинг названия инструмента: ETH-29NOV24-3200-C"""
        try:
            parts = name.split('-')
            if len(parts) == 4:
                currency = parts[0]
                date_str = parts[1]
                strike = float(parts[2])
                option_type = parts[3]  # C или P
                
                # Парсим дату
                expiry = datetime.strptime(date_str, '%d%b%y').date()
                
                return {
                    'currency': currency,
                    'expiration_date': expiry,
                    'strike': strike,
                    'option_type': 'CALL' if option_type == 'C' else 'PUT'
                }
        except:
            pass
        
        return None
    
    def collect_all_options(self):
        """Сбор всех ETH опционов"""
        self.log("Starting options collection")
        
        instruments = self.get_eth_instruments()
        
        if not instruments:
            self.log("No instruments found")
            return
        
        collected = 0
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for instrument in instruments:
            instrument_name = instrument['instrument_name']
            
            # Парсим инструмент
            parsed = self.parse_instrument_name(instrument_name)
            if not parsed:
                continue
            
            # Получаем данные опциона
            option_data = self.get_option_data(instrument_name)
            if not option_data:
                continue
            
            # Сохраняем в базу
            cursor.execute('''
                INSERT INTO eth_options (
                    timestamp, instrument_name, strike, expiration_date, option_type,
                    mark_price, bid_price, ask_price, underlying_price, implied_volatility,
                    delta, theta, gamma, vega, open_interest, volume_24h
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                instrument_name,
                parsed['strike'],
                parsed['expiration_date'],
                parsed['option_type'],
                option_data['mark_price'],
                option_data['bid_price'],
                option_data['ask_price'],
                option_data['underlying_price'],
                option_data['implied_volatility'],
                option_data['delta'],
                option_data['theta'],
                option_data['gamma'],
                option_data['vega'],
                option_data['open_interest'],
                option_data['volume_24h']
            ))
            
            collected += 1
            
            # Задержка между запросами
            time.sleep(0.1)
        
        conn.commit()
        conn.close()
        
        self.log(f"Collected {collected} options")
        return collected
    
    def analyze_options_flow(self):
        """Анализ потока опционов"""
        conn = sqlite3.connect(self.db_file)
        
        # Последние данные
        df = pd.read_sql_query('''
            SELECT * FROM eth_options 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
        ''', conn)
        
        if len(df) == 0:
            conn.close()
            return None
        
        # Анализ по типам
        calls = df[df['option_type'] == 'CALL']
        puts = df[df['option_type'] == 'PUT']
        
        # Put/Call ratio
        put_call_ratio = len(puts) / len(calls) if len(calls) > 0 else 0
        
        # Активные страйки
        top_strikes = df.groupby('strike')['volume_24h'].sum().sort_values(ascending=False).head(5)
        
        # Высокая IV
        high_iv = df[df['implied_volatility'] > df['implied_volatility'].quantile(0.8)]
        
        conn.close()
        
        return {
            'total_options': len(df),
            'calls_count': len(calls),
            'puts_count': len(puts),
            'put_call_ratio': put_call_ratio,
            'avg_iv': df['implied_volatility'].mean(),
            'underlying_price': df['underlying_price'].iloc[0],
            'top_strikes': top_strikes.to_dict(),
            'high_iv_count': len(high_iv)
        }
    
    def send_telegram(self, message):
        """Отправка в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': self.channels['vip'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            # Пробуем с прокси
            response = requests.post(url, json=data, proxies=self.proxies, timeout=10)
            if response.status_code == 200:
                return True
                
            # Без прокси
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.log(f"Telegram error: {e}")
            return False
    
    def run_collection_cycle(self):
        """Один цикл сбора"""
        collected = self.collect_all_options()
        
        if collected > 0:
            analysis = self.analyze_options_flow()
            
            if analysis:
                message = f"""
📊 <b>ETH OPTIONS UPDATE</b>

<b>Market Data:</b>
ETH Price: ${analysis['underlying_price']:,.2f}
Total Options: {analysis['total_options']}
Calls: {analysis['calls_count']} | Puts: {analysis['puts_count']}
Put/Call Ratio: {analysis['put_call_ratio']:.2f}

<b>Volatility:</b>
Avg IV: {analysis['avg_iv']*100:.1f}%
High IV Options: {analysis['high_iv_count']}

<b>Active Strikes:</b>
{chr(10).join(f"${int(strike):,}: {vol:.0f}" for strike, vol in list(analysis['top_strikes'].items())[:3])}

<i>Updated: {datetime.now().strftime('%H:%M:%S')}</i>
                """
                
                self.send_telegram(message.strip())
        
        return collected

if __name__ == "__main__":
    collector = ETHOptionsCollector()
    
    # Тестовый сбор
    print("Starting ETH Options collection...")
    result = collector.run_collection_cycle()
    print(f"Collection complete: {result} options processed")
