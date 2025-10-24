#!/usr/bin/env python3
"""
ASTRO AGENT
Финансовые предсказания на основе астрологии
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from core.aspects_calculator import AspectsCalculator

class AstroAgent:
    """
    Агент астрологических предсказаний
    """
    
    def __init__(self):
        self.aspects_calc = AspectsCalculator()
        print("✅ Astro Agent initialized")
    
    def predict(self, date: datetime = None):
        """
        Предсказание на основе астрологии
        """
        if date is None:
            date = datetime.now()
        
        # Get market direction from aspects
        market = self.aspects_calc.get_market_direction(date)
        
        direction = market['direction']
        strength = market['strength']
        volatility = market['volatility']
        
        # Adjust confidence based on volatility
        # High volatility = less confidence
        if volatility > 1.5:
            strength *= 0.8
        elif volatility < 0.8:
            strength *= 1.1
        
        strength = min(strength, 0.85)  # Cap at 85%
        
        return {
            'prediction': direction,
            'confidence': strength,
            'volatility': volatility,
            'aspects_count': market.get('aspects_count', 0)
        }

if __name__ == "__main__":
    agent = AstroAgent()
    
    # Test
    result = agent.predict()
    
    print(f"\n{'='*60}")
    print(f"ASTRO PREDICTION:")
    print(f"  Direction: {result['prediction']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Volatility: {result['volatility']:.2f}x")
    print(f"  Aspects: {result['aspects_count']}")
    print(f"{'='*60}")
