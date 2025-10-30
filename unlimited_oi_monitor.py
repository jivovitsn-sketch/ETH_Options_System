#!/usr/bin/env python3
import requests
import sqlite3
import time
from datetime import datetime, timedelta

class UnlimitedOIMonitor:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/unlimited_oi.db"
        self.assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        self.init_database()
        
    def init_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Отслеживание ВСЕХ экспираций без ограничений
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS all_positions_tracking (
                timestamp INTEGER,
                asset TEXT,
                symbol TEXT,
                expiry TEXT,
                expiry_date TEXT,
                dte INTEGER,
                strike REAL,
                option_type TEXT,
                open_interest REAL,
                volume_24h REAL,
                spot_price REAL,
                distance_pct REAL,
                time_category TEXT,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        
        # Кумулятивный анализ по каждой позиции
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS position_cumulative (
                position_key TEXT PRIMARY KEY,
                asset TEXT,
                expiry TEXT,
                expiry_date TEXT,
                dte INTEGER,
                strike REAL,
                option_type TEXT,
                first_seen INTEGER,
                last_update INTEGER,
                initial_oi REAL,
                current_oi REAL,
                peak_oi REAL,
                total_volume_flow REAL,
                tracking_days INTEGER,
                avg_daily_volume REAL,
                oi_evolution TEXT,
                big_money_confidence REAL,
                future_positioning_score REAL,
                status TEXT
            )
        """)
        
        # Анализ будущего позиционирования
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS future_positioning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                asset TEXT,
                time_horizon TEXT,
                dominant_strikes TEXT,
                call_put_ratio REAL,
                total_oi REAL,
                institutional_flow TEXT,
                market_expectation TEXT
            )
        """)
        
        self.conn.commit()
        print("Unlimited OI Monitor initialized - tracking ALL expirations")
    
    def parse_expiry_date(self, expiry_str):
        """Парсим дату экспирации в формате"""
        try:
            day = int(expiry_str[:2])
            month_str = expiry_str[2:5]
            year = 2000 + int(expiry_str[5:])
            
            month_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            
            month = month_map.get(month_str, 1)
            expiry_date = datetime(year, month, day)
            dte = (expiry_date - datetime.now()).days
            
            return expiry_date.strftime('%Y-%m-%d'), dte
            
        except:
            return None, 999
    
    def categorize_time_horizon(self, dte):
        """Категоризация временных горизонтов"""
        if dte <= 0:
            return "EXPIRED"
        elif dte <= 1:
            return "SAME_DAY"
        elif dte <= 7:
            return "WEEKLY"
        elif dte <= 30:
            return "MONTHLY"
        elif dte <= 90:
            return "QUARTERLY"
        elif dte <= 180:
            return "SEMI_ANNUAL"
        elif dte <= 365:
            return "ANNUAL"
        else:
            return "LONG_TERM"
    
    def cleanup_expired_options(self):
        """Автоматическая очистка истекших опционов"""
        current_time = int(time.time())
        
        # Удаляем истекшие из tracking
        expired_count = self.conn.execute("""
            DELETE FROM all_positions_tracking 
            WHERE time_category = 'EXPIRED'
        """).rowcount
        
        # Удаляем истекшие из cumulative
        expired_cumulative = self.conn.execute("""
            DELETE FROM position_cumulative 
            WHERE dte <= 0
        """).rowcount
        
        if expired_count > 0 or expired_cumulative > 0:
            print(f"Cleaned up {expired_count + expired_cumulative} expired positions")
        
        self.conn.commit()
    
    def collect_all_expirations(self, asset):
        """Сбор ВСЕХ доступных экспираций без ограничений"""
        timestamp = int(time.time())
        
        try:
            # Спот цена
            spot_resp = requests.get(f"{self.base_url}/v5/market/tickers",
                                   params={'category': 'spot', 'symbol': f'{asset}USDT'})
            spot_price = float(spot_resp.json()['result']['list'][0]['lastPrice'])
            
            # ВСЕ опционы без фильтров
            instruments_resp = requests.get(f"{self.base_url}/v5/market/instruments-info",
                                          params={'category': 'option', 'baseCoin': asset})
            
            options = instruments_resp.json()['result']['list']
            
            # Статистика по временным горизонтам
            time_stats = {}
            collected = 0
            
            print(f"  {asset}: Processing {len(options)} options across ALL time horizons...")
            
            for option in options:
                symbol = option['symbol']
                parts = symbol.split('-')
                if len(parts) < 4:
                    continue
                
                expiry = parts[1]
                strike = float(parts[2])
                option_type = 'Call' if parts[3] == 'C' else 'Put'
                
                expiry_date, dte = self.parse_expiry_date(expiry)
                if not expiry_date:
                    continue
                
                time_category = self.categorize_time_horizon(dte)
                
                # Пропускаем уже истекшие
                if time_category == "EXPIRED":
                    continue
                
                distance_pct = (strike - spot_price) / spot_price
                
                # Убираю ограничения по расстоянию для долгосрочных
                if time_category in ["SAME_DAY", "WEEKLY", "MONTHLY"]:
                    # Для краткосрочных ограничиваем 50%
                    if abs(distance_pct) > 0.50:
                        continue
                elif time_category in ["QUARTERLY", "SEMI_ANNUAL"]:
                    # Для среднесрочных 100%
                    if abs(distance_pct) > 1.0:
                        continue
                # Для годовых и долгосрочных НЕТ ограничений
                
                # Получаем данные опциона
                ticker_resp = requests.get(f"{self.base_url}/v5/market/tickers",
                                         params={'category': 'option', 'symbol': symbol})
                
                if ticker_resp.status_code == 200:
                    ticker = ticker_resp.json()['result']['list'][0]
                    
                    oi = float(ticker.get('openInterest', 0))
                    volume = float(ticker.get('volume24h', 0))
                    
                    # Сохраняем ВСЕ позиции с любым OI или объемом
                    if oi > 0 or volume > 0:
                        self.conn.execute("""
                            INSERT OR REPLACE INTO all_positions_tracking VALUES 
                            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (timestamp, asset, symbol, expiry, expiry_date, dte, strike,
                              option_type, oi, volume, spot_price, distance_pct, time_category))
                        
                        collected += 1
                        
                        # Статистика по категориям
                        if time_category not in time_stats:
                            time_stats[time_category] = 0
                        time_stats[time_category] += 1
                
                time.sleep(0.001)  # Минимальная задержка
            
            self.conn.commit()
            
            # Выводим статистику
            print(f"  {asset}: Collected {collected} positions:")
            for category, count in sorted(time_stats.items()):
                print(f"    {category}: {count}")
            
            return collected
            
        except Exception as e:
            print(f"Error collecting {asset} all expirations: {e}")
            return 0
    
    def update_position_analytics(self, asset):
        """Обновляем аналитику по всем позициям"""
        
        latest_data = self.conn.execute("""
            SELECT symbol, expiry, expiry_date, dte, strike, option_type, 
                   open_interest, volume_24h, timestamp, time_category
            FROM all_positions_tracking 
            WHERE asset = ? AND timestamp = (
                SELECT MAX(timestamp) FROM all_positions_tracking WHERE asset = ?
            )
        """, (asset, asset)).fetchall()
        
        for row in latest_data:
            (symbol, expiry, expiry_date, dte, strike, option_type, 
             oi, volume, timestamp, time_category) = row
            
            position_key = f"{asset}_{symbol}"
            
            # Проверяем существующую запись
            existing = self.conn.execute("""
                SELECT * FROM position_cumulative WHERE position_key = ?
            """, (position_key,)).fetchone()
            
            if existing:
                # Обновляем существующую
                (_, _, _, _, old_dte, _, _, first_seen, _, initial_oi, _, peak_oi,
                 total_volume, days, _, _, confidence, future_score, status) = existing
                
                new_peak_oi = max(peak_oi, oi)
                new_total_volume = total_volume + volume
                tracking_days = max(1, (timestamp - first_seen) / 86400)
                avg_daily_vol = new_total_volume / tracking_days
                
                # Эволюция OI
                if oi > initial_oi * 1.5:
                    oi_evolution = "STRONG_ACCUMULATION"
                elif oi > initial_oi * 1.2:
                    oi_evolution = "ACCUMULATION"
                elif oi < initial_oi * 0.7:
                    oi_evolution = "DECLINE"
                else:
                    oi_evolution = "STABLE"
                
                # Big money confidence (для долгосрочных позиций)
                size_factor = min(oi / 50, 10)
                time_factor = min(tracking_days / 7, 5) if time_category in ["QUARTERLY", "SEMI_ANNUAL", "ANNUAL"] else 1
                volume_factor = min(avg_daily_vol / 10, 3)
                
                big_money_confidence = (size_factor + time_factor + volume_factor) / 3
                
                # Future positioning score (для долгосрочных)
                if dte > 90:
                    future_score = big_money_confidence * (dte / 365) * 2
                else:
                    future_score = big_money_confidence
                
                self.conn.execute("""
                    UPDATE position_cumulative 
                    SET last_update = ?, dte = ?, current_oi = ?, peak_oi = ?, 
                        total_volume_flow = ?, tracking_days = ?, avg_daily_volume = ?,
                        oi_evolution = ?, big_money_confidence = ?, future_positioning_score = ?
                    WHERE position_key = ?
                """, (timestamp, dte, oi, new_peak_oi, new_total_volume, tracking_days,
                      avg_daily_vol, oi_evolution, big_money_confidence, future_score, position_key))
            
            else:
                # Новая позиция
                self.conn.execute("""
                    INSERT INTO position_cumulative VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (position_key, asset, expiry, expiry_date, dte, strike, option_type,
                      timestamp, timestamp, oi, oi, oi, volume, 1, volume,
                      "NEW", 1.0, 1.0, "ACTIVE"))
        
        self.conn.commit()
    
    def analyze_future_positioning(self, asset):
        """Анализ будущего позиционирования по временным горизонтам"""
        
        # Анализируем разные временные горизонты
        horizons = ["QUARTERLY", "SEMI_ANNUAL", "ANNUAL", "LONG_TERM"]
        
        for horizon in horizons:
            positions = self.conn.execute("""
                SELECT strike, option_type, current_oi, future_positioning_score, dte
                FROM position_cumulative 
                WHERE asset = ? AND future_positioning_score > 2
                AND dte BETWEEN ? AND ?
                ORDER BY future_positioning_score DESC
            """, (asset, 
                  90 if horizon == "QUARTERLY" else 180 if horizon == "SEMI_ANNUAL" else 365 if horizon == "ANNUAL" else 730,
                  180 if horizon == "QUARTERLY" else 365 if horizon == "SEMI_ANNUAL" else 730 if horizon == "ANNUAL" else 9999)).fetchall()
            
            if positions:
                call_oi = sum(oi for strike, opt_type, oi, score, dte in positions if opt_type == 'Call')
                put_oi = sum(oi for strike, opt_type, oi, score, dte in positions if opt_type == 'Put')
                total_oi = call_oi + put_oi
                
                if total_oi > 0:
                    call_put_ratio = call_oi / put_oi if put_oi > 0 else 999
                    
                    # Доминирующие страйки
                    top_strikes = sorted(positions, key=lambda x: x[2], reverse=True)[:5]
                    dominant_strikes = ",".join([f"{opt}${strike:.0f}({oi:.0f})" 
                                               for strike, opt, oi, score, dte in top_strikes])
                    
                    # Определяем институциональный флоу
                    if call_put_ratio > 2:
                        institutional_flow = "BULLISH_LONG_TERM"
                        market_expectation = f"Big money expects {asset} higher in {horizon.lower()}"
                    elif call_put_ratio < 0.5:
                        institutional_flow = "BEARISH_LONG_TERM"
                        market_expectation = f"Big money hedging {asset} downside in {horizon.lower()}"
                    else:
                        institutional_flow = "NEUTRAL_HEDGING"
                        market_expectation = f"Mixed positioning in {horizon.lower()}"
                    
                    # Сохраняем анализ
                    self.conn.execute("""
                        INSERT INTO future_positioning VALUES 
                        (NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (int(time.time()), asset, horizon, dominant_strikes, call_put_ratio,
                          total_oi, institutional_flow, market_expectation))
                    
                    print(f"  {asset} {horizon}: {institutional_flow}")
                    print(f"    C/P Ratio: {call_put_ratio:.2f}, Total OI: {total_oi:.0f}")
                    print(f"    {market_expectation}")
        
        self.conn.commit()
    
    def run_unlimited_cycle(self):
        """Полный цикл анализа всех временных горизонтов"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Unlimited OI Analysis - ALL Time Horizons")
        
        # Очистка истекших
        self.cleanup_expired_options()
        
        for asset in self.assets:
            collected = self.collect_all_expirations(asset)
            
            if collected > 0:
                self.update_position_analytics(asset)
                self.analyze_future_positioning(asset)
        
        return True
    
    def continuous_unlimited_monitoring(self, interval_minutes=10):
        """Непрерывный мониторинг всех временных горизонтов"""
        print(f"Starting unlimited monitoring (every {interval_minutes} minutes)")
        print("Tracking: SAME_DAY -> WEEKLY -> MONTHLY -> QUARTERLY -> SEMI_ANNUAL -> ANNUAL -> LONG_TERM")
        
        while True:
            try:
                self.run_unlimited_cycle()
                print(f"Next unlimited scan in {interval_minutes} minutes...\n")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("Unlimited monitoring stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import sys
    
    monitor = UnlimitedOIMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'unlimited':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        monitor.continuous_unlimited_monitoring(interval)
    else:
        monitor.run_unlimited_cycle()
        print("Unlimited analysis complete")
