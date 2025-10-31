import numpy as np
from scipy.stats import norm
from math import log, sqrt, exp
from datetime import datetime, timedelta
import sqlite3
import logging

logger = logging.getLogger(__name__)

class OptionPricing:
    """Расчет опционных параметров по Black-Scholes"""

    @staticmethod
    def calculate_iv(option_type, spot, strike, expiry_days, premium, risk_free=0.02):
        """Расчет подразумеваемой волатильности"""
        try:
            # Итеративный расчет IV
            iv = 0.5
            for _ in range(100):
                d1 = (log(spot/strike) + (risk_free + 0.5*iv**2)*(expiry_days/365)) / (iv*sqrt(expiry_days/365))
                d2 = d1 - iv*sqrt(expiry_days/365)

                if option_type == "CALL":
                    theoretical = spot * norm.cdf(d1) - strike * exp(-risk_free*expiry_days/365) * norm.cdf(d2)
                else:
                    theoretical = strike * exp(-risk_free*expiry_days/365) * norm.cdf(-d2) - spot * norm.cdf(-d1)

                diff = theoretical - premium
                if abs(diff) < 0.01:
                    return iv
                iv -= diff / (spot * norm.pdf(d1) * sqrt(expiry_days/365))
            return iv
        except Exception as e:
            logger.warning(f"IV calculation failed: {e}, using fallback 0.4")
            return 0.4

    @staticmethod
    def calculate_greeks(option_type, spot, strike, expiry_days, iv, risk_free=0.02):
        """Расчет греков"""
        try:
            T = expiry_days/365
            d1 = (log(spot/strike) + (risk_free + 0.5*iv**2)*T) / (iv*sqrt(T))
            d2 = d1 - iv*sqrt(T)

            if option_type == "CALL":
                delta = norm.cdf(d1)
                gamma = norm.pdf(d1) / (spot * iv * sqrt(T))
                theta = (-spot * norm.pdf(d1) * iv / (2*sqrt(T)) - 
                        risk_free * strike * exp(-risk_free*T) * norm.cdf(d2)) / 365
                vega = spot * norm.pdf(d1) * sqrt(T) / 100
            else:
                delta = norm.cdf(d1) - 1
                gamma = norm.pdf(d1) / (spot * iv * sqrt(T))
                theta = (-spot * norm.pdf(d1) * iv / (2*sqrt(T)) + 
                        risk_free * strike * exp(-risk_free*T) * norm.cdf(-d2)) / 365
                vega = spot * norm.pdf(d1) * sqrt(T) / 100

            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 6),
                'theta': round(theta, 4),
                'vega': round(vega, 4)
            }
        except Exception as e:
            logger.warning(f"Greeks calculation failed: {e}, using fallback values")
            return {'delta': 0.5, 'gamma': 0.01, 'theta': -0.05, 'vega': 0.02}

    @staticmethod
    def calculate_pop(option_type, spot, strike, expiry_days, iv, target_return=0.5):
        """Расчет Probability of Profit"""
        try:
            T = expiry_days/365
            if option_type == "CALL":
                target_price = strike + (target_return * spot)
                d2 = (log(spot/target_price) + (0.02 - 0.5*iv**2)*T) / (iv*sqrt(T))
                pop = norm.cdf(d2)
            else:
                target_price = strike - (target_return * spot)
                d2 = (log(spot/target_price) + (0.02 - 0.5*iv**2)*T) / (iv*sqrt(T))
                pop = norm.cdf(-d2)
            return max(0.1, min(0.9, pop))
        except Exception as e:
            logger.warning(f"PoP calculation failed: {e}, using 0.5")
            return 0.5

