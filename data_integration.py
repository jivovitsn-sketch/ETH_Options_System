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

def get_max_pain(symbol):
    """Получить данные Max Pain из JSON файлов"""
    try:
        max_pain_dir = './data/max_pain/'
        if not os.path.exists(max_pain_dir):
            return None
        
        files = [f for f in os.listdir(max_pain_dir) if f.startswith(symbol) and f.endswith('.json')]
        if not files:
            return None
        
        latest_file = max(files)
        with open(os.path.join(max_pain_dir, latest_file), 'r') as f:
            data = json.load(f)
        
        return {
            'max_pain_strike': data.get('max_pain_strike'),
            'spot_price': data.get('spot_price'),
            'distance_pct': data.get('distance_pct'),
            'put_call_ratio': data.get('put_call_ratio'),
            'total_oi': data.get('total_oi')
        }
    except Exception as e:
        print(f"Error getting Max Pain data for {symbol}: {e}")
        return None

def get_pcr_data(symbol):
    """Получить данные PCR из JSON файлов"""
    try:
        pcr_dir = './data/pcr/'
        if not os.path.exists(pcr_dir):
            return None
        
        files = [f for f in os.listdir(pcr_dir) if f.startswith(symbol) and f.endswith('.json')]
        if not files:
            return None
        
        latest_file = max(files)
        with open(os.path.join(pcr_dir, latest_file), 'r') as f:
            data = json.load(f)
        
        return {
            'pcr_oi': data.get('pcr_oi'),
            'pcr_rsi': data.get('pcr_rsi'),
            'interpretation': data.get('interpretation')
        }
    except Exception as e:
        print(f"Error getting PCR data for {symbol}: {e}")
        return None

def get_vanna_data(symbol):
    """Получить данные Vanna из JSON файлов"""
    try:
        vanna_dir = './data/vanna/'
        if not os.path.exists(vanna_dir):
            return None
        
        files = [f for f in os.listdir(vanna_dir) if f.startswith(symbol) and f.endswith('.json')]
        if not files:
            return None
        
        latest_file = max(files)
        with open(os.path.join(vanna_dir, latest_file), 'r') as f:
            data = json.load(f)
        
        return {
            'total_vanna': data.get('total_vanna'),
            'interpretation': data.get('interpretation')
        }
    except Exception as e:
        print(f"Error getting Vanna data for {symbol}: {e}")
        return None

def get_iv_rank_data(symbol):
    """Получить данные IV Rank из JSON файлов"""
    try:
        iv_dir = './data/iv_rank/'
        if not os.path.exists(iv_dir):
            return None
        
        files = [f for f in os.listdir(iv_dir) if f.startswith(symbol) and f.endswith('.json')]
        if not files:
            return None
        
        latest_file = max(files)
        with open(os.path.join(iv_dir, latest_file), 'r') as f:
            data = json.load(f)
        
        return {
            'current_iv': data.get('current_iv'),
            'iv_rank': data.get('iv_rank_52w'),
            'iv_percentile': data.get('iv_percentile_52w'),
            'interpretation': data.get('interpretation')
        }
    except Exception as e:
        print(f"Error getting IV Rank data for {symbol}: {e}")
        return None

def get_option_vwap(symbol):
    """Получить OPTION VWAP данные"""
    try:
        from option_vwap_calculator import get_option_vwap
        return get_option_vwap(symbol)
    except Exception as e:
        logger.error(f"Error getting option vwap for {symbol}: {e}")
        return None
