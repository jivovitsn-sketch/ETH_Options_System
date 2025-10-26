#!/usr/bin/env python3
"""
РЕАЛЬНЫЙ КАЛЬКУЛЯТОР ОПЦИОНОВ
"""
from datetime import datetime, timedelta
import math

class OptionsCalculator:
    def __init__(self):
        self.risk_free_rate = 0.05  # 5% годовых
    
    def calculate_option_details(self, spot_price, signal_type, dte=60):
        """Реальный расчет опционных параметров"""
        
        # Определяем страйки на основе текущей цены
        if signal_type == "BUY":
            # Bull Call Spread
            long_strike = round(spot_price / 50) * 50  # ATM округленный
            short_strike = long_strike + 200  # OTM +$200
        else:
            # Bear Put Spread  
            long_strike = round(spot_price / 50) * 50  # ATM
            short_strike = long_strike - 200  # OTM -$200
        
        # Экспирация
        expiry_date = datetime.now() + timedelta(days=dte)
        
        # Расчет премий (упрощенная модель Блэка-Шоулза)
        long_premium = self._calculate_premium(spot_price, long_strike, dte, signal_type)
        short_premium = self._calculate_premium(spot_price, short_strike, dte, signal_type)
        
        net_debit = long_premium - short_premium
        max_profit = abs(short_strike - long_strike) - net_debit
        max_loss = net_debit
        
        # Точки безубыточности
        if signal_type == "BUY":
            breakeven = long_strike + net_debit
        else:
            breakeven = long_strike - net_debit
        
        # Take Profit уровни
        tp1_price = breakeven + (max_profit * 0.3)
        tp2_price = breakeven + (max_profit * 0.6) 
        tp3_price = breakeven + (max_profit * 0.9)
        
        tp1_profit = max_profit * 0.3
        tp2_profit = max_profit * 0.6
        tp3_profit = max_profit * 0.9
        
        return {
            'long_strike': long_strike,
            'short_strike': short_strike,
            'expiry_date': expiry_date,
            'dte': dte,
            'net_debit': net_debit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven': breakeven,
            'tp1_price': tp1_price,
            'tp2_price': tp2_price, 
            'tp3_price': tp3_price,
            'tp1_profit': tp1_profit,
            'tp2_profit': tp2_profit,
            'tp3_profit': tp3_profit,
            'roi_potential': (max_profit / net_debit) * 100
        }
    
    def _calculate_premium(self, spot, strike, dte, option_type):
        """Упрощенный расчет премии опциона"""
        
        # Волатильность (примерная для ETH)
        iv = 0.65  # 65% IV
        
        # Время до экспирации в годах
        time_to_expiry = dte / 365.0
        
        # d1 и d2 для Блэка-Шоулза
        d1 = (math.log(spot / strike) + (self.risk_free_rate + 0.5 * iv**2) * time_to_expiry) / (iv * math.sqrt(time_to_expiry))
        d2 = d1 - iv * math.sqrt(time_to_expiry)
        
        # Нормальная CDF (приближение)
        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        
        if option_type in ["BUY", "CALL"]:
            # Call option
            premium = spot * norm_cdf(d1) - strike * math.exp(-self.risk_free_rate * time_to_expiry) * norm_cdf(d2)
        else:
            # Put option
            premium = strike * math.exp(-self.risk_free_rate * time_to_expiry) * norm_cdf(-d2) - spot * norm_cdf(-d1)
        
        return max(premium, 0.01)  # Минимум $0.01

if __name__ == "__main__":
    calc = OptionsCalculator()
    details = calc.calculate_option_details(3939, "BUY", 60)
    
    print("Расчет опциона:")
    for key, value in details.items():
        print(f"  {key}: {value}")
