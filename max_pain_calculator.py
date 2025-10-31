#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAX PAIN CALCULATOR - STAGE 1.3.2 [BTC/ETH/SOL/XRP/DOGE/MNT]"""

import sqlite3, pandas as pd, numpy as np, json, logging
from datetime import datetime, timedelta
from collections import defaultdict
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
        try:
            conn = sqlite3.connect(OI_DB_PATH)
            query = """SELECT strike, expiry_date, option_type, open_interest, dte
                FROM all_positions_tracking 
                WHERE asset = ? AND open_interest > 0 AND dte > 0
                ORDER BY expiry_date, strike"""
            self.options_data = pd.read_sql_query(query, conn, params=(self.symbol,))
            conn.close()
            
            if not self.options_data.empty:
                expirations = sorted(self.options_data['expiry_date'].unique())
                logger.info(f"✅ Loaded {len(self.options_data)} options")
                logger.info(f"   Expirations: {len(expirations)} dates")
                logger.info(f"   Next 3: {expirations[:3]}")
                return self.options_data
        except Exception as e:
            logger.error(f"Load error: {e}")
        return pd.DataFrame()
    
    def calculate_max_pain_for_expiry(self, expiry_date):
        """
        Max Pain = страйк, при котором суммарная стоимость всех опционов минимальна
        
        Для каждого потенциального страйка K:
        - Call OI: если Strike < K, то стоимость = (K - Strike) × OI
        - Put OI: если Strike > K, то стоимость = (Strike - K) × OI
        """
        expiry_options = self.options_data[self.options_data['expiry_date'] == expiry_date]
        
        if expiry_options.empty:
            return None, None
        
        # Получаем уникальные страйки
        strikes = sorted(expiry_options['strike'].unique())
        
        if not strikes:
            return None, None
        
        min_pain = float('inf')
        max_pain_strike = None
        pain_by_strike = {}
        
        for test_strike in strikes:
            total_pain = 0
            
            # Считаем боль для Call опционов
            calls = expiry_options[expiry_options['option_type'] == 'Call']
            for _, call in calls.iterrows():
                if call['strike'] < test_strike:
                    # Call ITM - holders получают прибыль
                    total_pain += (test_strike - call['strike']) * call['open_interest']
            
            # Считаем боль для Put опционов
            puts = expiry_options[expiry_options['option_type'] == 'Put']
            for _, put in puts.iterrows():
                if put['strike'] > test_strike:
                    # Put ITM - holders получают прибыль
                    total_pain += (put['strike'] - test_strike) * put['open_interest']
            
            pain_by_strike[test_strike] = total_pain
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = test_strike
        
        return max_pain_strike, pain_by_strike
    
    def calculate_all_max_pain(self):
        """Расчет Max Pain для всех экспираций"""
        if self.options_data is None or self.options_data.empty:
            return {}
        
        expirations = sorted(self.options_data['expiry_date'].unique())
        
        for expiry in expirations[:10]:  # Топ-10 ближайших экспираций
            max_pain, pain_dict = self.calculate_max_pain_for_expiry(expiry)
            
            if max_pain:
                # Дополнительная статистика
                expiry_options = self.options_data[self.options_data['expiry_date'] == expiry]
                total_oi = expiry_options['open_interest'].sum()
                call_oi = expiry_options[expiry_options['option_type'] == 'Call']['open_interest'].sum()
                put_oi = expiry_options[expiry_options['option_type'] == 'Put']['open_interest'].sum()
                dte = int(expiry_options['dte'].iloc[0])
                
                distance_pct = abs(self.spot_price - max_pain) / self.spot_price * 100
                direction = "↑" if max_pain > self.spot_price else "↓" if max_pain < self.spot_price else "→"
                
                self.max_pain_by_expiry[expiry] = {
                    'max_pain': max_pain,
                    'pain_by_strike': pain_dict,
                    'spot_price': self.spot_price,
                    'distance_pct': distance_pct,
                    'direction': direction,
                    'dte': dte,
                    'total_oi': total_oi,
                    'call_oi': call_oi,
                    'put_oi': put_oi,
                    'put_call_ratio': put_oi / call_oi if call_oi > 0 else 0
                }
                
                logger.info(f"   {expiry} (DTE {dte}): Max Pain ${max_pain:,.0f} {direction} (spot ${self.spot_price:,.0f}, {distance_pct:.1f}%)")
        
        # Общий Max Pain (взвешенный по OI)
        if self.max_pain_by_expiry:
            weighted_sum = sum(data['max_pain'] * data['total_oi'] for data in self.max_pain_by_expiry.values())
            total_weight = sum(data['total_oi'] for data in self.max_pain_by_expiry.values())
            self.overall_max_pain = weighted_sum / total_weight if total_weight > 0 else None
            
            if self.overall_max_pain:
                overall_distance = abs(self.spot_price - self.overall_max_pain) / self.spot_price * 100
                logger.info(f"\n✅ Overall Max Pain: ${self.overall_max_pain:,.0f} ({overall_distance:.1f}% from spot)")
        
        return self.max_pain_by_expiry
    
    def save_to_database(self):
        try:
            conn = sqlite3.connect('data/options_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS max_pain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, expiry_date DATE, max_pain_strike REAL,
                spot_price REAL, distance_pct REAL, dte INTEGER,
                total_oi REAL, call_oi REAL, put_oi REAL, put_call_ratio REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        
        # Берем топ-5 ближайших экспираций
        sorted_expiries = sorted(self.max_pain_by_expiry.items(), 
                                key=lambda x: x[1]['dte'])[:5]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # График 1: Max Pain vs Spot по экспирациям
        expiry_labels = [exp[:10] for exp, _ in sorted_expiries]
        max_pains = [data['max_pain'] for _, data in sorted_expiries]
        spots = [data['spot_price'] for _, data in sorted_expiries]
        
        x = np.arange(len(expiry_labels))
        width = 0.35
        
        ax1.bar(x - width/2, max_pains, width, label='Max Pain', color='orange', alpha=0.8)
        ax1.bar(x + width/2, spots, width, label='Spot Price', color='blue', alpha=0.8)
        ax1.set_xlabel('Expiration Date', fontsize=12)
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.set_title(f'{self.symbol} Max Pain by Expiration', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(expiry_labels, rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # График 2: Pain Curve для ближайшей экспирации
        if sorted_expiries:
            nearest_expiry, nearest_data = sorted_expiries[0]
            pain_dict = nearest_data['pain_by_strike']
            
            strikes = sorted(pain_dict.keys())
            pains = [pain_dict[s] for s in strikes]
            
            ax2.plot(strikes, pains, 'purple', linewidth=2, marker='o', markersize=4)
            ax2.axvline(nearest_data['max_pain'], color='orange', linestyle='--', 
                       linewidth=2, label=f'Max Pain: ${nearest_data["max_pain"]:,.0f}')
            ax2.axvline(self.spot_price, color='blue', linestyle='--', 
                       linewidth=2, label=f'Spot: ${self.spot_price:,.0f}')
            
            ax2.set_xlabel('Strike Price ($)', fontsize=12)
            ax2.set_ylabel('Total Pain ($)', fontsize=12)
            ax2.set_title(f'{self.symbol} Pain Curve - {nearest_expiry[:10]} (DTE {nearest_data["dte"]})', 
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
            'symbol': self.symbol,
            'timestamp': datetime.now().isoformat(),
            'spot_price': self.spot_price,
            'overall_max_pain': self.overall_max_pain,
            'expirations': {
                exp: {
                    'max_pain': info['max_pain'],
                    'distance_pct': info['distance_pct'],
                    'direction': info['direction'],
                    'dte': info['dte'],
                    'total_oi': info['total_oi'],
                    'put_call_ratio': info['put_call_ratio']
                }
                for exp, info in self.max_pain_by_expiry.items()
            }
        }
        
        filename = f'data/max_pain/{self.symbol}_max_pain_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"✅ JSON: {filename}")
        return filename
    
    def run_full_calculation(self):
        logger.info(f"\n{'='*80}\n🎯 MAX PAIN: {self.symbol}\n{'='*80}")
        
        if not self.get_spot_price():
            logger.error("❌ No spot price")
            return False
        
        if self.load_options_data().empty:
            logger.error("❌ No options data")
            return False
        
        logger.info(f"\n📊 Calculating Max Pain for {len(self.options_data['expiry_date'].unique())} expirations...")
        
        if not self.calculate_all_max_pain():
            logger.error("❌ Max Pain calculation failed")
            return False
        
        self.save_to_database()
        self.plot_max_pain()
        self.export_to_json()
        
        logger.info(f"✅ {self.symbol} COMPLETE!\n")
        return True

def main():
    print("="*80)
    print("🎯 MAX PAIN CALCULATOR - STAGE 1.3.2")
    print("="*80 + "\n")
    
    results = {}
    for symbol in SYMBOLS:
        try:
            calc = MaxPainCalculator(symbol)
            success = calc.run_full_calculation()
            results[symbol] = {
                'success': success,
                'overall_max_pain': calc.overall_max_pain,
                'spot_price': calc.spot_price,
                'num_expirations': len(calc.max_pain_by_expiry)
            }
        except Exception as e:
            logger.error(f"❌ {symbol} error: {e}")
            results[symbol] = {'success': False}
    
    print("\n" + "="*80)
    print("📈 FINAL RESULTS - MAX PAIN")
    print("="*80)
    
    for symbol, r in results.items():
        if r['success']:
            mp = r['overall_max_pain']
            spot = r['spot_price']
            distance = abs(spot - mp) / spot * 100 if mp else 0
            direction = "↑" if mp > spot else "↓" if mp < spot else "→"
            
            print(f"\n✅ {symbol}:")
            print(f"   Spot: ${spot:,.2f} | Max Pain: ${mp:,.0f} {direction} ({distance:.1f}%)")
            print(f"   Expirations analyzed: {r['num_expirations']}")
        else:
            print(f"\n❌ {symbol}: FAILED")
    
    print("\n" + "="*80)
    print("✅ STAGE 1.3.2 COMPLETE!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
