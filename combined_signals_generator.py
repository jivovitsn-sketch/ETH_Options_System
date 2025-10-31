#!/usr/bin/env python3
"""STAGE 1.3.4: COMBINED SIGNALS GENERATOR"""

import sqlite3, pandas as pd, numpy as np, json, logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

SYMBOLS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
Path('data/signals').mkdir(parents=True, exist_ok=True)

class CombinedSignalsGenerator:
    def __init__(self, symbol):
        self.symbol = symbol
        self.gamma_data = None
        self.max_pain_data = None
        self.spot_price = None
        
    def load_analytics(self):
        """Загрузка Gamma + Max Pain"""
        try:
            conn = sqlite3.connect('data/options_data.db')
            
            # Gamma
            gamma_df = pd.read_sql_query(
                "SELECT * FROM gamma_exposure WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                conn, params=(self.symbol,))
            
            # Max Pain
            mp_df = pd.read_sql_query(
                "SELECT * FROM max_pain WHERE symbol = ? ORDER BY timestamp DESC LIMIT 5",
                conn, params=(self.symbol,))
            
            conn.close()
            
            if not gamma_df.empty:
                self.gamma_data = gamma_df.iloc[0]
            if not mp_df.empty:
                self.max_pain_data = mp_df
                
            return True
        except Exception as e:
            logger.error(f"{self.symbol} load error: {e}")
            return False
    
    def get_spot_price(self):
        """Получение текущей цены"""
        try:
            conn = sqlite3.connect('data/futures_data.db')
            result = pd.read_sql_query(
                "SELECT last_price FROM spot_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                conn, params=(f"{self.symbol}USDT",))
            conn.close()
            
            if not result.empty:
                self.spot_price = float(result['last_price'].iloc[0])
                return True
        except:
            pass
        return False
    
    def generate_signal(self):
        """Генерация торгового сигнала"""
        if not self.gamma_data or self.max_pain_data is None or not self.spot_price:
            return None
        
        # 1. Gamma анализ
        total_gex = float(self.gamma_data['total_gex'])
        gamma_bias = 1 if total_gex > 0 else -1  # Positive = Bullish
        
        # 2. Max Pain анализ
        nearest_mp = float(self.max_pain_data.iloc[0]['max_pain_strike'])
        mp_distance = (nearest_mp - self.spot_price) / self.spot_price * 100
        mp_bias = 1 if mp_distance > 0 else -1  # Above spot = Bullish
        
        # 3. Combined Score (-2 to +2)
        combined_score = gamma_bias + mp_bias
        
        # 4. Генерация сигнала
        if combined_score >= 1:
            signal = 'BUY'
            strength = 'STRONG' if combined_score == 2 else 'MODERATE'
        elif combined_score <= -1:
            signal = 'SELL'
            strength = 'STRONG' if combined_score == -2 else 'MODERATE'
        else:
            signal = 'NEUTRAL'
            strength = 'WEAK'
        
        return {
            'symbol': self.symbol,
            'signal': signal,
            'strength': strength,
            'combined_score': combined_score,
            'spot_price': self.spot_price,
            'gamma_bias': gamma_bias,
            'total_gex': total_gex,
            'max_pain': nearest_mp,
            'mp_distance_pct': mp_distance,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_signal(self, signal_data):
        """Сохранение сигнала"""
        if not signal_data:
            return
        
        # 1. В БД
        try:
            conn = sqlite3.connect('data/oi_signals.db')
            cursor = conn.cursor()
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, signal TEXT, strength TEXT, combined_score REAL,
                spot_price REAL, gamma_bias REAL, total_gex REAL,
                max_pain REAL, mp_distance_pct REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            
            cursor.execute('''INSERT INTO signals 
                (symbol, signal, strength, combined_score, spot_price, gamma_bias,
                 total_gex, max_pain, mp_distance_pct, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (signal_data['symbol'], signal_data['signal'], signal_data['strength'],
                 signal_data['combined_score'], signal_data['spot_price'], 
                 signal_data['gamma_bias'], signal_data['total_gex'],
                 signal_data['max_pain'], signal_data['mp_distance_pct'],
                 signal_data['timestamp']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB save error: {e}")
        
        # 2. В JSON
        filename = f"data/signals/{self.symbol}_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(signal_data, f, indent=2)
    
    def run(self):
        logger.info(f"\n{'='*80}\n🎯 SIGNAL: {self.symbol}\n{'='*80}")
        
        if not self.get_spot_price():
            logger.error(f"❌ {self.symbol}: No spot price")
            return None
        
        if not self.load_analytics():
            logger.error(f"❌ {self.symbol}: No analytics")
            return None
        
        signal = self.generate_signal()
        
        if signal:
            self.save_signal(signal)
            logger.info(f"✅ {self.symbol}: {signal['signal']} ({signal['strength']}) | Score: {signal['combined_score']}")
            return signal
        
        return None

def main():
    print("="*80)
    print("🎯 STAGE 1.3.4: COMBINED SIGNALS GENERATOR")
    print("="*80 + "\n")
    
    results = {}
    for symbol in SYMBOLS:
        try:
            generator = CombinedSignalsGenerator(symbol)
            signal = generator.run()
            results[symbol] = signal if signal else {'status': 'FAILED'}
        except Exception as e:
            logger.error(f"❌ {symbol}: {e}")
            results[symbol] = {'status': 'ERROR', 'error': str(e)}
    
    print("\n" + "="*80)
    print("📊 FINAL SIGNALS")
    print("="*80)
    
    for symbol, signal in results.items():
        if isinstance(signal, dict) and 'signal' in signal:
            print(f"\n✅ {symbol}: {signal['signal']} ({signal['strength']})")
            print(f"   Score: {signal['combined_score']} | Spot: ${signal['spot_price']:.2f}")
        else:
            print(f"\n❌ {symbol}: NO SIGNAL")
    
    print("\n" + "="*80)
    print("✅ STAGE 1.3.4 COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
