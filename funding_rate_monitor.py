#!/usr/bin/env python3
"""
💰 FUNDING RATE MONITOR - Мониторинг и алерты Funding Rate
Пункт 1.2.2: Funding Rate (каждые 8 часов + алерты)
"""
import sqlite3
import time
from datetime import datetime, timedelta

class FundingRateMonitor:
    def __init__(self):
        self.db_path = "data/futures_data.db"
        self.alerts_db = "data/funding_alerts.db"
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'MNTUSDT']
        self.thresholds = {
            'extreme_positive': 0.10,
            'high_positive': 0.05,
            'extreme_negative': -0.10,
            'high_negative': -0.05
        }
        self.init_alerts_db()
    
    def init_alerts_db(self):
        conn = sqlite3.connect(self.alerts_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS funding_alerts (
                timestamp INTEGER, symbol TEXT, funding_rate REAL,
                alert_type TEXT, message TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS funding_history (
                timestamp INTEGER, symbol TEXT, funding_rate REAL,
                next_funding_time INTEGER, rate_change REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        conn.commit()
        conn.close()
        print("Database initialized")
    
    def get_latest_funding(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        funding_data = {}
        for symbol in self.symbols:
            cursor.execute("""
                SELECT funding_rate, timestamp FROM futures_ticker
                WHERE symbol = ? AND funding_rate != 0
                ORDER BY timestamp DESC LIMIT 1
            """, (symbol,))
            result = cursor.fetchone()
            if result:
                funding_data[symbol] = {'rate': result[0], 'timestamp': result[1]}
        conn.close()
        return funding_data
    
    def check_alert_conditions(self, symbol, funding_rate):
        alerts = []
        rate_pct = funding_rate * 100
        if rate_pct > self.thresholds['extreme_positive']:
            alerts.append({'type': 'EXTREME_POSITIVE',
                          'message': "EXTREME LONG FUNDING: %.4f%%" % rate_pct})
        elif rate_pct > self.thresholds['high_positive']:
            alerts.append({'type': 'HIGH_POSITIVE',
                          'message': "HIGH LONG FUNDING: %.4f%%" % rate_pct})
        if rate_pct < self.thresholds['extreme_negative']:
            alerts.append({'type': 'EXTREME_NEGATIVE',
                          'message': "EXTREME SHORT FUNDING: %.4f%%" % rate_pct})
        elif rate_pct < self.thresholds['high_negative']:
            alerts.append({'type': 'HIGH_NEGATIVE',
                          'message': "HIGH SHORT FUNDING: %.4f%%" % rate_pct})
        return alerts
    
    def save_alert(self, symbol, funding_rate, alert_type, message):
        conn = sqlite3.connect(self.alerts_db)
        timestamp = int(datetime.now().timestamp())
        conn.execute("""
            INSERT INTO funding_alerts (timestamp, symbol, funding_rate, alert_type, message)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, symbol, funding_rate, alert_type, message))
        conn.commit()
        conn.close()
    
    def run_cycle(self):
        print("\n" + "="*80)
        print("[%s] Funding Rate Monitor" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*80)
        funding_data = self.get_latest_funding()
        if not funding_data:
            print("No funding data")
            return
        alerts_count = 0
        for symbol, data in funding_data.items():
            rate = data['rate']
            rate_pct = rate * 100
            alerts = self.check_alert_conditions(symbol, rate)
            print("  %s | FR: %+.4f%%" % (symbol, rate_pct))
            if alerts:
                alerts_count += len(alerts)
                for alert in alerts:
                    print("    ALERT: %s" % alert['message'])
                    self.save_alert(symbol, rate, alert['type'], alert['message'])
        print("="*80)
        print("Checked: %d assets | Alerts: %d" % (len(funding_data), alerts_count))
        print("="*80 + "\n")
    
    def run(self):
        print("Funding Rate Monitor Started")
        print("Tracking: " + ', '.join(self.symbols))
        print("Check interval: 30 minutes\n")
        while True:
            try:
                self.run_cycle()
                time.sleep(1800)
            except KeyboardInterrupt:
                print("\nStopping...")
                break
            except Exception as e:
                print("Error:", e)
                time.sleep(300)

if __name__ == "__main__":
    monitor = FundingRateMonitor()
    monitor.run()
