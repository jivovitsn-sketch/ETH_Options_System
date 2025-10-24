#!/usr/bin/env python3
"""REAL OPTIONS DATA from Deribit"""
import urllib.request
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

class DeribitOptionsDownloader:
    def __init__(self):
        self.base_url = "https://www.deribit.com/api/v2/public"
        print("✅ Deribit downloader initialized")
    
    def get_instruments(self, currency="BTC"):
        """Get all option instruments"""
        url = f"{self.base_url}/get_instruments?currency={currency}&kind=option&expired=false"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        
        instruments = data['result']
        print(f"✅ Found {len(instruments)} {currency} options")
        return instruments
    
    def get_order_book(self, instrument_name):
        """Get order book for instrument"""
        url = f"{self.base_url}/get_order_book?instrument_name={instrument_name}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
            return data['result']
        except:
            return None
    
    def download_snapshot(self, currency="BTC"):
        """Download full options snapshot"""
        instruments = self.get_instruments(currency)
        
        options_data = []
        
        for i, inst in enumerate(instruments[:50]):  # First 50 for test
            if i % 10 == 0:
                print(f"Progress: {i}/{len(instruments[:50])}")
            
            name = inst['instrument_name']
            book = self.get_order_book(name)
            
            if book:
                options_data.append({
                    'instrument': name,
                    'strike': inst['strike'],
                    'expiration': inst['expiration_timestamp'],
                    'option_type': inst['option_type'],
                    'underlying_price': book.get('underlying_price'),
                    'mark_price': book.get('mark_price'),
                    'mark_iv': book.get('mark_iv'),
                    'bid_price': book.get('best_bid_price'),
                    'ask_price': book.get('best_ask_price'),
                    'open_interest': book.get('open_interest'),
                    'volume': book.get('stats', {}).get('volume'),
                    'greeks': book.get('greeks', {}),
                    'timestamp': datetime.now().isoformat()
                })
            
            time.sleep(0.2)
        
        df = pd.DataFrame(options_data)
        
        # Save
        output_dir = Path('data/options') / currency
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = output_dir / f"{currency}_options_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\n✅ Saved to {filename}")
        print(f"\nSample:")
        print(df[['instrument', 'strike', 'mark_price', 'mark_iv', 'open_interest']].head(10))
        
        return df

if __name__ == "__main__":
    downloader = DeribitOptionsDownloader()
    df = downloader.download_snapshot("BTC")
