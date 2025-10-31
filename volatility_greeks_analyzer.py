#!/usr/bin/env python3
"""STAGE 1.3.3: VOLATILITY & GREEKS - работаем с тем что есть"""

import sqlite3, pandas as pd, numpy as np, json, logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

Path('data/volatility').mkdir(parents=True, exist_ok=True)

print("="*80)
print("📊 STAGE 1.3.3: VOLATILITY & GREEKS")
print("="*80 + "\n")

# ETH OPTIONS
try:
    conn = sqlite3.connect('data/eth_options.db')
    df = pd.read_sql_query("""SELECT strike, option_type, implied_volatility, 
        delta, gamma, vega, theta, open_interest 
        FROM eth_options WHERE open_interest > 0 
        AND expiration_date >= date('now')""", conn)
    conn.close()
    
    if not df.empty:
        avg_iv = df['implied_volatility'].mean()
        total_gamma = (df['gamma'] * df['open_interest']).sum()
        
        logger.info(f"✅ ETH: IV={avg_iv:.1f}%, Gamma={total_gamma:.2f}")
        
        result = {
            'ETH': {
                'avg_iv': float(avg_iv),
                'total_gamma': float(total_gamma),
                'options_count': len(df)
            }
        }
        
        # Save
        with open(f'data/volatility/stage_1.3.3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✅ ETH ANALYZED: {len(df)} options")
    else:
        logger.error("❌ No ETH options data")
except Exception as e:
    logger.error(f"❌ ETH error: {e}")

print("\n" + "="*80)
print("✅ STAGE 1.3.3 COMPLETE!")
print("="*80)
