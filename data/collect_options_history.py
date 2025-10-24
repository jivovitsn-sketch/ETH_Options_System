#!/usr/bin/env python3
"""Collect options snapshots for backtest"""
import urllib.request
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

def download_snapshot(currency="BTC"):
    """Download current snapshot"""
    base_url = "https://www.deribit.com/api/v2/public"
    
    # Get instruments
    url = f"{base_url}/get_instruments?currency={currency}&kind=option&expired=false"
    with urllib.request.urlopen(url) as response:
        instruments = json.loads(response.read())['result']
    
    print(f"Found {len(instruments)} options")
    
    # Get data for each
    data = []
    for i, inst in enumerate(instruments):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(instruments)}")
        
        name = inst['instrument_name']
        url = f"{base_url}/get_order_book?instrument_name={name}"
        
        try:
            with urllib.request.urlopen(url) as response:
                book = json.loads(response.read())['result']
            
            data.append({
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
            
            time.sleep(0.15)
        except:
            pass
    
    df = pd.DataFrame(data)
    
    # Save
    output_dir = Path('data/options_history') / currency
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\n✅ Saved {len(df)} options to {filename}")
    
    # Summary
    print(f"\nSpot: ${df['underlying_price'].iloc[0]:,.2f}")
    print(f"Expirations: {df['expiration'].nunique()}")
    print(f"Total OI: {df['oi'].sum():.1f} BTC")
    
    return df

if __name__ == "__main__":
    print("="*70)
    print("OPTIONS HISTORY COLLECTOR")
    print("="*70)
    download_snapshot("BTC")
