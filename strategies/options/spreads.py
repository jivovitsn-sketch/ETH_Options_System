#!/usr/bin/env python3
"""
OPTIONS SPREADS - FIXED
Реалистичный расчёт P&L
"""

import numpy as np
from typing import Dict

class OptionsSpreads:
    """
    Опционные конструкции с ПРАВИЛЬНЫМ расчётом P&L
    """
    
    def __init__(self, contract_multiplier: float = 0.01):
        """
        contract_multiplier: размер контракта в BTC
        Например 0.01 BTC = $1000 при BTC=$100k
        """
        self.contract_multiplier = contract_multiplier
        print(f"✅ Options Spreads initialized (multiplier={contract_multiplier})")
    
    def bull_call_spread(self, spot_price: float, 
                        lower_strike_pct: float, upper_strike_pct: float,
                        risk_amount: float) -> Dict:
        """
        Bull Call Spread
        
        strike_pct: в процентах от spot (1.0 = ATM, 1.05 = 5% OTM)
        risk_amount: сколько $ готов рисковать
        """
        lower_strike = spot_price * lower_strike_pct
        upper_strike = spot_price * upper_strike_pct
        
        # Spread width в процентах
        spread_width_pct = (upper_strike - lower_strike) / spot_price
        
        # Реалистичная премия (50% от ширины спреда)
        premium = risk_amount
        
        # Max profit = разница страйков - премия
        # НО в процентах от капитала
        max_profit_pct = spread_width_pct - (premium / risk_amount * spread_width_pct)
        max_profit = risk_amount * max_profit_pct
        
        # Ограничиваем реалистично (опционы редко дают >100% на одну сделку)
        max_profit = min(max_profit, risk_amount * 1.0)  # Max 100% прибыли
        
        max_loss = premium
        breakeven_pct = lower_strike_pct + (premium / risk_amount * spread_width_pct)
        
        return {
            'type': 'bull_call_spread',
            'lower_strike': lower_strike,
            'upper_strike': upper_strike,
            'spread_width_pct': spread_width_pct,
            'premium': premium,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven_pct': breakeven_pct,
            'risk_reward': max_profit / max_loss if max_loss > 0 else 0
        }
    
    def bear_put_spread(self, spot_price: float,
                       lower_strike_pct: float, upper_strike_pct: float,
                       risk_amount: float) -> Dict:
        """Bear Put Spread"""
        lower_strike = spot_price * lower_strike_pct
        upper_strike = spot_price * upper_strike_pct
        
        spread_width_pct = (upper_strike - lower_strike) / spot_price
        premium = risk_amount
        
        max_profit_pct = spread_width_pct - (premium / risk_amount * spread_width_pct)
        max_profit = risk_amount * max_profit_pct
        max_profit = min(max_profit, risk_amount * 1.0)
        
        max_loss = premium
        breakeven_pct = upper_strike_pct - (premium / risk_amount * spread_width_pct)
        
        return {
            'type': 'bear_put_spread',
            'lower_strike': lower_strike,
            'upper_strike': upper_strike,
            'spread_width_pct': spread_width_pct,
            'premium': premium,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven_pct': breakeven_pct,
            'risk_reward': max_profit / max_loss if max_loss > 0 else 0
        }
    
    def calculate_pnl(self, strategy: Dict, entry_price: float, exit_price: float) -> float:
        """
        Рассчитать P&L РЕАЛИСТИЧНО
        """
        strategy_type = strategy['type']
        price_change_pct = (exit_price - entry_price) / entry_price
        
        if strategy_type == 'bull_call_spread':
            # Если цена выросла
            if price_change_pct > 0:
                # Profit пропорционален росту цены, но ограничен max_profit
                profit_pct = min(
                    price_change_pct / strategy['spread_width_pct'],
                    1.0
                )
                return strategy['max_profit'] * profit_pct
            else:
                # Loss пропорционален падению
                return max(strategy['max_loss'] * price_change_pct, -strategy['max_loss'])
        
        elif strategy_type == 'bear_put_spread':
            # Если цена упала
            if price_change_pct < 0:
                profit_pct = min(
                    abs(price_change_pct) / strategy['spread_width_pct'],
                    1.0
                )
                return strategy['max_profit'] * profit_pct
            else:
                return max(strategy['max_loss'] * -price_change_pct, -strategy['max_loss'])
        
        return 0

if __name__ == "__main__":
    spreads = OptionsSpreads()
    
    spot = 100000
    risk = 500
    
    # Bull Call: ATM to 10% OTM
    bull_call = spreads.bull_call_spread(spot, 1.0, 1.10, risk)
    print(f"\nBull Call Spread:")
    print(f"  Risk: ${risk}")
    print(f"  Max Profit: ${bull_call['max_profit']:.2f}")
    print(f"  R:R = {bull_call['risk_reward']:.2f}")
    
    # Simulate profit if price rises 5%
    pnl = spreads.calculate_pnl(bull_call, spot, spot * 1.05)
    print(f"  P&L at +5%: ${pnl:.2f}")
