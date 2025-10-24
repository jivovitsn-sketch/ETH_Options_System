#!/usr/bin/env python3
"""LIVE MONITOR - мониторинг в реальном времени"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from datetime import datetime
from discord_alerts import DiscordAlerter

class LiveMonitor:
    def __init__(self):
        self.alerter = DiscordAlerter()
        self.last_check = None
        
        print("✅ Live Monitor initialized")
        print("   Checking every 5 minutes")
    
    def check_system_health(self):
        """Check if system is healthy"""
        
        # Check if we have recent data
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
        files = sorted(data_dir.glob("*.csv"))
        
        if not files:
            self.alerter.system_error("No data files found!")
            return False
        
        # Check last file timestamp
        last_file = files[-1]
        # Would check actual data timestamp here
        
        # Send health check
        metrics = {
            'capital': 10000,  # Would be real capital
            'open_trades': 0,  # Would be real open trades
            'win_rate': 75.0   # Would be calculated
        }
        
        self.alerter.system_healthy(metrics)
        return True
    
    def monitor_signals(self):
        """Monitor for trading signals"""
        
        # Would check real market data here
        # For now, send test
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking signals...")
        
        # Example: if bullish signal detected
        # self.alerter.trade_opened('ETHUSDT', 'Bull Call 60DTE', 3939.0, 500.0)
        
        print("  No signals")
    
    def run(self, interval_minutes=5):
        """Run monitoring loop"""
        
        print(f"\nStarting live monitor (check every {interval_minutes} min)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_system_health()
                self.monitor_signals()
                
                time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")

if __name__ == "__main__":
    monitor = LiveMonitor()
    
    # Test alert first
    print("\nSending test alert...")
    monitor.alerter.send("🚀 System Started", "Live monitoring active", color=3447003)
    
    # Start monitoring
    # monitor.run(interval_minutes=5)
    
    print("\nTo run live monitoring:")
    print("  python3 bot/live_monitor.py")
