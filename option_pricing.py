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
    """Бычий Call Spread с оптимальными страйками"""
    # Длинный колл: ATM или немного ITM
    long_strike = spot_price * 0.98  # 2% ITM
    # Короткий колл: дальше OTM для лучшего профита
    short_strike = spot_price * 1.25  # 25% OTM
    
    # Расчёт параметров
    spread_width = short_strike - long_strike
    max_profit = spread_width * 0.6  # ~60% от ширины
    premium = spread_width * 0.3  # ~30% от ширины
    
    return {
        'asset': asset,
        'strategy_type': 'BULL_CALL_SPREAD',
        'long_call_strike': round(long_strike, 2),
        'short_call_strike': round(short_strike, 2),
        'premium_paid': round(premium, 2),
        'max_profit': round(max_profit, 2),
        'max_loss': round(premium, 2),
        'break_even': round(long_strike + premium, 2),
        'probability_of_profit': 0.55,
        'expiration_days': expiration_days,
        'risk_reward_ratio': round(max_profit / premium, 2)
    }


def generate_bear_put_spread(asset, spot_price, expiration_days):
    """Медвежий Put Spread с оптимальными страйками"""
    # Длинный пут: ATM или немного ITM
    long_strike = spot_price * 1.02  # 2% ITM
    # Короткий пут: дальше OTM
    short_strike = spot_price * 0.75  # 25% OTM
    
    # Расчёт параметров
    spread_width = long_strike - short_strike
    max_profit = spread_width * 0.55  # ~55% от ширины
    premium = spread_width * 0.35  # ~35% от ширины
    
    return {
        'asset': asset,
        'strategy_type': 'BEAR_PUT_SPREAD',
        'long_put_strike': round(long_strike, 2),
        'short_put_strike': round(short_strike, 2),
        'premium_paid': round(premium, 2),
        'max_profit': round(max_profit, 2),
        'max_loss': round(premium, 2),
        'break_even': round(long_strike - premium, 2),
        'probability_of_profit': 0.50,
        'expiration_days': expiration_days,
        'risk_reward_ratio': round(max_profit / premium, 2)
    }


def generate_long_straddle(asset, spot_price, expiration_days):
    """Стрэддл для волатильности"""
    strike = spot_price
    
    # Для стрэддла нужна высокая премия
    call_premium = spot_price * 0.04
    put_premium = spot_price * 0.038
    total_premium = call_premium + put_premium
    
    return {
        'asset': asset,
        'strategy_type': 'LONG_STRADDLE',
        'strike': round(strike, 2),
        'call_premium': round(call_premium, 2),
        'put_premium': round(put_premium, 2),
        'total_premium': round(total_premium, 2),
        'max_loss': round(total_premium, 2),
        'upper_breakeven': round(strike + total_premium, 2),
        'lower_breakeven': round(strike - total_premium, 2),
        'probability_of_profit': 0.45,
        'expiration_days': expiration_days
    }


def get_dynamic_expiration_days(asset, signal_type):
    """Динамический выбор РЕАЛЬНОЙ экспирации"""
    from real_expirations import expiration_manager
    
    # Получаем лучшую экспирацию из РЕАЛЬНЫХ данных
    dte = expiration_manager.get_best_expiration(asset, signal_type)
    
    return dte


def generate_option_strategy(asset, signal_type, spot_price):
    """Генерация стратегии с РЕАЛЬНОЙ экспирацией"""
    # Получаем динамическую экспирацию из РЕАЛЬНЫХ данных
    expiration_days = get_dynamic_expiration_days(asset, signal_type)

    if signal_type == "BULLISH":
        return generate_bull_call_spread(asset, spot_price, expiration_days)
    elif signal_type == "BEARISH":
        return generate_bear_put_spread(asset, spot_price, expiration_days)
    else:
        return generate_long_straddle(asset, spot_price, expiration_days)
def generate_option_strategies(asset, signal_type, spot_price, confidence, expiry_days=45):
    """Генерация опционных стратегий с РЕАЛЬНЫМИ экспирациями и широкими спредами"""
    from real_expirations import expiration_manager
    
    # Получаем РЕАЛЬНУЮ экспирацию
    dte = expiration_manager.get_best_expiration(asset, signal_type)
    
    # Генерируем стратегию через НОВЫЕ функции
    if signal_type == "BULLISH":
        strategy = generate_bull_call_spread(asset, spot_price, dte)
    elif signal_type == "BEARISH":
        strategy = generate_bear_put_spread(asset, spot_price, dte)
    else:
        strategy = generate_long_straddle(asset, spot_price, dte)
    
    return [strategy]
