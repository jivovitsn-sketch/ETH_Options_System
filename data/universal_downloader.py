#!/usr/bin/env python3
"""UNIVERSAL DATA DOWNLOADER - All assets"""

import urllib.request
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import time

class UniversalDownloader:
    def __init__(self):
        self.bybit_base = "https://api.bybit.com/v5/market"
        self.deribit_base = "https://www.deribit.com/api/v2/public"
        print("✅ Universal Downloader initialized")
    
    def download_spot_historical(self, symbol: str, days: int = 100):
        """Download spot data from Bybit"""
        print(f"\n📊 Downloading {symbol} ({days} days)...")
        
        output_dir = Path(__file__).parent / 'raw' / symbol
        output_dir.mkdir(parents=True, exist_ok=True)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        total_candles = 0
        current_date = start_date
        
        while current_date < end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            start_ms = int(current_date.timestamp() * 1000)
            end_ms = int((current_date + timedelta(days=1)).timestamp() * 1000)
            
            url = f"{self.bybit_base}/kline?category=spot&symbol={symbol}&interval=60&start={start_ms}&end={end_ms}&limit=1000"
            
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                    
                    if data.get('retCode') == 0 and data['result']['list']:
                        klines = data['result']['list']
                        
                        filename = output_dir / f"{symbol}_{date_str}.csv"
                        
                        with open(filename, 'w', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
                            
                            for k in reversed(klines):
                                ts = datetime.fromtimestamp(int(k[0])/1000)
                                writer.writerow([
                                    ts.strftime('%Y-%m-%d %H:%M:%S'),
                                    float(k[1]),
                                    float(k[2]),
                                    float(k[3]),
                                    float(k[4]),
                                    float(k[5]),
                                    float(k[6]) if len(k) > 6 else 0
                                ])
                        
                        total_candles += len(klines)
                        
                        if total_candles % 500 == 0:
                            print(f"  {total_candles} candles, {date_str}")
                
                time.sleep(0.15)
                
            except Exception as e:
                print(f"  Error {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        print(f"✅ {symbol}: {total_candles} candles")
        return total_candles
    
    def download_options(self, currency: str):
        """Download options from Deribit"""
        print(f"\n📊 Downloading {currency} options...")
        
        url = f"{self.deribit_base}/get_instruments?currency={currency}&kind=option&expired=false"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
            
            instruments = data['result']
            print(f"  Found {len(instruments)} options")
            
            options_data = []
            
            for i, inst in enumerate(instruments):
                if i % 50 == 0:
                    print(f"  {i}/{len(instruments)}")
                
                name = inst['instrument_name']
                book_url = f"{self.deribit_base}/get_order_book?instrument_name={name}"
                
                try:
                    with urllib.request.urlopen(book_url, timeout=5) as response:
                        book = json.loads(response.read())['result']
                    
                    options_data.append({
                        'instrument': name,
                        'strike': inst['strike'],
                        'expiration': inst['expiration_timestamp'],
                        'option_type': inst['option_type'],
                        'underlying_price': book.get('underlying_price'),
                        'mark_price': book.get('mark_price'),
                        'mark_iv': book.get('mark_iv'),
                        'bid': book.get('best_bid_price'),
                        'ask': book.get('best_ask_price'),
                        'oi': book.get('open_interest'),
                        'volume': book.get('stats', {}).get('volume'),
                        'greeks': book.get('greeks', {}),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    time.sleep(0.12)
                    
                except:
                    pass
            
            output_dir = Path(__file__).parent / 'options_history' / currency
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            import pandas as pd
            df = pd.DataFrame(options_data)
            df.to_csv(filename, index=False)
            
            print(f"✅ {currency}: {len(df)} options")
            
            return len(df)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0

if __name__ == "__main__":
    dl = UniversalDownloader()
    
    assets = [
        ('BTCUSDT', 'BTC'),
        ('ETHUSDT', 'ETH'),
        ('SOLUSDT', 'SOL'),
        ('XRPUSDT', 'XRP')
    ]
    
    print("="*70)
    print("DOWNLOADING ALL ASSETS")
    print("="*70)
    
    for spot, opts in assets:
        print(f"\n{'='*70}")
        print(f"{spot}")
        print(f"{'='*70}")
        
        # Spot (100 days for now)
        dl.download_spot_historical(spot, days=100)
        
        # Options (BTC, ETH only)
        if opts in ['BTC', 'ETH']:
            dl.download_options(opts)
    
    print("\n" + "="*70)
    print("✅ DOWNLOAD COMPLETE")
    print("="*70)
