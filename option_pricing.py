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

class OptionPositionManager:
    """Управление опционными позициями"""

    def __init__(self, db_path='data/oi_signals.db'):
        self.db_path = db_path

    def open_position(self, asset, strategy, option_type, strike, expiry_days,
                     premium, quantity, signal_strength):
        """Открытие новой опционной позиции"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d')
            greeks = OptionPricing.calculate_greeks(option_type, strike * 1.02, strike, expiry_days, 0.6)
            pop = OptionPricing.calculate_pop(option_type, strike * 1.02, strike, expiry_days, 0.6)

            cursor.execute('''
                INSERT INTO option_positions
                (asset, strategy_type, option_type, strike_price, expiry_date,
                 entry_premium, current_premium, quantity, delta, theta, vega, gamma, pop,
                 days_to_expiry, status, signal_strength, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset, strategy, option_type, strike, expiry_date,
                premium, premium, quantity,
                greeks['delta'], greeks['theta'], greeks['vega'], greeks['gamma'], pop,
                expiry_days, 'ACTIVE', signal_strength, 0.0
            ))

            conn.commit()
            conn.close()
            logger.info(f"📝 Открыта новая позиция: {asset} {option_type} @ {strike}")
        except Exception as e:
            logger.error(f"❌ Ошибка открытия позиции: {e}")

    def get_active_positions(self, asset=None):
        """Получение активных позиций"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if asset:
                cursor.execute('''
                    SELECT * FROM option_positions 
                    WHERE status = "ACTIVE" AND asset = ?
                    ORDER BY created_at DESC
                ''', (asset,))
            else:
                cursor.execute('''
                    SELECT * FROM option_positions 
                    WHERE status = "ACTIVE" 
                    ORDER BY created_at DESC
                ''')
            
            positions = cursor.fetchall()
            conn.close()
            return positions
        except Exception as e:
            logger.error(f"❌ Ошибка получения позиций: {e}")
            return []

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
        
        # 2. BULL CALL SPREAD - ИСПРАВЛЕНО: добавлены theta и vega
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
            'theta': greeks_call['theta'] * 0.6,  # ДОБАВЛЕНО
            'vega': greeks_call['vega'] * 0.6,   # ДОБАВЛЕНО
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
        
        # 2. BEAR PUT SPREAD - ИСПРАВЛЕНО: добавлены theta и vega
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
            'theta': greeks_put['theta'] * 0.6,  # ДОБАВЛЕНО
            'vega': greeks_put['vega'] * 0.6,   # ДОБАВЛЕНО
            'pop': min(0.95, pop_put * 1.1),
            'max_profit': round((strike_put - strike_short_put) - premium_spread_put, 2),
            'max_loss': round(premium_spread_put, 2),
            'breakeven': round(strike_put - premium_spread_put, 2),
            'description': 'Put Spread {:.0f}/{:.0f}'.format(strike_put, strike_short_put)
        })
    
    return strategies

def format_option_signal_message(asset, signal_type, confidence, spot_price, strategies):
    """Форматирование опционного сигнала с греками"""
    
    message = """
🎯 **{} OPTIONS SIGNAL: {}**
⏰ {} | 📊 Уверенность: {:.0%}

💰 **СПОТ ЦЕНА:** ${:,.0f}
📈 **IV РАНГ:** 65% | 🕒 **ЭКСПИРАЦИЯ:** 45-60 дней

---

📊 **РЕКОМЕНДУЕМЫЕ СТРАТЕГИИ:**
""".format(
        signal_type, 
        asset,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        confidence,
        spot_price
    )

    for i, strat in enumerate(strategies[:2], 1):
        premium_pct = (strat['premium'] / spot_price) * 100
        
        # Для спредов используем strike_long, для одиночных - strike
        if 'strike_long' in strat:
            strike_display = strat['strike_long']
        else:
            strike_display = strat['strike']
            
        message += """
**{}. {}**
`{}`

📈 **ПАРАМЕТРЫ:**
• Страйк: `${:.0f}`
• Премия: `${:.0f}` ({:.1f}% от спота)
• Break-Even: `${:.0f}`
• Probability of Profit: `{:.1%}`

🎯 **ГРЕКИ:**
• Delta: `{:.3f}` | Theta: `{:.3f}`
• Vega: `{:.3f}` | Max Loss: `${:.0f}`

💼 **РИСК-МЕНЕДЖМЕНТ:**
• Бюджет: `${:.0f}` на контракт
• Фиксация прибыли: 50% от максимальной
• Стоп-лосс: 60% от премии
• Роллирование: за 21 день до экспирации
""".format(
            i,
            strat['type'].replace('_', ' ').title(),
            strat['description'],
            strike_display,
            strat['premium'],
            premium_pct,
            strat['breakeven'],
            strat['pop'],
            strat['delta'],
            strat['theta'],
            strat['vega'],
            strat['max_loss'],
            strat['premium']
        )

    message += """
---

⚠️ **ВАЖНО:** 
• Временной decay (Theta) ускоряется за 30 дней до экспирации
• IV может значительно влиять на премию
• Всегда диверсифицируйте по страйкам и экспирациям
• Максимальный риск = уплаченная премия
"""

    return message

def get_dynamic_expiration_days(signal_type):
    """Динамический выбор дней до экспирации на основе типа сигнала"""
    import random
    if signal_type == "BULLISH":
        return random.randint(30, 60)  # Длинные экспирации для бычьих
    elif signal_type == "BEARISH":
        return random.randint(7, 30)   # Короткие экспирации для медвежьих
    else:
        return random.randint(21, 45)  # Средние для нейтральных

def generate_option_strategy(asset, signal_type, spot_price):
    """Генерация опционной стратегии на основе сигнала"""
    # Получаем динамическую экспирацию
    expiration_days = get_dynamic_expiration_days(signal_type)
    
    if signal_type == "BULLISH":
        return generate_bull_call_spread(asset, spot_price, expiration_days)
    elif signal_type == "BEARISH":
        return generate_bear_put_spread(asset, spot_price, expiration_days)
    else:
        return generate_long_straddle(asset, spot_price, expiration_days)

def generate_bull_call_spread(asset, spot_price, expiration_days):
    """Генерация бычьей стратегии кол спред"""
    return {
        'strategy_type': 'BULL_CALL_SPREAD',
        'long_call_strike': spot_price * 0.95,
        'short_call_strike': spot_price * 1.10,
        'premium_collected': spot_price * 0.02,
        'max_profit': spot_price * 0.08,
        'max_loss': spot_price * 0.02,
        'probability_of_profit': 0.65,
        'expiration_days': expiration_days
    }

def generate_bear_put_spread(asset, spot_price, expiration_days):
    """Генерация медвежьей стратегии пут спред"""
    return {
        'strategy_type': 'BEAR_PUT_SPREAD',
        'long_put_strike': spot_price * 1.05,
        'short_put_strike': spot_price * 0.90,
        'premium_collected': spot_price * 0.015,
        'max_profit': spot_price * 0.06,
        'max_loss': spot_price * 0.015,
        'probability_of_profit': 0.60,
        'expiration_days': expiration_days
    }

def generate_long_straddle(asset, spot_price, expiration_days):
    """Генерация нейтральной стратегии стрэддл"""
    return {
        'strategy_type': 'LONG_STRADDLE',
        'strike': spot_price,
        'call_premium': spot_price * 0.02,
        'put_premium': spot_price * 0.018,
        'total_premium': spot_price * 0.038,
        'max_loss': spot_price * 0.038,
        'probability_of_profit': 0.55,
        'expiration_days': expiration_days
    }
