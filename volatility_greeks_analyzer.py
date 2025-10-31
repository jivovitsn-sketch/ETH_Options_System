#!/usr/bin/env python3
"""STAGE 1.3.3: VOLATILITY & GREEKS [только ETH с реальными данными]"""

import sqlite3, pandas as pd, numpy as np, json, logging
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('logs/volatility_greeks.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

FUTURES_DB = 'data/futures_data.db'
ETH_OPTIONS_DB = 'data/eth_options.db'

class VolatilityGreeksAnalyzer:
    def __init__(self):
        self.spot_price = None
        self.options_data = None
        Path('logs').mkdir(exist_ok=True)
        Path('charts').mkdir(exist_ok=True)
        Path('data/volatility').mkdir(parents=True, exist_ok=True)
    
    def get_spot_price(self):
        conn = sqlite3.connect(FUTURES_DB)
        result = pd.read_sql_query("SELECT last_price FROM spot_data WHERE symbol = 'ETHUSDT' ORDER BY timestamp DESC LIMIT 1", conn)
        conn.close()
        if not result.empty:
            self.spot_price = float(result['last_price'].iloc[0])
            logger.info(f"ETH Spot: ${self.spot_price:,.2f}")
            return True
        return False
    
    def load_options(self):
        conn = sqlite3.connect(ETH_OPTIONS_DB)
        query = """SELECT strike, expiration_date, option_type, implied_volatility,
                  delta, gamma, vega, theta, open_interest, mark_price
                  FROM eth_options WHERE open_interest > 0 
                  AND expiration_date >= date('now')
                  ORDER BY expiration_date, strike"""
        self.options_data = pd.read_sql_query(query, conn)
        conn.close()
        
        if not self.options_data.empty:
            logger.info(f"✅ Loaded {len(self.options_data)} ETH options")
            return True
        return False
    
    def analyze_iv(self):
        atm = self.options_data[
            (self.options_data['strike'] >= self.spot_price * 0.9) &
            (self.options_data['strike'] <= self.spot_price * 1.1) &
            (self.options_data['implied_volatility'] > 0)
        ]
        
        avg_iv = atm['implied_volatility'].mean()
        call_iv = atm[atm['option_type'] == 'CALL']['implied_volatility'].mean()
        put_iv = atm[atm['option_type'] == 'PUT']['implied_volatility'].mean()
        
        logger.info(f"📊 IV: Avg={avg_iv:.1f}%, Calls={call_iv:.1f}%, Puts={put_iv:.1f}%")
        return {'avg_iv': avg_iv, 'call_iv': call_iv, 'put_iv': put_iv}
    
    def analyze_greeks(self):
        total_delta = (self.options_data['delta'] * self.options_data['open_interest']).sum()
        total_gamma = (self.options_data['gamma'] * self.options_data['open_interest']).sum()
        
        logger.info(f"📊 Greeks: Delta={total_delta:,.0f}, Gamma={total_gamma:,.2f}")
        return {'total_delta': total_delta, 'total_gamma': total_gamma}
    
    def export_json(self, iv, greeks):
        data = {
            'symbol': 'ETH',
            'timestamp': datetime.now().isoformat(),
            'spot_price': self.spot_price,
            'iv_analysis': iv,
            'greeks': greeks
        }
        filename = f'data/volatility/ETH_vol_greeks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"✅ JSON: {filename}")
    
    def run(self):
        logger.info(f"\n{'='*80}\n📊 VOLATILITY & GREEKS: ETH\n{'='*80}")
        
        if not self.get_spot_price():
            logger.error("❌ No spot price")
            return False
        
        if not self.load_options():
            logger.error("❌ No options data")
            return False
        
        iv = self.analyze_iv()
        greeks = self.analyze_greeks()
        self.export_json(iv, greeks)
        
        return True

if __name__ == "__main__":
    print("="*80)
    print("📊 VOLATILITY & GREEKS - STAGE 1.3.3 (ETH ONLY)")
    print("="*80 + "\n")
    
    analyzer = VolatilityGreeksAnalyzer()
    success = analyzer.run()
    
    print("\n" + "="*80)
    print("="*80 + "\n")
