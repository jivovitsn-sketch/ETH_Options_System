#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAX PAIN - ДИНАМИЧЕСКИЙ ТОП-5 БЛИЖАЙШИХ ЭКСПИРАЦИЙ"""

import sqlite3, pandas as pd, numpy as np, json, logging
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('logs/max_pain.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

OI_DB_PATH = 'data/unlimited_oi.db'
FUTURES_DB_PATH = 'data/futures_data.db'
SYMBOLS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
MAX_DTE = 180  # Собираем данные до 6 месяцев
TOP_N_EXPIRIES = 5  # Рассчитываем только топ-5 ближайших

class MaxPainCalculator:
    def __init__(self, symbol):
        self.symbol = symbol
        self.spot_price = None
        self.options_data = None
        self.max_pain_by_expiry = {}
        self.overall_max_pain = None
        for p in ['logs', 'charts', 'data/max_pain']: Path(p).mkdir(parents=True, exist_ok=True)
    
    def get_spot_price(self):
        try:
            conn = sqlite3.connect(FUTURES_DB_PATH)
            result = pd.read_sql_query("SELECT last_price FROM spot_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                                      conn, params=(f"{self.symbol}USDT",))
            conn.close()
            if not result.empty:
                self.spot_price = float(result['last_price'].iloc[0])
                logger.info(f"{self.symbol} Spot: ${self.spot_price:,.2f}")
                return self.spot_price
        except Exception as e:
            logger.error(f"Spot error: {e}")
        return None
    
    def load_options_data(self):
        """ЗАГРУЖАЕМ ВСЕ (для продолжения сбора), но рассчитываем только топ-5"""
        try:
            conn = sqlite3.connect(OI_DB_PATH)
            query = f"""SELECT strike, expiry_date, option_type, open_interest, dte
                FROM all_positions_tracking 
                WHERE asset = ? AND open_interest > 0 AND dte > 0 AND dte <= {MAX_DTE}
                ORDER BY dte, strike"""
            self.options_data = pd.read_sql_query(query, conn, params=(self.symbol,))
            conn.close()
            
            if not self.options_data.empty:
                all_expirations = sorted(self.options_data['expiry_date'].unique())
                logger.info(f"✅ Loaded {len(self.options_data)} options")
                logger.info(f"   Total expirations: {len(all_expirations)}")
                logger.info(f"   Will calculate TOP-{TOP_N_EXPIRIES} nearest")
                return self.options_data
        except Exception as e:
            logger.error(f"Load error: {e}")
        return pd.DataFrame()
    
    def calculate_max_pain_fast(self, expiry_date):
        expiry_df = self.options_data[self.options_data['expiry_date'] == expiry_date]
        if expiry_df.empty:
            return None, None
        
        calls = expiry_df[expiry_df['option_type'] == 'Call']
        puts = expiry_df[expiry_df['option_type'] == 'Put']
        strikes = sorted(expiry_df['strike'].unique())
        
        if not strikes:
            return None, None
        
        pain_values = []
        for test_strike in strikes:
            call_pain = calls[calls['strike'] < test_strike].apply(
                lambda row: (test_strike - row['strike']) * row['open_interest'], axis=1).sum()
            put_pain = puts[puts['strike'] > test_strike].apply(
                lambda row: (row['strike'] - test_strike) * row['open_interest'], axis=1).sum()
            pain_values.append(call_pain + put_pain)
        
        pain_dict = dict(zip(strikes, pain_values))
        max_pain_strike = strikes[np.argmin(pain_values)]
        return max_pain_strike, pain_dict
    
    def calculate_all_max_pain(self):
        if self.options_data is None or self.options_data.empty:
            return {}
        
        # ДИНАМИЧЕСКИ берем TOP-N ближайших экспираций
        all_expirations = sorted(self.options_data['expiry_date'].unique())
        nearest_expirations = all_expirations[:TOP_N_EXPIRIES]
        
        logger.info(f"📊 Processing TOP-{len(nearest_expirations)} nearest expirations:")
        
        for expiry in nearest_expirations:
            max_pain, pain_dict = self.calculate_max_pain_fast(expiry)
            
            if max_pain:
                expiry_options = self.options_data[self.options_data['expiry_date'] == expiry]
                total_oi = expiry_options['open_interest'].sum()
                call_oi = expiry_options[expiry_options['option_type'] == 'Call']['open_interest'].sum()
                put_oi = expiry_options[expiry_options['option_type'] == 'Put']['open_interest'].sum()
                dte = int(expiry_options['dte'].iloc[0])
                
                distance_pct = abs(self.spot_price - max_pain) / self.spot_price * 100
                direction = "↑" if max_pain > self.spot_price else "↓" if max_pain < self.spot_price else "→"
                
                self.max_pain_by_expiry[expiry] = {
                    'max_pain': max_pain, 'pain_by_strike': pain_dict,
                    'spot_price': self.spot_price, 'distance_pct': distance_pct,
                    'direction': direction, 'dte': dte,
                    'total_oi': total_oi, 'call_oi': call_oi, 'put_oi': put_oi,
                    'put_call_ratio': put_oi / call_oi if call_oi > 0 else 0
                }
                
                logger.info(f"   {expiry} (DTE {dte}): ${max_pain:,.0f} {direction} ({distance_pct:.1f}%)")
        
        # Взвешенный Max Pain
        if self.max_pain_by_expiry:
            weighted_sum = sum(d['max_pain'] * d['total_oi'] for d in self.max_pain_by_expiry.values())
            total_weight = sum(d['total_oi'] for d in self.max_pain_by_expiry.values())
            self.overall_max_pain = weighted_sum / total_weight if total_weight > 0 else None
            if self.overall_max_pain:
                dist = abs(self.spot_price - self.overall_max_pain) / self.spot_price * 100
                logger.info(f"✅ Overall Max Pain: ${self.overall_max_pain:,.0f} ({dist:.1f}%)")
        
        return self.max_pain_by_expiry
    
    def save_to_database(self):
        try:
            conn = sqlite3.connect('data/options_data.db')
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS max_pain (
                id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, expiry_date DATE, max_pain_strike REAL,
                spot_price REAL, distance_pct REAL, dte INTEGER, total_oi REAL, call_oi REAL, put_oi REAL,
                put_call_ratio REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, expiry_date, timestamp))''')
            timestamp = datetime.now()
            for expiry, data in self.max_pain_by_expiry.items():
                cursor.execute('''INSERT OR REPLACE INTO max_pain 
                    (symbol, expiry_date, max_pain_strike, spot_price, distance_pct, dte,
                     total_oi, call_oi, put_oi, put_call_ratio, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (self.symbol, expiry, data['max_pain'], data['spot_price'],
                     data['distance_pct'], data['dte'], data['total_oi'],
                     data['call_oi'], data['put_oi'], data['put_call_ratio'], timestamp))
            conn.commit()
            conn.close()
            logger.info("✅ Saved to DB")
        except Exception as e:
            logger.error(f"DB error: {e}")
    
    def plot_max_pain(self):
        if not self.max_pain_by_expiry:
            return
        sorted_expiries = sorted(self.max_pain_by_expiry.items(), key=lambda x: x[1]['dte'])
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        labels = [f"{exp[:10]}\nDTE {d['dte']}" for exp, d in sorted_expiries]
        max_pains = [d['max_pain'] for _, d in sorted_expiries]
        spots = [d['spot_price'] for _, d in sorted_expiries]
        
        x = np.arange(len(labels))
        width = 0.35
        ax1.bar(x - width/2, max_pains, width, label='Max Pain', color='orange', alpha=0.8)
        ax1.bar(x + width/2, spots, width, label='Spot', color='blue', alpha=0.8)
        ax1.set_xlabel('Expiration', fontsize=12)
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.set_title(f'{self.symbol} Max Pain - TOP-{len(sorted_expiries)} Nearest', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, fontsize=10)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        if sorted_expiries:
            nearest_exp, nearest_data = sorted_expiries[0]
            pain_dict = nearest_data['pain_by_strike']
            strikes = sorted(pain_dict.keys())
            pains = [pain_dict[s] for s in strikes]
            
            ax2.plot(strikes, pains, 'purple', linewidth=2, marker='o', markersize=4)
            ax2.axvline(nearest_data['max_pain'], color='orange', linestyle='--', 
                       linewidth=2, label=f'Max Pain: ${nearest_data["max_pain"]:,.0f}')
            ax2.axvline(self.spot_price, color='blue', linestyle='--', 
                       linewidth=2, label=f'Spot: ${self.spot_price:,.0f}')
            ax2.set_xlabel('Strike ($)', fontsize=12)
            ax2.set_ylabel('Total Pain ($)', fontsize=12)
            ax2.set_title(f'{self.symbol} Pain Curve - {nearest_exp[:10]} (DTE {nearest_data["dte"]})', 
                         fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        filename = f'charts/{self.symbol}_max_pain_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"✅ Chart: {filename}")
    
    def export_to_json(self):
        data = {
            'symbol': self.symbol, 'timestamp': datetime.now().isoformat(),
            'spot_price': self.spot_price, 'overall_max_pain': self.overall_max_pain,
            'expirations': {
                exp: {k: v for k, v in info.items() if k != 'pain_by_strike'}
                for exp, info in self.max_pain_by_expiry.items()
            }
        }
        filename = f'data/max_pain/{self.symbol}_max_pain_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"✅ JSON: {filename}")
    
    def run_full_calculation(self):
        logger.info(f"\n{'='*80}\n🎯 MAX PAIN: {self.symbol}\n{'='*80}")
        if not self.get_spot_price() or self.load_options_data().empty:
            return False
        if not self.calculate_all_max_pain():
            return False
        self.save_to_database()
        self.plot_max_pain()
        self.export_to_json()
        logger.info(f"✅ {self.symbol} COMPLETE!\n")
        return True

def main():
    print("="*80 + f"\n🎯 MAX PAIN (TOP-{TOP_N_EXPIRIES} ДИНАМИЧЕСКИХ)\n" + "="*80 + "\n")
    results = {}
    for symbol in SYMBOLS:
        try:
            calc = MaxPainCalculator(symbol)
            success = calc.run_full_calculation()
            results[symbol] = {
                'success': success, 'overall_max_pain': calc.overall_max_pain,
                'spot_price': calc.spot_price, 'num_expirations': len(calc.max_pain_by_expiry)
            }
        except Exception as e:
            logger.error(f"❌ {symbol}: {e}")
            results[symbol] = {'success': False}
    
    print("\n" + "="*80 + "\n📈 RESULTS\n" + "="*80)
    for symbol, r in results.items():
        if r['success']:
            mp, spot = r['overall_max_pain'], r['spot_price']
            dist = abs(spot - mp) / spot * 100 if mp else 0
            direction = "↑" if mp > spot else "↓"
            print(f"\n✅ {symbol}: Spot ${spot:,.2f} | Max Pain ${mp:,.0f} {direction} ({dist:.1f}%)")
        else:
            print(f"\n❌ {symbol}: FAILED")
    print("\n" + "="*80 + "\n✅ STAGE 1.3.2 COMPLETE!\n" + "="*80)

if __name__ == "__main__":
    main()
