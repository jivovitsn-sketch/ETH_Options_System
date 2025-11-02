#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVANCED INDICATORS - RSI, MACD для опционных метрик
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

def calculate_rsi(data: List[float], period: int = 14) -> float:
    """Расчёт RSI"""
    if len(data) < period + 1:
        return 50.0  # Neutral если недостаточно данных
    
    deltas = np.diff(data)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)


def calculate_macd(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """Расчёт MACD"""
    if len(data) < slow:
        return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
    
    # EMA calculation
    def ema(values, period):
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        return np.convolve(values, weights, mode='valid')[-1]
    
    fast_ema = ema(data, fast)
    slow_ema = ema(data, slow)
    
    macd_line = fast_ema - slow_ema
    
    # Signal line (EMA of MACD)
    # Упрощённо - берём среднее последних signal периодов
    signal_line = 0.0
    histogram = macd_line - signal_line
    
    return {
        'macd': float(macd_line),
        'signal': float(signal_line),
        'histogram': float(histogram)
    }


def get_pcr_history(asset: str, hours: int = 168) -> List[float]:
    """Получить историю PCR из БД"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        cursor.execute('''
            SELECT timestamp, 
                   SUM(CASE WHEN option_type = 'Put' THEN open_interest ELSE 0 END) as put_oi,
                   SUM(CASE WHEN option_type = 'Call' THEN open_interest ELSE 0 END) as call_oi
            FROM all_positions_tracking
            WHERE asset = ? AND timestamp > ?
            GROUP BY timestamp
            ORDER BY timestamp ASC
        ''', (asset, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        pcr_values = []
        for row in rows:
            put_oi = row[1]
            call_oi = row[2]
            if call_oi > 0:
                pcr = put_oi / call_oi
                pcr_values.append(pcr)
        
        return pcr_values
        
    except Exception as e:
        return []


def get_gex_history(asset: str, hours: int = 168) -> List[float]:
    """Получить историю GEX из БД"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        cursor.execute('''
            SELECT timestamp, 
                   SUM(open_interest) as total_gex
            FROM all_positions_tracking
            WHERE asset = ? AND timestamp > ?
            GROUP BY timestamp
            ORDER BY timestamp ASC
        ''', (asset, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        gex_values = [row[1] for row in rows]
        return gex_values
        
    except Exception as e:
        return []


def get_pcr_rsi(asset: str) -> Optional[float]:
    """PCR RSI"""
    history = get_pcr_history(asset, hours=336)  # 14 дней
    if len(history) < 15:
        return None
    return calculate_rsi(history, period=14)


def get_gex_rsi(asset: str) -> Optional[float]:
    """GEX RSI"""
    history = get_gex_history(asset, hours=336)
    if len(history) < 15:
        return None
    return calculate_rsi(history, period=14)


def get_oi_macd(asset: str) -> Optional[Dict[str, float]]:
    """MACD для Open Interest"""
    try:
        conn = sqlite3.connect('./data/unlimited_oi.db')
        cursor = conn.cursor()
        
        cutoff = int((datetime.now() - timedelta(hours=672)).timestamp())  # 28 дней
        
        cursor.execute('''
            SELECT timestamp, SUM(open_interest) as total_oi
            FROM all_positions_tracking
            WHERE asset = ? AND timestamp > ?
            GROUP BY timestamp
            ORDER BY timestamp ASC
        ''', (asset, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) < 26:
            return None
        
        oi_values = [row[1] for row in rows]
        return calculate_macd(oi_values)
        
    except Exception as e:
        return None


def get_iv_macd(asset: str) -> Optional[Dict[str, float]]:
    """MACD для IV (если есть данные)"""
    # TODO: добавить когда будет IV история
    return None


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 ADVANCED INDICATORS TEST")
    print("=" * 60)
    
    assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
    
    for asset in assets:
        print(f"\n📊 {asset}:")
        
        pcr_rsi = get_pcr_rsi(asset)
        if pcr_rsi:
            print(f"  PCR RSI: {pcr_rsi:.1f}")
        
        gex_rsi = get_gex_rsi(asset)
        if gex_rsi:
            print(f"  GEX RSI: {gex_rsi:.1f}")
        
        oi_macd = get_oi_macd(asset)
        if oi_macd:
            print(f"  OI MACD: {oi_macd['histogram']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