def generate_option_strategies(asset, signal_type, spot_price, confidence, expiry_days=45):
    """Генерация опционных стратегий на основе сигнала"""
    
    strategies = []
    base_iv = 0.6 if asset in ['BTC', 'ETH'] else 0.8
    
    if signal_type == "BULLISH":
        # 1. LONG CALL Strategy
        strike_call = spot_price * 1.08  # 8% OTM
        premium_call = spot_price * 0.045  # 4.5% премии
        greeks_call = OptionPricing.calculate_greeks("CALL", spot_price, strike_call, expiry_days, base_iv)
        pop_call = OptionPricing.calculate_pop("CALL", spot_price, strike_call, expiry_days, base_iv)
        
        strategies.append({
            'type': 'LONG_CALL',
            'option_type': 'CALL',
            'strike': round(strike_call, 2),
            'expiry_days': expiry_days,
            'premium': round(premium_call, 2),
            'delta': greeks_call['delta'],
            'theta': greeks_call['theta'],
            'vega': greeks_call['vega'],
            'pop': pop_call,
            'max_profit': 'Unlimited',
            'max_loss': round(premium_call, 2),
            'breakeven': round(strike_call + premium_call, 2),
            'description': 'BUY CALL {:.0f} | Premium: ${:.0f}'.format(strike_call, premium_call)
        })
        
        # 2. BULL CALL SPREAD
        strike_short = spot_price * 1.15
        premium_spread = (spot_price * 0.045) - (spot_price * 0.025)
        
        strategies.append({
            'type': 'BULL_CALL_SPREAD',
            'option_type': 'CALL_SPREAD',
            'strike_long': round(strike_call, 2),
            'strike_short': round(strike_short, 2),
            'expiry_days': expiry_days,
            'premium': round(premium_spread, 2),
            'delta': greeks_call['delta'] * 0.6,
            'theta': greeks_call['theta'] * 0.6,  # ДОБАВЛЕНО theta для спреда
            'vega': greeks_call['vega'] * 0.6,   # ДОБАВЛЕНО vega для спреда
            'pop': min(0.95, pop_call * 1.1),
            'max_profit': round((strike_short - strike_call) - premium_spread, 2),
            'max_loss': round(premium_spread, 2),
            'breakeven': round(strike_call + premium_spread, 2),
            'description': 'Call Spread {:.0f}/{:.0f}'.format(strike_call, strike_short)
        })
    
    elif signal_type == "BEARISH":
        # 1. LONG PUT Strategy
        strike_put = spot_price * 0.92  # 8% OTM
        premium_put = spot_price * 0.038  # 3.8% премии
        greeks_put = OptionPricing.calculate_greeks("PUT", spot_price, strike_put, expiry_days, base_iv)
        pop_put = OptionPricing.calculate_pop("PUT", spot_price, strike_put, expiry_days, base_iv)
        
        strategies.append({
            'type': 'LONG_PUT',
            'option_type': 'PUT',
            'strike': round(strike_put, 2),
            'expiry_days': expiry_days,
            'premium': round(premium_put, 2),
            'delta': greeks_put['delta'],
            'theta': greeks_put['theta'],
            'vega': greeks_put['vega'],
            'pop': pop_put,
            'max_profit': round(strike_put - premium_put, 2),
            'max_loss': round(premium_put, 2),
            'breakeven': round(strike_put - premium_put, 2),
            'description': 'BUY PUT {:.0f} | Premium: ${:.0f}'.format(strike_put, premium_put)
        })
        
        # 2. BEAR PUT SPREAD
        strike_short_put = spot_price * 0.85
        premium_spread_put = (spot_price * 0.038) - (spot_price * 0.022)
        
        strategies.append({
            'type': 'BEAR_PUT_SPREAD',
            'option_type': 'PUT_SPREAD',
            'strike_long': round(strike_put, 2),
            'strike_short': round(strike_short_put, 2),
            'expiry_days': expiry_days,
            'premium': round(premium_spread_put, 2),
            'delta': greeks_put['delta'] * 0.6,
            'theta': greeks_put['theta'] * 0.6,  # ДОБАВЛЕНО theta для спреда
            'vega': greeks_put['vega'] * 0.6,   # ДОБАВЛЕНО vega для спреда
            'pop': min(0.95, pop_put * 1.1),
            'max_profit': round((strike_put - strike_short_put) - premium_spread_put, 2),
            'max_loss': round(premium_spread_put, 2),
            'breakeven': round(strike_put - premium_spread_put, 2),
            'description': 'Put Spread {:.0f}/{:.0f}'.format(strike_put, strike_short_put)
        })
    
    return strategies

# Перезаписываем option_pricing.py с исправлениями
with open('option_pricing.py', 'r') as f:
    content = f.read()

# Находим старую функцию generate_option_strategies и заменяем ее
import re
old_pattern = r'def generate_option_strategies\([^)]+\):.*?return strategies'
new_function = re.sub(r'def generate_option_strategies\([^)]+\):.*?return strategies', 
                     inspect.getsource(generate_option_strategies).replace('def generate_option_strategies(asset, signal_type, spot_price, confidence, expiry_days=45):', 'def generate_option_strategies(asset, signal_type, spot_price, confidence, expiry_days=45):'), 
                     content, flags=re.DOTALL)

with open('option_pricing.py', 'w') as f:
    f.write(new_function)

print("✅ Исправлена функция generate_option_strategies - добавлены theta и vega для спредов")
