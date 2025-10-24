#!/usr/bin/env python3
"""
ALL OPTIONS STRATEGIES
8 конструкций + lottery plays
"""

from typing import Dict

class AllOptionStrategies:
    """
    Все 8 опционных стратегий + лотерейки
    """
    
    def __init__(self):
        print("✅ All Option Strategies initialized (8 + lottery)")
    
    # ==================== DIRECTIONAL ====================
    
    def bull_call_spread(self, entry_price: float, risk: float) -> Dict:
        """1. Bull Call Spread - бычья ставка"""
        return {'type': 'bull_call_spread', 'entry': entry_price, 'risk': risk}
    
    def bear_put_spread(self, entry_price: float, risk: float) -> Dict:
        """2. Bear Put Spread - медвежья ставка"""
        return {'type': 'bear_put_spread', 'entry': entry_price, 'risk': risk}
    
    # ==================== NEUTRAL ====================
    
    def iron_condor(self, entry_price: float, risk: float) -> Dict:
        """3. Iron Condor - боковик (нейтральная)"""
        return {'type': 'iron_condor', 'entry': entry_price, 'risk': risk}
    
    def butterfly_spread(self, entry_price: float, risk: float) -> Dict:
        """4. Butterfly - точечная ставка (цена не двинется)"""
        return {'type': 'butterfly', 'entry': entry_price, 'risk': risk}
    
    # ==================== VOLATILITY ====================
    
    def straddle(self, entry_price: float, risk: float) -> Dict:
        """5. Straddle - большое движение в любую сторону"""
        return {'type': 'straddle', 'entry': entry_price, 'risk': risk}
    
    def strangle(self, entry_price: float, risk: float) -> Dict:
        """6. Strangle - дешевле straddle, нужно больше движения"""
        return {'type': 'strangle', 'entry': entry_price, 'risk': risk}
    
    # ==================== TIME-BASED ====================
    
    def calendar_spread(self, entry_price: float, risk: float) -> Dict:
        """7. Calendar Spread - игра на временном распаде"""
        return {'type': 'calendar', 'entry': entry_price, 'risk': risk}
    
    def credit_spread(self, entry_price: float, risk: float, direction: str) -> Dict:
        """8. Credit Spread - получаем премию сразу"""
        return {'type': f'credit_{direction}', 'entry': entry_price, 'risk': risk}
    
    # ==================== LOTTERY ====================
    
    def lottery_call(self, entry_price: float, risk: float) -> Dict:
        """Лотерейка - далекий OTM call (20%+ OTM)"""
        return {'type': 'lottery_call', 'entry': entry_price, 'risk': risk}
    
    def lottery_put(self, entry_price: float, risk: float) -> Dict:
        """Лотерейка - далекий OTM put (20%+ OTM)"""
        return {'type': 'lottery_put', 'entry': entry_price, 'risk': risk}
    
    # ==================== P&L CALCULATOR ====================
    
    def calculate_pnl(self, strategy: Dict, exit_price: float) -> float:
        """
        Универсальный расчёт P&L для всех стратегий
        """
        entry = strategy['entry']
        risk = strategy['risk']
        stype = strategy['type']
        
        price_change = (exit_price - entry) / entry
        
        # DIRECTIONAL
        if stype == 'bull_call_spread':
            if price_change > 0.02: return risk * 1.0      # Max profit
            elif price_change > 0.01: return risk * 0.5
            elif price_change < -0.01: return -risk * 0.5  # Max loss
            else: return risk * price_change * 10
        
        elif stype == 'bear_put_spread':
            if price_change < -0.02: return risk * 1.0
            elif price_change < -0.01: return risk * 0.5
            elif price_change > 0.01: return -risk * 0.5
            else: return -risk * price_change * 10
        
        # NEUTRAL
        elif stype == 'iron_condor':
            # Profit если цена в коридоре ±3%
            if abs(price_change) < 0.03:
                return risk * 0.5  # Max profit = 50% риска
            else:
                return -risk * 1.0  # Max loss
        
        elif stype == 'butterfly':
            # Max profit если цена не двинулась
            if abs(price_change) < 0.01:
                return risk * 1.5  # High R:R
            elif abs(price_change) < 0.03:
                return risk * 0.3
            else:
                return -risk * 1.0
        
        # VOLATILITY
        elif stype == 'straddle':
            # Нужно большое движение
            if abs(price_change) > 0.05:
                return risk * 2.0  # Большая прибыль
            elif abs(price_change) > 0.03:
                return risk * 0.5
            else:
                return -risk * 0.8  # Дорогая премия
        
        elif stype == 'strangle':
            # Дешевле, но нужно ещё больше движения
            if abs(price_change) > 0.07:
                return risk * 2.5
            elif abs(price_change) > 0.04:
                return risk * 0.5
            else:
                return -risk * 0.6
        
        # TIME-BASED
        elif stype == 'calendar':
            # Profit от временного распада
            if abs(price_change) < 0.02:
                return risk * 0.4  # Slow profit
            else:
                return -risk * 0.8
        
        elif stype in ['credit_bullish', 'credit_bearish']:
            # Получили премию, держим если цена в диапазоне
            if abs(price_change) < 0.04:
                return risk * 0.6
            else:
                return -risk * 1.0
        
        # LOTTERY
        elif stype == 'lottery_call':
            # Огромная прибыль или полная потеря
            if price_change > 0.20:  # +20%
                return risk * 10.0  # 10x!
            elif price_change > 0.10:
                return risk * 2.0
            else:
                return -risk * 1.0  # Полная потеря
        
        elif stype == 'lottery_put':
            if price_change < -0.20:
                return risk * 10.0
            elif price_change < -0.10:
                return risk * 2.0
            else:
                return -risk * 1.0
        
        return 0

if __name__ == "__main__":
    strategies = AllOptionStrategies()
    
    entry = 100000
    risk = 500
    
    print("\n📊 TESTING ALL STRATEGIES:")
    print("="*60)
    
    # Test each strategy at +5% move
    test_cases = [
        ('Bull Call', strategies.bull_call_spread(entry, risk), entry * 1.05),
        ('Bear Put', strategies.bear_put_spread(entry, risk), entry * 0.95),
        ('Iron Condor', strategies.iron_condor(entry, risk), entry * 1.02),
        ('Butterfly', strategies.butterfly_spread(entry, risk), entry * 1.00),
        ('Straddle', strategies.straddle(entry, risk), entry * 1.06),
        ('Strangle', strategies.strangle(entry, risk), entry * 1.08),
        ('Calendar', strategies.calendar_spread(entry, risk), entry * 1.01),
        ('Lottery Call', strategies.lottery_call(entry, risk), entry * 1.25),
    ]
    
    for name, strat, exit in test_cases:
        pnl = strategies.calculate_pnl(strat, exit)
        pct_move = (exit - entry) / entry * 100
        print(f"{name:15s} @ {pct_move:+5.1f}% move → P&L: ${pnl:+7.0f} ({pnl/risk*100:+6.0f}%)")
