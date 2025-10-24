#!/usr/bin/env python3
"""SIGNAL GENERATOR - Генерация торговых сигналов"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import yaml

class SignalGenerator:
    def __init__(self):
        config_path = Path(__file__).parent.parent / 'configs' / 'strategies.yaml'
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.min_confidence = 0.65
        print("✅ Signal Generator initialized")
    
    def load_price_data(self, symbol: str, days: int = 30):
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / symbol
        
        if not data_dir.exists():
            return pd.DataFrame()
        
        files = sorted(data_dir.glob("*.csv"))[-days:]
        if not files:
            return pd.DataFrame()
        
        dfs = []
        for file in files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        result = pd.concat(dfs, ignore_index=True)
        result['timestamp'] = pd.to_datetime(result['timestamp'])
        return result.sort_values('timestamp')
    
    def calculate_trend(self, df: pd.DataFrame):
        if df.empty or len(df) < 50:
            return {'trend': 'NEUTRAL', 'strength': 0.5}
        
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        latest = df.iloc[-1]
        
        if latest['close'] > latest['sma20'] > latest['sma50']:
            return {'trend': 'BULLISH', 'strength': 0.8}
        elif latest['close'] < latest['sma20'] < latest['sma50']:
            return {'trend': 'BEARISH', 'strength': 0.8}
        else:
            return {'trend': 'NEUTRAL', 'strength': 0.5}
    
    def generate_signal(self, symbol: str):
        print(f"\n{'='*60}")
        print(f"🎯 Generating signal for {symbol}")
        print(f"{'='*60}")
        
        df = self.load_price_data(symbol, days=30)
        
        if df.empty:
            return {'action': 'HOLD', 'reason': 'No price data'}
        
        trend = self.calculate_trend(df)
        print(f"📊 Trend: {trend['trend']} ({trend['strength']:.0%})")
        
        if trend['trend'] == 'NEUTRAL':
            return {'action': 'HOLD', 'reason': 'No clear trend'}
        
        spot = df['close'].iloc[-1]
        direction = trend['trend']
        construction = 'bull_call_spread' if direction == 'BULLISH' else 'bear_put_spread'
        
        signal = {
            'action': 'OPEN',
            'symbol': symbol,
            'direction': direction,
            'construction': construction,
            'spot_price': spot,
            'position_size': 0.05,
            'confidence': trend['strength']
        }
        
        print(f"✅ SIGNAL: {construction} - {direction} ({trend['strength']:.0%})")
        return signal

if __name__ == "__main__":
    print("Signal Generator ready")
