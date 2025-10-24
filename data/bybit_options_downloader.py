#!/usr/bin/env python3
"""
BYBIT OPTIONS DATA DOWNLOADER
Загрузка опционных данных: OI, IV, Greeks, цены
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time

class BybitOptionsDownloader:
    """
    Загрузка опционных данных с Bybit
    """
    
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.session = requests.Session()
        print("✅ Bybit Options Downloader initialized")
    
    def get_option_symbols(self, base_coin: str = "BTC"):
        """Получить список опционных символов"""
        endpoint = "/v5/market/instruments-info"
        params = {
            "category": "option",
            "baseCoin": base_coin
        }
        
        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            data = response.json()
            symbols = [item['symbol'] for item in data['result']['list']]
            print(f"✅ Found {len(symbols)} option symbols for {base_coin}")
            return symbols
        else:
            print(f"❌ Error: {response.status_code}")
            return []
    
    def get_option_ticker(self, symbol: str):
        """Получить данные тикера (цена, IV, Greeks)"""
        endpoint = "/v5/market/tickers"
        params = {
            "category": "option",
            "symbol": symbol
        }
        
        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['result']['list']:
                return data['result']['list'][0]
        return None
    
    def get_open_interest(self, symbol: str):
        """Получить Open Interest"""
        endpoint = "/v5/market/open-interest"
        params = {
            "category": "option",
            "symbol": symbol,
            "intervalTime": "5min"
        }
        
        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data['result']['list']
        return []
    
    def download_options_snapshot(self, base_coin: str = "BTC"):
        """
        Загрузить снимок всех опционов
        """
        print(f"\n📊 Downloading options data for {base_coin}...")
        
        # Get symbols
        symbols = self.get_option_symbols(base_coin)
        
        if not symbols:
            print("❌ No symbols found")
            return None
        
        # Limit to first 50 for test
        symbols = symbols[:50]
        
        options_data = []
        
        for i, symbol in enumerate(symbols):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(symbols)}")
            
            ticker = self.get_option_ticker(symbol)
            
            if ticker:
                options_data.append({
                    'symbol': symbol,
                    'underlying_price': ticker.get('underlyingPrice'),
                    'bid': ticker.get('bid1Price'),
                    'ask': ticker.get('ask1Price'),
                    'last_price': ticker.get('lastPrice'),
                    'mark_price': ticker.get('markPrice'),
                    'volume_24h': ticker.get('volume24h'),
                    'open_interest': ticker.get('openInterest'),
                    'iv': ticker.get('markIv'),
                    'delta': ticker.get('delta'),
                    'gamma': ticker.get('gamma'),
                    'vega': ticker.get('vega'),
                    'theta': ticker.get('theta'),
                    'timestamp': datetime.now().isoformat()
                })
            
            time.sleep(0.1)  # Rate limit
        
        df = pd.DataFrame(options_data)
        
        # Save
        output_dir = Path('data/options') / base_coin
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = output_dir / f"{base_coin}_options_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"✅ Saved {len(df)} options to {filename}")
        print(f"\n📊 Sample data:")
        print(df.head())
        
        return df

if __name__ == "__main__":
    downloader = BybitOptionsDownloader()
    
    # Test download
    df = downloader.download_options_snapshot("BTC")
