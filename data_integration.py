import sqlite3
import json
import os
from datetime import datetime, timedelta

def get_futures_data(symbol):
    try:
        conn = sqlite3.connect('./data/futures_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT last_price, volume_24h, open_interest, funding_rate FROM futures_ticker WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (f"{symbol}USDT",))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {'price': result[0], 'volume_24h': result[1], 'open_interest': result[2], 'funding_rate': result[3]}
        return None
    except Exception as e:
        print(f"Error getting futures data for {symbol}: {e}")
        return None

def get_recent_liquidations(symbol, hours=4):
    try:
        conn = sqlite3.connect('./data/futures_data.db')
        cursor = conn.cursor()
        since_ts = int((datetime.now() - timedelta(hours=hours)).timestamp())
        cursor.execute("SELECT side, SUM(value) as total_value, COUNT(*) as count FROM liquidations WHERE symbol = ? AND timestamp > ? GROUP BY side", (f"{symbol}USDT", since_ts))
        result = cursor.fetchall()
        conn.close()
        liquidations = {'long': 0, 'short': 0, 'total_count': 0}
        for side, value, count in result:
            if side == 'Buy': liquidations['long'] = value
            elif side == 'Sell': liquidations['short'] = value
            liquidations['total_count'] += count
        liquidations['ratio'] = liquidations['long'] / liquidations['short'] if liquidations['short'] > 0 else 999
        return liquidations
    except Exception as e:
        print(f"Error getting liquidations for {symbol}: {e}")
        return {'long': 0, 'short': 0, 'total_count': 0, 'ratio': 1}

def get_gamma_exposure(symbol):
    try:
        gex_dir = './data/gex/'
        if not os.path.exists(gex_dir): return None
        files = [f for f in os.listdir(gex_dir) if f.startswith(symbol) and f.endswith('.json')]
        if not files: return None
        latest_file = max(files)
        with open(os.path.join(gex_dir, latest_file), 'r') as f:
            data = json.load(f)
        return {'spot_price': data.get('spot_price'), 'total_gex': data.get('total_gex'), 'zero_gamma_level': data.get('zero_gamma_level'), 'gex_by_strike': data.get('gex_by_strike', {})}
    except Exception as e:
        print(f"Error getting GEX data for {symbol}: {e}")
        return None

def analyze_funding_signal(funding_rate):
    """Анализ сигнала по funding rate"""
    if funding_rate is None:
        return "📊 НЕТ ДАННЫХ"
    
    if abs(funding_rate) > 0.0005:  # 0.05%
        return "🚨 ЭКСТРЕМАЛЬНЫЙ ФАНДИНГ"
    elif abs(funding_rate) > 0.0002:  # 0.02%
        return "⚠️ ВЫСОКИЙ ФАНДИНГ"
    elif abs(funding_rate) > 0.0001:  # 0.01%
        return "📊 ПОВЫШЕННЫЙ ФАНДИНГ"
    return "✅ НОРМАЛЬНЫЙ ФАНДИНГ"

def analyze_liquidation_signal(liquidations):
    """Анализ сигнала по ликвидациям"""
    if liquidations['total_count'] == 0:
        return "📊 НЕТ ЛИКВИДАЦИЙ"
    
    if liquidations['ratio'] > 3:
        return "🔥 ПРЕОБЛАДАЮТ ЛОНГ ЛИКВИДАЦИИ (медвежий)"
    elif liquidations['ratio'] < 0.33:
        return "🔥 ПРЕОБЛАДАЮТ ШОРТ ЛИКВИДАЦИИ (бычий)"
    elif liquidations['ratio'] > 1.5:
        return "⚠️ БОЛЬШЕ ЛОНГ ЛИКВИДАЦИЙ"
    elif liquidations['ratio'] < 0.67:
        return "⚠️ БОЛЬШЕ ШОРТ ЛИКВИДАЦИЙ"
    
    return "⚖️ БАЛАНС ЛИКВИДАЦИЙ"

def analyze_gamma_signal(gex_data, current_price):
    """Анализ сигнала по Gamma Exposure"""
    if not gex_data or not gex_data.get('zero_gamma_level'):
        return "📊 GEX ДАННЫЕ НЕДОСТУПНЫ"
    
    zero_gamma = gex_data['zero_gamma_level']
    diff_pct = (current_price - zero_gamma) / zero_gamma * 100
    
    if diff_pct > 2:
        return f"🟢 ЦЕНА ВЫШЕ ZERO GAMMA (+{diff_pct:.1f}%)"
    elif diff_pct < -2:
        return f"🔴 ЦЕНА НИЖЕ ZERO GAMMA ({diff_pct:.1f}%)"
    elif abs(diff_pct) < 0.5:
        return f"🎯 ЦЕНА ВБЛИЗИ ZERO GAMMA"
    
    return f"📊 ЦЕНА ОТ ZERO GAMMA: {diff_pct:.1f}%"

def check_critical_alerts(asset):
    """Проверка критических условий для алертов"""
    alerts = []
    
    futures_data = get_futures_data(asset)
    liquidations = get_recent_liquidations(asset, hours=1)
    
    if futures_data and futures_data.get('funding_rate') and abs(futures_data['funding_rate']) > 0.001:
        alerts.append(f"🚨 КРИТИЧЕСКИЙ ФАНДИНГ: {futures_data['funding_rate']*10000:.1f} bp")
    
    if liquidations['total_count'] > 1000:
        alerts.append(f"🔥 МАССОВЫЕ ЛИКВИДАЦИИ: {liquidations['total_count']} сделок")
    
    if liquidations['ratio'] > 5 or liquidations['ratio'] < 0.2:
        alerts.append(f"⚡ ДИСБАЛАНС ЛИКВИДАЦИЙ: ratio = {liquidations['ratio']:.1f}")
    
    return alerts
