#!/usr/bin/env python3
import requests
import sqlite3
import time
import threading
from datetime import datetime, timedelta

class MultiAssetOISystem:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.db_path = "data/multi_asset_oi.db"
        self.assets = ['BTC', 'ETH', 'SOL', 'XRP']
        self.running = False
        self.init_database()
    
    def init_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                asset TEXT,
                symbol TEXT,
                strike REAL,
                option_type TEXT,
                open_interest REAL,
                volume_24h REAL,
                bid REAL,
                ask REAL,
                implied_vol REAL,
                spot_price REAL
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                asset TEXT,
                status TEXT,
                message TEXT,
                data_points_collected INTEGER
            )
        """)
        
        self.conn.commit()
        print(f"Multi-asset database initialized: {self.db_path}")
    
    def check_asset_options_available(self, asset):
        """Проверяем доступность опционов для актива"""
        try:
            response = requests.get(f"{self.base_url}/v5/market/instruments-info",
                                  params={'category': 'option', 'baseCoin': asset}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0:
                    options_count = len(data['result']['list'])
                    return options_count > 0, options_count
            
        except Exception as e:
            print(f"Error checking {asset} options: {e}")
        
        return False, 0
    
    def collect_asset_data(self, asset):
        """Сбор данных по конкретному активу"""
        timestamp = int(time.time())
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n[{date}] Collecting {asset} data...")
        
        # Проверяем доступность опционов
        options_available, options_count = self.check_asset_options_available(asset)
        
        if not options_available:
            status_msg = f"No options available for {asset}"
            print(f"  ❌ {status_msg}")
            self.log_system_status(asset, "NO_OPTIONS", status_msg, 0)
            return 0
        
        print(f"  📊 Found {options_count} {asset} options")
        
        # Получаем спот цену
        try:
            spot_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                       params={'category': 'spot', 'symbol': f'{asset}USDT'})
            spot_price = float(spot_response.json()['result']['list'][0]['lastPrice'])
            print(f"  💰 {asset} spot: ${spot_price:,.2f}")
        except:
            print(f"  ❌ Failed to get {asset} spot price")
            self.log_system_status(asset, "SPOT_ERROR", "Failed to get spot price", 0)
            return 0
        
        # Получаем опционы
        instruments_response = requests.get(f"{self.base_url}/v5/market/instruments-info",
                                          params={'category': 'option', 'baseCoin': asset})
        
        if instruments_response.status_code != 200:
            self.log_system_status(asset, "API_ERROR", "Failed to get instruments", 0)
            return 0
        
        options = instruments_response.json()['result']['list']
        collected_count = 0
        significant_oi_count = 0
        
        for option in options:
            symbol = option['symbol']
            
            # Парсим символ
            parts = symbol.split('-')
            if len(parts) < 4:
                continue
            
            try:
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
                    
                    oi = float(ticker.get('openInterest', 0))
                    volume = float(ticker.get('volume24h', 0))
                    bid = float(ticker.get('bid1Price', 0))
                    ask = float(ticker.get('ask1Price', 0))
                    iv = float(ticker.get('markIv', 0))
                    
                    # Сохраняем в базу
                    self.conn.execute("""
                        INSERT INTO oi_tracking VALUES (
                            NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        timestamp, date, asset, symbol, strike, option_type,
                        oi, volume, bid, ask, iv, spot_price
                    ))
                    
                    collected_count += 1
                    
                    # Считаем значимые OI
                    if oi > 50:
                        significant_oi_count += 1
                        if oi > 500:  # Очень крупные позиции
                            print(f"    🔥 {symbol}: OI {oi:.1f}, Vol {volume:.1f}")
            
            time.sleep(0.02)  # Не спамим API
        
        self.conn.commit()
        
        status_msg = f"Collected {collected_count} options, {significant_oi_count} with significant OI"
        print(f"  ✅ {status_msg}")
        self.log_system_status(asset, "SUCCESS", status_msg, collected_count)
        
        return collected_count
    
    def log_system_status(self, asset, status, message, data_points):
        """Логирование статуса системы"""
        timestamp = int(time.time())
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.conn.execute("""
            INSERT INTO system_status VALUES (NULL, ?, ?, ?, ?, ?, ?)
        """, (timestamp, date, asset, status, message, data_points))
        self.conn.commit()
    
    def analyze_recent_changes(self, asset, hours=1):
        """Анализ изменений за последние часы"""
        cutoff_time = int(time.time()) - (hours * 3600)
        
        query = """
        SELECT symbol, strike, option_type, open_interest, volume_24h, timestamp
        FROM oi_tracking 
        WHERE asset = ? AND timestamp >= ?
        ORDER BY symbol, timestamp
        """
        
        cursor = self.conn.execute(query, (asset, cutoff_time))
        results = cursor.fetchall()
        
        if len(results) < 2:
            return []
        
        # Группируем по символам и ищем изменения
        changes = []
        symbol_data = {}
        
        for row in results:
            symbol = row[0]
            if symbol not in symbol_data:
                symbol_data[symbol] = []
            symbol_data[symbol].append(row)
        
        for symbol, data in symbol_data.items():
            if len(data) >= 2:
                latest = data[-1]
                previous = data[-2]
                
                oi_change = latest[3] - previous[3]  # open_interest change
                oi_change_pct = (oi_change / previous[3]) * 100 if previous[3] > 0 else 0
                
                if abs(oi_change_pct) > 20 and latest[4] > 10:  # 20% change + volume > 10
                    changes.append({
                        'symbol': symbol,
                        'strike': latest[1],
                        'option_type': latest[2],
                        'oi_change': oi_change,
                        'oi_change_pct': oi_change_pct,
                        'volume': latest[4]
                    })
        
        return changes
    
    def get_current_walls(self, asset):
        """Получить текущие стенки страйков"""
        latest_time = self.conn.execute("""
            SELECT MAX(timestamp) FROM oi_tracking WHERE asset = ?
        """, (asset,)).fetchone()[0]
        
        if not latest_time:
            return []
        
        query = """
        SELECT strike, option_type, open_interest
        FROM oi_tracking 
        WHERE asset = ? AND timestamp = ?
        """
        
        cursor = self.conn.execute(query, (asset, latest_time))
        results = cursor.fetchall()
        
        # Группируем по страйкам
        strike_totals = {}
        for row in results:
            strike = row[0]
            oi = row[2]
            
            if strike not in strike_totals:
                strike_totals[strike] = 0
            strike_totals[strike] += oi
        
        # Фильтруем значимые стенки
        walls = [(strike, total_oi) for strike, total_oi in strike_totals.items() if total_oi > 100]
        walls.sort(key=lambda x: x[1], reverse=True)
        
        return walls[:10]  # Топ 10
    
    def show_system_health(self):
        """Показать здоровье системы"""
        print(f"\n=== SYSTEM HEALTH CHECK ===")
        
        for asset in self.assets:
            # Последний статус
            cursor = self.conn.execute("""
                SELECT date, status, message, data_points_collected
                FROM system_status 
                WHERE asset = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (asset,))
            
            result = cursor.fetchone()
            if result:
                date, status, message, data_points = result
                status_icon = "✅" if status == "SUCCESS" else "❌"
                print(f"{asset}: {status_icon} {status} - {message} ({date})")
            else:
                print(f"{asset}: ❓ No data collected yet")
        
        # Общая статистика
        total_records = self.conn.execute("SELECT COUNT(*) FROM oi_tracking").fetchone()[0]
        print(f"\nTotal OI records: {total_records:,}")
        
        # Активность за последний час
        hour_ago = int(time.time()) - 3600
        recent_records = self.conn.execute("""
            SELECT COUNT(*) FROM oi_tracking WHERE timestamp >= ?
        """, (hour_ago,)).fetchone()[0]
        
        print(f"Records last hour: {recent_records:,}")
        
        return total_records > 0
    
    def continuous_monitoring(self, interval_minutes=30):
        """Непрерывный мониторинг всех активов"""
        print(f"🚀 Starting continuous monitoring (every {interval_minutes}min)")
        self.running = True
        
        cycle_count = 0
        
        while self.running:
            cycle_count += 1
            print(f"\n{'='*50}")
            print(f"MONITORING CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")
            
            total_collected = 0
            
            # Собираем данные по всем активам
            for asset in self.assets:
                try:
                    collected = self.collect_asset_data(asset)
                    total_collected += collected
                    
                    # Анализируем изменения
                    changes = self.analyze_recent_changes(asset, hours=1)
                    if changes:
                        print(f"  🚨 {asset} SIGNIFICANT CHANGES:")
                        for change in changes[:3]:  # Топ 3
                            print(f"    {change['option_type']} ${change['strike']:.0f}: OI {change['oi_change_pct']:+.1f}%")
                    
                    # Показываем стенки
                    walls = self.get_current_walls(asset)
                    if walls:
                        print(f"  🏗️  {asset} TOP WALLS: ${walls[0][0]:.0f} (OI: {walls[0][1]:.0f}), ${walls[1][0]:.0f} (OI: {walls[1][1]:.0f})")
                
                except Exception as e:
                    print(f"  ❌ Error processing {asset}: {e}")
                    self.log_system_status(asset, "ERROR", str(e), 0)
            
            print(f"\n📊 CYCLE SUMMARY: {total_collected} total data points collected")
            
            # Показываем здоровье системы
            self.show_system_health()
            
            if not self.running:
                break
            
            print(f"\n💤 Sleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
    
    def start_background_monitoring(self, interval_minutes=30):
        """Запуск мониторинга в фоне"""
        monitor_thread = threading.Thread(
            target=self.continuous_monitoring, 
            args=(interval_minutes,),
            daemon=True
        )
        monitor_thread.start()
        print(f"Background monitoring started (interval: {interval_minutes}min)")
        return monitor_thread
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        print("Stopping monitoring...")

if __name__ == "__main__":
    system = MultiAssetOISystem()
    
    print("=== MULTI-ASSET OI ANALYSIS SYSTEM ===")
    
    # Первоначальный сбор по всем активам
    print("1. Initial data collection for all assets...")
    for asset in system.assets:
        system.collect_asset_data(asset)
    
    print("\n2. System health check...")
    system.show_system_health()
    
    print("\n3. Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    
    try:
        system.continuous_monitoring(interval_minutes=15)  # Каждые 15 минут
    except KeyboardInterrupt:
        system.stop_monitoring()
        print("\nMonitoring stopped by user")
