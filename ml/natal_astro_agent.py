#!/usr/bin/env python3
"""
NATAL ASTRO AGENT
Использует натальные карты для предсказаний
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from core.natal_chart import NatalChartManager

class NatalAstroAgent:
    """
    Агент на основе натальных транзитов
    """
    
    def __init__(self):
        self.natal_manager = NatalChartManager()
        print("✅ Natal Astro Agent initialized")
    
    def predict(self, symbol: str = 'BTCUSDT', date: datetime = None):
        """
        Предсказание на основе натальных транзитов
        """
        if date is None:
            date = datetime.now()
        
        signal = self.natal_manager.get_signal(symbol, date)
        
        return {
            'prediction': signal['direction'],
            'confidence': signal['confidence'],
            'aspects_count': signal.get('aspects_count', 0),
            'trend_score': signal.get('trend_score', 0)
        }

if __name__ == "__main__":
    agent = NatalAstroAgent()
    
    print(f"\n{'='*60}")
    print(f"NATAL ASTRO PREDICTIONS")
    print(f"{'='*60}")
    
    for symbol in ['BTCUSDT', 'ETHUSDT']:
        result = agent.predict(symbol)
        
        print(f"\n{symbol}:")
        print(f"  Direction: {result['prediction']}")
        print(f"  Confidence: {result['confidence']:.2%}")
