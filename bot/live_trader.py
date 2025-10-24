#!/usr/bin/env python3
"""LIVE TRADER - реальная торговля"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import urllib.request
import json
from datetime import datetime
from discord_alerts import DiscordAlerter

class LiveTrader:
    def __init__(self, paper_trading=True):
        self.paper = paper_trading
        self.alerter = DiscordAlerter()
        self.capital = 10000
        self.position = None
        
        print("✅ Live Trader initialized")
        print(f"   Mode: {'PAPER' if paper_trading else 'LIVE'}")
        print(f"   Capital: ${self.capital:,.0f}")
    
    def get_current_price(self, symbol='ETHUSDT'):
        """Get current price from Bybit"""
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
        
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
                price = float(data['result']['list'][0]['lastPrice'])
                return price
        except:
            return None
    
    def check_signal(self, symbol='ETHUSDT'):
        """Check for trading signal (simplified)"""
        # В реальности здесь Order Blocks detection
        # Для теста используем random
        import random
        return random.choice([None, 'BUY', None, None, None])
    
    def open_position(self, symbol, price):
        """Open position"""
        size = self.capital * 0.05
        
        self.position = {
            'symbol': symbol,
            'entry': price,
            'size': size,
            'opened_at': datetime.now()
        }
        
        self.alerter.trade_opened(symbol, 'Order Blocks', price, size)
        
        print(f"\n🟢 OPENED: {symbol} @ ${price:,.2f}, size ${size:,.0f}")
    
    def close_position(self, price):
        """Close position"""
        pnl_pct = (price - self.position['entry']) / self.position['entry']
        pnl = self.position['size'] * pnl_pct
        
        self.capital += pnl
        
        self.alerter.trade_closed(
            self.position['symbol'],
            'Order Blocks',
            pnl,
            pnl_pct * 100
        )
        
        print(f"🔴 CLOSED: {self.position['symbol']} @ ${price:,.2f}, P&L: ${pnl:,.2f}")
        
        self.position = None
    
    def run(self, interval_seconds=60):
        """Run trading loop"""
        
        print(f"\nStarting live trader (check every {interval_seconds}s)")
        print("Press Ctrl+C to stop\n")
        
        self.alerter.send("🚀 Live Trader Started", f"Paper Trading: {self.paper}", 3447003)
        
        try:
            while True:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Get price
                price = self.get_current_price('ETHUSDT')
                
                if price is None:
                    print(f"[{timestamp}] ❌ Failed to get price")
                    time.sleep(interval_seconds)
                    continue
                
                print(f"[{timestamp}] ETH: ${price:,.2f}, Capital: ${self.capital:,.0f}")
                
                # Check position
                if self.position:
                    # Check exit (simplified - 1 hour hold)
                    hold_time = (datetime.now() - self.position['opened_at']).seconds
                    
                    if hold_time > 3600:  # 1 hour
                        self.close_position(price)
                else:
                    # Check signal
                    signal = self.check_signal()
                    
                    if signal == 'BUY':
                        self.open_position('ETHUSDT', price)
                
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            
            if self.position:
                print("\nClosing open position...")
                price = self.get_current_price('ETHUSDT')
                if price:
                    self.close_position(price)

if __name__ == "__main__":
    trader = LiveTrader(paper_trading=True)
    
    print("\nTest mode - will run for 5 minutes")
    print("In production: python3 bot/live_trader.py")
    
    # Test for 5 minutes
    # trader.run(interval_seconds=60)
