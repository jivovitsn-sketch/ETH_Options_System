#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GAMMA EXPOSURE CALCULATOR - FINAL [работает с eth_options.db]"""

import sqlite3, pandas as pd, numpy as np, json, logging
from datetime import datetime
from scipy.stats import norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('logs/gamma_exposure.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

DB_PATH = 'data/eth_options.db'
FUTURES_DB_PATH = 'data/futures_data.db'
RISK_FREE_RATE, CONTRACT_MULTIPLIER = 0.05, 1
SYMBOLS = ['ETH']  # Только ETH в БД
GEX_ALERT_THRESHOLD = 1000000

class BlackScholesGreeks:
    def __init__(self, S, K, T, r, sigma, option_type='call'):
        self.S, self.K, self.T = S, K, max(T, 1/365)
        self.r, self.sigma, self.option_type = r, max(sigma, 0.01), option_type.lower()
        self.d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        self.d2 = self.d1 - sigma*np.sqrt(T)
    def gamma(self): return norm.pdf(self.d1) / (self.S * self.sigma * np.sqrt(self.T))
    def delta(self): return norm.cdf(self.d1) if self.option_type == 'call' else norm.cdf(self.d1) - 1

class GammaExposureCalculator:
    def __init__(self, symbol):
        self.symbol, self.spot_price, self.options_data = symbol, None, None
        self.gex_by_strike, self.total_gex, self.zero_gamma_level = {}, 0, None
        for p in ['logs', 'charts', 'data/gex']: Path(p).mkdir(parents=True, exist_ok=True)
    
    def get_spot_price(self):
        try:
            conn = sqlite3.connect(FUTURES_DB_PATH)
            symbol_usdt = f"{self.symbol}USDT"
            result = pd.read_sql_query("SELECT last_price FROM spot_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", conn, params=(symbol_usdt,))
            conn.close()
            if not result.empty:
                self.spot_price = float(result['last_price'].iloc[0])
                logger.info(f"{self.symbol} Spot: ${self.spot_price:.2f}")
                return self.spot_price
        except Exception as e: 
            logger.error(f"Spot error: {e}")
        return None
    
    def load_options_data(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            # Используем instrument_name для фильтрации по символу (ETH-*)
            query = f"SELECT * FROM eth_options WHERE instrument_name LIKE ? AND open_interest > 0 AND expiration_date >= date('now') ORDER BY strike"
            pattern = f"{self.symbol}-%"
            self.options_data = pd.read_sql_query(query, conn, params=(pattern,))
            conn.close()
            
            if not self.options_data.empty:
                logger.info(f"Loaded {len(self.options_data)} options for {self.symbol}")
                logger.info(f"Expirations: {sorted(self.options_data['expiration_date'].unique())}")
                return self.options_data
            else:
                logger.warning(f"No options data for {self.symbol}")
        except Exception as e: 
            logger.error(f"Load error: {e}")
        return pd.DataFrame()
    
    def calculate_gamma_exposure(self):
        if self.options_data is None or self.options_data.empty or not self.spot_price: 
            return {}
        gex_by_strike = {}
        for _, row in self.options_data.iterrows():
            try:
                expiry_str = str(row['expiration_date'])
                T = max((datetime.strptime(expiry_str, '%Y-%m-%d') - datetime.now()).days / 365.0, 1/365)
                
                iv = float(row['implied_volatility'])
                sigma = iv / 100 if iv > 1 else max(iv, 0.01)
                
                opt_type = str(row['option_type']).lower()
                if opt_type not in ['call', 'put']: opt_type = 'call'
                
                strike = float(row['strike'])
                oi = float(row['open_interest'])
                
                bs = BlackScholesGreeks(self.spot_price, strike, T, RISK_FREE_RATE, sigma, opt_type)
                gex = bs.gamma() * oi * CONTRACT_MULTIPLIER * self.spot_price
                if opt_type == 'put': gex = -gex
                gex_by_strike[strike] = gex_by_strike.get(strike, 0) + gex
            except Exception as e: 
                logger.debug(f"Error for strike {row.get('strike', 'N/A')}: {e}")
        
        self.gex_by_strike = dict(sorted(gex_by_strike.items()))
        self.total_gex = sum(gex_by_strike.values())
        logger.info(f"✅ GEX calculated: {len(gex_by_strike)} strikes, Total: ${self.total_gex:,.0f}")
        return self.gex_by_strike
    
    def find_zero_gamma_level(self):
        if not self.gex_by_strike or len(self.gex_by_strike) < 2: return None
        strikes, gex_values = np.array(list(self.gex_by_strike.keys())), np.array(list(self.gex_by_strike.values()))
        sign_changes = np.where(np.diff(np.sign(gex_values)))[0]
        if len(sign_changes) > 0:
            idx = sign_changes[np.argmin(np.abs(strikes[sign_changes] - self.spot_price))]
            x1, x2, y1, y2 = strikes[idx], strikes[idx+1], gex_values[idx], gex_values[idx+1]
            if y2 != y1:
                self.zero_gamma_level = x1 - y1 * (x2 - x1) / (y2 - y1)
                logger.info(f"✅ Zero Gamma Level: ${self.zero_gamma_level:.2f}")
                return self.zero_gamma_level
        return None
    
    def save_to_database(self):
        try:
            conn = sqlite3.connect('data/options_data.db')
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS gamma_exposure (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, strike REAL, gex_value REAL, spot_price REAL, total_gex REAL, zero_gamma_level REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(symbol, strike, timestamp))''')
            timestamp = datetime.now()
            for strike, gex in self.gex_by_strike.items():
                cursor.execute('INSERT OR REPLACE INTO gamma_exposure (symbol, strike, gex_value, spot_price, total_gex, zero_gamma_level, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (self.symbol, strike, gex, self.spot_price, self.total_gex, self.zero_gamma_level, timestamp))
            conn.commit()
            conn.close()
            logger.info("✅ GEX saved to DB")
        except Exception as e: logger.error(f"DB error: {e}")
    
    def plot_gamma_exposure(self):
        if not self.gex_by_strike: return
        strikes, gex_values = list(self.gex_by_strike.keys()), list(self.gex_by_strike.values())
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        colors = ['green' if g > 0 else 'red' for g in gex_values]
        ax1.bar(strikes, gex_values, color=colors, alpha=0.7, width=max(strikes)*0.01)
        ax1.axhline(0, color='black', linewidth=0.8)
        if self.spot_price: ax1.axvline(self.spot_price, color='blue', linestyle='--', linewidth=2, label=f'Spot: ${self.spot_price:.2f}')
        if self.zero_gamma_level: ax1.axvline(self.zero_gamma_level, color='orange', linestyle='--', linewidth=2, label=f'Zero Gamma: ${self.zero_gamma_level:.2f}')
        ax1.set_xlabel('Strike ($)', fontsize=12); ax1.set_ylabel('GEX ($)', fontsize=12)
        ax1.set_title(f'{self.symbol} Gamma Exposure\nTotal GEX: ${self.total_gex:,.0f}', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=10); ax1.grid(True, alpha=0.3)
        ax2.plot(strikes, np.cumsum(gex_values), 'purple', linewidth=2, marker='o', markersize=4)
        ax2.axhline(0, color='black', linewidth=0.8)
        if self.spot_price: ax2.axvline(self.spot_price, color='blue', linestyle='--', linewidth=2)
        ax2.set_xlabel('Strike ($)', fontsize=12); ax2.set_ylabel('Cumulative GEX ($)', fontsize=12)
        ax2.set_title(f'{self.symbol} Cumulative Gamma Exposure', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        plt.tight_layout()
        filename = f'charts/{self.symbol}_gex_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"✅ Chart saved: {filename}")
    
    def export_to_json(self):
        data = {'symbol': self.symbol, 'timestamp': datetime.now().isoformat(), 'spot_price': self.spot_price,
                'total_gex': self.total_gex, 'zero_gamma_level': self.zero_gamma_level,
                'gex_by_strike': {str(k): v for k, v in self.gex_by_strike.items()}}
        filename = f'data/gex/{self.symbol}_gex_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f: json.dump(data, f, indent=2)
        logger.info(f"✅ JSON exported: {filename}")
        return filename
    
    def run_full_calculation(self):
        logger.info(f"\n{'='*80}\n🧮 GAMMA EXPOSURE: {self.symbol}\n{'='*80}")
        if not self.get_spot_price(): return False
        if self.load_options_data().empty: return False
        if not self.calculate_gamma_exposure(): return False
        self.find_zero_gamma_level()
        self.save_to_database()
        self.plot_gamma_exposure()
        self.export_to_json()
        logger.info(f"✅ {self.symbol} COMPLETE!\n")
        return True

def main():
    print("="*80)
    print("🧮 GAMMA EXPOSURE CALCULATOR - STAGE 1.3.1")
    print("="*80 + "\n")
    results = {}
    for symbol in SYMBOLS:
        try:
            calc = GammaExposureCalculator(symbol)
            success = calc.run_full_calculation()
            results[symbol] = {'success': success, 'total_gex': calc.total_gex if success else 0,
                              'zero_gamma': calc.zero_gamma_level, 'spot_price': calc.spot_price}
        except Exception as e:
            logger.error(f"❌ {symbol} error: {e}")
            results[symbol] = {'success': False}
    
    print("\n" + "="*80)
    print("📈 FINAL RESULTS")
    print("="*80)
    for symbol, r in results.items():
        if r['success']:
            zg_str = f" | Zero Gamma: ${r['zero_gamma']:,.2f}" if r['zero_gamma'] else ""
            print(f"\n✅ {symbol}:")
            print(f"   Spot Price: ${r['spot_price']:,.2f}")
            print(f"   Total GEX: ${r['total_gex']:,.0f}{zg_str}")
        else:
            print(f"\n❌ {symbol}: FAILED")
    print("\n" + "="*80)
    print("✅ STAGE 1.3.1 COMPLETE!")
    print("="*80 + "\n")

if __name__ == "__main__": main()
