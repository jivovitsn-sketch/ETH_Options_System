#!/usr/bin/env python3
"""
Professional OI Strike Analysis System
Tracks accumulations, walls, breakdowns and volatility correlations
"""

import requests
import sqlite3
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timedelta

class OIStrikeAnalysisSystem:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/oi_strike_analysis.db"
        self.init_database()
        
        # Параметры анализа
        self.analysis_params = {
            'wall_threshold': 50,  # Минимальный OI для считания "стенкой"
            'accumulation_threshold': 0.25,  # 25% рост OI = накопление
            'breakdown_threshold': -0.30,  # 30% падение OI = разбор
            'volume_confirmation': 10,  # Минимальный объем для подтверждения
            'iv_spike_threshold': 0.15,  # 15% рост IV = всплеск волатильности
        }
    
    def init_database(self):
        """Инициализация базы данных для хранения исторических данных"""
        self.conn = sqlite3.connect(self.db_path)
        
        # Таблица исторических данных OI по страйкам
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                symbol TEXT,
                asset TEXT,
                expiry TEXT,
                strike REAL,
                option_type TEXT,
                open_interest REAL,
                volume_24h REAL,
                bid REAL,
                ask REAL,
                mid_price REAL,
                implied_vol REAL,
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                spot_price REAL
            )
        """)
        
        # Таблица анализа накоплений
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                asset TEXT,
                expiry TEXT,
                strike REAL,
                option_type TEXT,
                analysis_type TEXT,  -- 'accumulation', 'breakdown', 'wall', 'spike'
                oi_change_pct REAL,
                oi_absolute_change REAL,
                volume_ratio REAL,
                iv_change_pct REAL,
                significance_score REAL,
                notes TEXT
            )
        """)
        
        # Таблица стенок страйков
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS strike_walls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                asset TEXT,
                expiry TEXT,
                strike REAL,
                wall_strength REAL,  -- Суммарный OI calls + puts
                call_oi REAL,
                put_oi REAL,
                net_delta REAL,
                distance_from_spot_pct REAL,
                wall_type TEXT  -- 'support', 'resistance', 'neutral'
            )
        """)
        
        self.conn.commit()
        print(f"Database initialized: {self.db_path}")
    
    def collect_comprehensive_data(self, asset='ETH'):
        """Сбор полных данных по опционам для анализа"""
        
        timestamp = int(time.time())
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Collecting comprehensive {asset} options data...")
        
        # Получаем спот цену
        spot_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                   params={'category': 'spot', 'symbol': f'{asset}USDT'})
        spot_price = float(spot_response.json()['result']['list'][0]['lastPrice'])
        print(f"{asset} spot: ${spot_price:,.2f}")
        
        # Получаем все опционы
        instruments_response = requests.get(f"{self.base_url}/v5/market/instruments-info",
                                          params={'category': 'option', 'baseCoin': asset})
        
        if instruments_response.status_code != 200:
            print(f"Failed to get instruments data")
            return
        
        options = instruments_response.json()['result']['list']
        print(f"Found {len(options)} {asset} options")
        
        collected_count = 0
        
        for option in options:
            symbol = option['symbol']
            
            # Парсим детали опциона
            parts = symbol.split('-')
            if len(parts) < 4:
                continue
                
            try:
                expiry = parts[1]
                strike = float(parts[2])
                option_type = 'Call' if parts[3] == 'C' else 'Put'
            except:
                continue
            
            # Получаем тикер данные
            ticker_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                         params={'category': 'option', 'symbol': symbol})
            
            if ticker_response.status_code == 200:
                ticker_data = ticker_response.json()
                if ticker_data['retCode'] == 0 and ticker_data['result']['list']:
                    ticker = ticker_data['result']['list'][0]
                    
                    # Извлекаем все доступные данные
                    oi = float(ticker.get('openInterest', 0))
                    volume = float(ticker.get('volume24h', 0))
                    bid = float(ticker.get('bid1Price', 0))
                    ask = float(ticker.get('ask1Price', 0))
                    mid_price = (bid + ask) / 2 if bid > 0 and ask > 0 else 0
                    iv = float(ticker.get('markIv', 0))
                    delta = float(ticker.get('delta', 0))
                    gamma = float(ticker.get('gamma', 0))
                    theta = float(ticker.get('theta', 0))
                    vega = float(ticker.get('vega', 0))
                    
                    # Сохраняем в базу
                    self.conn.execute("""
                        INSERT INTO oi_history VALUES (
                            NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        timestamp, date, symbol, asset, expiry, strike, option_type,
                        oi, volume, bid, ask, mid_price, iv, delta, gamma, theta, vega, spot_price
                    ))
                    
                    collected_count += 1
                    
                    # Показываем прогресс для крупных OI
                    if oi > 50:
                        print(f"  {symbol}: OI {oi:.1f}, Vol {volume:.1f}")
            
            # Не спамим API
            time.sleep(0.03)
        
        self.conn.commit()
        print(f"Collected data for {collected_count} options")
        
        # Сразу запускаем анализ
        self.analyze_oi_changes(asset)
        self.identify_strike_walls(asset)
    
    def analyze_oi_changes(self, asset='ETH'):
        """Анализ изменений OI для выявления накоплений и разборов"""
        
        print(f"Analyzing OI changes for {asset}...")
        
        # Получаем данные за последние 24 часа
        yesterday = int(time.time()) - 86400
        
        query = """
        SELECT symbol, strike, option_type, open_interest, volume_24h, implied_vol, timestamp
        FROM oi_history 
        WHERE asset = ? AND timestamp >= ?
        ORDER BY symbol, timestamp
        """
        
        df = pd.read_sql_query(query, self.conn, params=(asset, yesterday))
        
        if len(df) < 2:
            print("Insufficient historical data for change analysis")
            return []
        
        # Группируем по символам и вычисляем изменения
        analysis_results = []
        
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol].sort_values('timestamp')
            
            if len(symbol_data) < 2:
                continue
            
            latest = symbol_data.iloc[-1]
            previous = symbol_data.iloc[-2]
            
            # Вычисляем изменения
            oi_change = latest['open_interest'] - previous['open_interest']
            oi_change_pct = (oi_change / previous['open_interest']) * 100 if previous['open_interest'] > 0 else 0
            
            volume_ratio = latest['volume_24h'] / latest['open_interest'] if latest['open_interest'] > 0 else 0
            
            iv_change = latest['implied_vol'] - previous['implied_vol']
            iv_change_pct = (iv_change / previous['implied_vol']) * 100 if previous['implied_vol'] > 0 else 0
            
            # Определяем тип события
            analysis_type = None
            significance_score = 0
            notes = ""
            
            # Накопление
            if (oi_change_pct >= self.analysis_params['accumulation_threshold'] * 100 and 
                latest['volume_24h'] >= self.analysis_params['volume_confirmation']):
                analysis_type = 'accumulation'
                significance_score = min(oi_change_pct / 10, 10)  # Нормализуем 0-10
                notes = f"OI рост {oi_change_pct:.1f}%, объем {latest['volume_24h']:.1f}"
            
            # Разбор
            elif (oi_change_pct <= self.analysis_params['breakdown_threshold'] * 100 and
                  latest['volume_24h'] >= self.analysis_params['volume_confirmation']):
                analysis_type = 'breakdown'
                significance_score = min(abs(oi_change_pct) / 10, 10)
                notes = f"OI падение {oi_change_pct:.1f}%, объем {latest['volume_24h']:.1f}"
            
            # Всплеск волатильности
            elif abs(iv_change_pct) >= self.analysis_params['iv_spike_threshold'] * 100:
                analysis_type = 'volatility_spike'
                significance_score = min(abs(iv_change_pct) / 5, 10)
                notes = f"IV изменение {iv_change_pct:.1f}%"
            
            if analysis_type:
                analysis_results.append({
                    'symbol': symbol,
                    'strike': latest['strike'],
                    'option_type': latest['option_type'],
                    'analysis_type': analysis_type,
                    'oi_change_pct': oi_change_pct,
                    'significance_score': significance_score,
                    'notes': notes
                })
        
        print(f"Found {len(analysis_results)} significant OI changes")
        return analysis_results
    
    def identify_strike_walls(self, asset='ETH'):
        """Идентификация стенок страйков"""
        
        print(f"Identifying strike walls for {asset}...")
        
        # Получаем последние данные
        query = """
        SELECT strike, option_type, open_interest, spot_price
        FROM oi_history 
        WHERE asset = ? 
        AND timestamp = (SELECT MAX(timestamp) FROM oi_history WHERE asset = ?)
        """
        
        df = pd.read_sql_query(query, self.conn, params=(asset, asset))
        
        if df.empty:
            print("No data for wall analysis")
            return []
        
        spot_price = df['spot_price'].iloc[0]
        
        # Группируем по страйкам
        strike_analysis = []
        
        for strike in df['strike'].unique():
            strike_data = df[df['strike'] == strike]
            
            call_oi = strike_data[strike_data['option_type'] == 'Call']['open_interest'].sum()
            put_oi = strike_data[strike_data['option_type'] == 'Put']['open_interest'].sum()
            
            total_oi = call_oi + put_oi
            
            if total_oi >= self.analysis_params['wall_threshold']:
                # Вычисляем характеристики стенки
                distance_pct = ((strike - spot_price) / spot_price) * 100
                
                # Определяем тип стенки
                if distance_pct > 2:
                    wall_type = 'resistance'
                elif distance_pct < -2:
                    wall_type = 'support'
                else:
                    wall_type = 'neutral'
                
                strike_analysis.append({
                    'strike': strike,
                    'wall_strength': total_oi,
                    'call_oi': call_oi,
                    'put_oi': put_oi,
                    'distance_from_spot_pct': distance_pct,
                    'wall_type': wall_type
                })
        
        # Сортируем по силе стенки
        strike_analysis.sort(key=lambda x: x['wall_strength'], reverse=True)
        
        print(f"Identified {len(strike_analysis)} strike walls")
        return strike_analysis
    
    def get_analysis_report(self, asset='ETH'):
        """Генерация отчета по анализу"""
        
        print(f"\n=== OI ANALYSIS REPORT FOR {asset} ===")
        
        # Последние изменения OI
        recent_changes = self.analyze_oi_changes(asset)
        
        if recent_changes:
            print(f"\nSIGNIFICANT OI CHANGES:")
            for change in recent_changes[:10]:  # Топ 10
                print(f"  {change['option_type']} ${change['strike']:.0f}: {change['analysis_type']}")
                print(f"    Score: {change['significance_score']:.1f} | {change['notes']}")
        
        # Текущие стенки
        walls = self.identify_strike_walls(asset)
        
        if walls:
            print(f"\nCURRENT STRIKE WALLS:")
            for wall in walls[:10]:  # Топ 10
                print(f"  ${wall['strike']:.0f} ({wall['wall_type']}): OI {wall['wall_strength']:.0f}")
                print(f"    Calls: {wall['call_oi']:.0f} | Puts: {wall['put_oi']:.0f} | Distance: {wall['distance_from_spot_pct']:.1f}%")

if __name__ == "__main__":
    # Создаем и запускаем систему анализа
    analyzer = OIStrikeAnalysisSystem()
    
    print("=== OI STRIKE ANALYSIS SYSTEM ===")
    print("1. Collecting initial data...")
    analyzer.collect_comprehensive_data('ETH')
    
    print("\n2. Generating analysis report...")
    analyzer.get_analysis_report('ETH')
    
    print("\n3. System ready for continuous monitoring")