def format_option_signal_message(asset, signal_type, confidence, spot_price, strategies):
    """Форматирование опционного сигнала с НОВЫМИ стратегиями"""
    
    message = f"""🎯 {signal_type} OPTIONS SIGNAL: {asset}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 📊 Уверенность: {confidence:.0%}

💰 СПОТ ЦЕНА: ${spot_price:,.2f}
📈 IV РАНГ: 65% | 🕒 ЭКСПИРАЦИЯ: {strategies[0]['expiration_days']} дней

---

📊 РЕКОМЕНДУЕМЫЕ СТРАТЕГИИ:

"""
    
    for i, strat in enumerate(strategies[:2], 1):
        strategy_type = strat['strategy_type']
        premium = strat.get('premium_paid', strat.get('total_premium', 0))
        
        if strategy_type == 'BULL_CALL_SPREAD':
            message += f"""**{i}. Bull Call Spread**
LONG CALL ${strat['long_call_strike']:.2f} / SHORT CALL ${strat['short_call_strike']:.2f}

📈 ПАРАМЕТРЫ:
- Премия: ${premium:.2f} ({premium/spot_price*100:.1f}% от спота)
- Max Profit: ${strat['max_profit']:.2f}
- Max Loss: ${strat['max_loss']:.2f}
- Break-Even: ${strat['break_even']:.2f}
- Risk/Reward: {strat['risk_reward_ratio']:.2f}
- Probability of Profit: {strat['probability_of_profit']:.0%}
- Экспирация: {strat['expiration_days']} дней

💼 РИСК-МЕНЕДЖМЕНТ:
- Бюджет: ${premium:.2f} на спред
- Фиксация прибыли: 50% от max profit
- Стоп-лосс: 60% от премии
- Роллирование: за 21 день до экспирации

"""
        elif strategy_type == 'BEAR_PUT_SPREAD':
            message += f"""**{i}. Bear Put Spread**
LONG PUT ${strat['long_put_strike']:.2f} / SHORT PUT ${strat['short_put_strike']:.2f}

📈 ПАРАМЕТРЫ:
- Премия: ${premium:.2f} ({premium/spot_price*100:.1f}% от спота)
- Max Profit: ${strat['max_profit']:.2f}
- Max Loss: ${strat['max_loss']:.2f}
- Break-Even: ${strat['break_even']:.2f}
- Risk/Reward: {strat['risk_reward_ratio']:.2f}
- Probability of Profit: {strat['probability_of_profit']:.0%}
- Экспирация: {strat['expiration_days']} дней

💼 РИСК-МЕНЕДЖМЕНТ:
- Бюджет: ${premium:.2f} на спред
- Фиксация прибыли: 50% от max profit
- Стоп-лосс: 60% от премии
- Роллирование: за 21 день до экспирации

"""
        elif strategy_type == 'LONG_STRADDLE':
            message += f"""**{i}. Long Straddle**
STRADDLE @ ${strat['strike']:.2f}

📈 ПАРАМЕТРЫ:
- Call Premium: ${strat['call_premium']:.2f}
- Put Premium: ${strat['put_premium']:.2f}
- Total Premium: ${strat['total_premium']:.2f} ({strat['total_premium']/spot_price*100:.1f}% от спота)
- Upper Break-Even: ${strat['upper_breakeven']:.2f}
- Lower Break-Even: ${strat['lower_breakeven']:.2f}
- Probability of Profit: {strat['probability_of_profit']:.0%}
- Экспирация: {strat['expiration_days']} дней

💼 РИСК-МЕНЕДЖМЕНТ:
- Бюджет: ${strat['total_premium']:.2f} на стрэддл
- Max Loss: ${strat['max_loss']:.2f}
- Требуется движение ±{abs(strat['upper_breakeven']-spot_price)/spot_price*100:.1f}%

"""
    
    message += """---

⚠️ ВАЖНО: 
- Временной decay (Theta) ускоряется за 30 дней до экспирации
- IV может значительно влиять на премию
- Всегда диверсифицируйте по страйкам и экспирациям
- Максимальный риск = уплаченная премия
"""
    
    return message
