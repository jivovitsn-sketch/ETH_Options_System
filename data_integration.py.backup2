#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATA INTEGRATION - FIXED VERSION
Исправлены PCR, GEX, Max Pain
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ==================== FUTURES ====================

def get_futures_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Фьючерсные данные"""
    try:
        conn = sqlite3.connect('./data/futures.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT price, funding_rate, open_interest
            FROM futures_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (symbol,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'price': row[0],
                'funding_rate': row[1],
                'open_interest': row[2],
                'spot_price': row[0]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting futures data: {e}")
        return None


def get_recent_liquidations(symbol: str, hours: int = 4) -> Optional[Dict[str, Any]]:
    """Ликвидации"""
    try:
        conn = sqlite3.connect('./data/liquidations.db')
        cursor = conn.cursor()
        
        cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        cursor.execute('''
            SELECT side, SUM(qty * price) as total_usd
            FROM liquidations
            WHERE symbol = ? AND timestamp > ?
            GROUP BY side
        ''', (symbol, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        longs = sum(row[1] for row in rows if row[0] == 'Buy')
        shorts = sum(row[1] for row in rows if row[0] == 'Sell')
        
        total = longs + shorts
        ratio = (shorts / longs) if longs > 0 else 999.0
        
        return {
            'longs_liquidated': longs,
            'shorts_liquidated': shorts,
            'total_usd': total,
            'ratio': ratio
        }
    except Exception as e:
        logger.error(f"Error getting liquidations: {e}")
        return None


# ==================== OPTIONS - FIXED ====================

def get_pcr_data(symbol: str) -> Optional[Dict[str, Any]]:
    """PCR - ИСПРАВЛЕНО"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        # Берём последние данные
        cutoff = int((datetime.now() - timedelta(hours=24)).timestamp())
        
        cursor.execute('''
            SELECT 
                option_type,
                SUM(open_interest) as total_oi,
                SUM(volume_24h) as total_volume
            FROM all_positions_tracking
            WHERE asset = ? 
              AND timestamp > ?
              AND open_interest > 0
            GROUP BY option_type
        ''', (symbol, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        put_oi = 0
        call_oi = 0
        put_volume = 0
        call_volume = 0
        
        for row in rows:
            if row[0] == 'Put':
                put_oi = row[1]
                put_volume = row[2]
            elif row[0] == 'Call':
                call_oi = row[1]
                call_volume = row[2]
        
        if call_oi == 0:
            return None
        
        ratio = put_oi / call_oi
        volume_ratio = put_volume / call_volume if call_volume > 0 else 0
        
        return {
            'ratio': ratio,
            'put_oi': put_oi,
            'call_oi': call_oi,
            'put_volume': put_volume,
            'call_volume': call_volume,
            'volume_ratio': volume_ratio
        }
        
    except Exception as e:
        logger.error(f"Error getting PCR for {symbol}: {e}")
        return None


def get_gamma_exposure(symbol: str) -> Optional[Dict[str, Any]]:
    """GEX - ИСПРАВЛЕНО"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        # Берём свежие данные
        cutoff = int((datetime.now() - timedelta(hours=24)).timestamp())
        
        cursor.execute('''
            SELECT 
                strike,
                option_type,
                open_interest,
                spot_price
            FROM all_positions_tracking
            WHERE asset = ?
              AND timestamp > ?
              AND open_interest > 0
            ORDER BY timestamp DESC
            LIMIT 1000
        ''', (symbol, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # Упрощённый расчёт GEX
        spot_price = rows[0][3] if rows else 0
        
        total_gamma = 0
        call_gamma = 0
        put_gamma = 0
        
        for row in rows:
            strike = row[0]
            option_type = row[1]
            oi = row[2]
            
            # Простая gamma: зависит от moneyness
            moneyness = abs(strike - spot_price) / spot_price
            gamma = oi * (1 - moneyness) if moneyness < 0.1 else oi * 0.1
            
            total_gamma += gamma
            
            if option_type == 'Call':
                call_gamma += gamma
            else:
                put_gamma += gamma
        
        return {
            'total_gamma': total_gamma,
            'call_gamma': call_gamma,
            'put_gamma': put_gamma,
            'gamma_ratio': call_gamma / put_gamma if put_gamma > 0 else 0,
            'spot_price': spot_price
        }
        
    except Exception as e:
        logger.error(f"Error getting GEX for {symbol}: {e}")
        return None


def get_max_pain(symbol: str) -> Optional[Dict[str, Any]]:
    """Max Pain - ИСПРАВЛЕНО"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        # Берём данные по всем страйкам
        cutoff = int((datetime.now() - timedelta(hours=24)).timestamp())
        
        cursor.execute('''
            SELECT 
                strike,
                option_type,
                open_interest,
                spot_price
            FROM all_positions_tracking
            WHERE asset = ?
              AND timestamp > ?
              AND open_interest > 0
        ''', (symbol, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        spot_price = rows[0][3]
        
        # Группируем по страйкам
        strikes_data = {}
        for row in rows:
            strike = row[0]
            option_type = row[1]
            oi = row[2]
            
            if strike not in strikes_data:
                strikes_data[strike] = {'calls': 0, 'puts': 0}
            
            if option_type == 'Call':
                strikes_data[strike]['calls'] += oi
            else:
                strikes_data[strike]['puts'] += oi
        
        # Расчёт max pain
        strikes = sorted(strikes_data.keys())
        
        max_pain_price = spot_price
        min_pain = float('inf')
        
        for test_price in strikes:
            total_pain = 0
            
            for strike, data in strikes_data.items():
                # Call pain
                if test_price > strike:
                    total_pain += data['calls'] * (test_price - strike)
                
                # Put pain
                if test_price < strike:
                    total_pain += data['puts'] * (strike - test_price)
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_price = test_price
        
        distance = (max_pain_price - spot_price) / spot_price
        
        return {
            'price': max_pain_price,
            'distance_pct': distance,
            'total_pain': min_pain,
            'spot_price': spot_price
        }
        
    except Exception as e:
        logger.error(f"Error getting Max Pain for {symbol}: {e}")
        return None


def get_vanna_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Vanna данные"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        cutoff = int((datetime.now() - timedelta(hours=24)).timestamp())
        
        cursor.execute('''
            SELECT SUM(open_interest) as total_vanna
            FROM all_positions_tracking
            WHERE asset = ? AND timestamp > ?
        ''', (symbol, cutoff))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return {'total_vanna': row[0]}
        return None
    except:
        return None


def get_iv_rank_data(symbol: str) -> Optional[Dict[str, Any]]:
    """IV Rank - ДОБАВЛЕНО"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        # Берём данные за последний месяц
        cutoff = int((datetime.now() - timedelta(days=30)).timestamp())
        
        cursor.execute('''
            SELECT timestamp, mark_iv
            FROM all_positions_tracking
            WHERE asset = ?
              AND timestamp > ?
              AND mark_iv > 0
            ORDER BY timestamp DESC
        ''', (symbol, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows or len(rows) < 10:
            return None
        
        # Текущая IV
        current_iv = rows[0][1]
        
        # Все IV за период
        all_ivs = [row[1] for row in rows]
        
        # IV Rank = где текущая IV в диапазоне min-max
        min_iv = min(all_ivs)
        max_iv = max(all_ivs)
        
        if max_iv == min_iv:
            iv_rank = 50.0
        else:
            iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
        
        # IV Percentile (сколько дней IV была ниже)
        lower_count = sum(1 for iv in all_ivs if iv < current_iv)
        iv_percentile = (lower_count / len(all_ivs)) * 100
        
        return {
            'rank': iv_rank,
            'percentile': iv_percentile,
            'current_iv': current_iv,
            'min_iv': min_iv,
            'max_iv': max_iv
        }
        
    except Exception as e:
        logger.error(f"Error getting IV Rank for {symbol}: {e}")
        return None


def get_option_vwap(symbol: str) -> Optional[Dict[str, Any]]:
    """Option VWAP"""
    try:
        from option_vwap_calculator import calculate_option_vwap
        return calculate_option_vwap(symbol)
    except:
        return None


# ==================== ADVANCED INDICATORS ====================

def get_pcr_rsi(symbol: str) -> Optional[float]:
    """PCR RSI"""
    try:
        from advanced_indicators import get_pcr_rsi
        return get_pcr_rsi(symbol)
    except:
        return None


def get_gex_rsi(symbol: str) -> Optional[float]:
    """GEX RSI"""
    try:
        from advanced_indicators import get_gex_rsi
        return get_gex_rsi(symbol)
    except:
        return None


def get_oi_macd(symbol: str) -> Optional[Dict]:
    """OI MACD"""
    try:
        from advanced_indicators import get_oi_macd
        return get_oi_macd(symbol)
    except:
        return None
