#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OI DYNAMICS ANALYZER - Анализ изменения Open Interest во времени
СКОЛЬЗЯЩЕЕ ОКНО: Всегда анализируем экспирации в следующие 45 дней
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OIDynamicsAnalyzer:
    """Анализ динамики OI для выявления ранних сигналов"""

    def __init__(self, db_path: str = './data/unlimited_oi.db'):
        self.db_path = db_path
        self.analysis_period_hours = 24  # Анализ за последние 24 часа
        self.days_forward = 45  # Скользящее окно: следующие 45 дней
        
        # Вычисляем динамическую дату
        self.max_expiration = datetime.now() + timedelta(days=self.days_forward)
        
        logger.info(f"📅 Dynamic window: {datetime.now().strftime('%Y-%m-%d')} → {self.max_expiration.strftime('%Y-%m-%d')} (next {self.days_forward} days)")

    def get_oi_dynamics(self, asset: str) -> Optional[Dict[str, Any]]:
        """Получить динамику OI для актива по всем релевантным экспирациям"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем список экспираций в следующие 45 дней
            cutoff = int((datetime.now() - timedelta(hours=48)).timestamp())
            max_exp_str = self.max_expiration.strftime('%Y-%m-%d')
            now_str = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT DISTINCT expiry_date, MIN(dte) as min_dte
                FROM all_positions_tracking
                WHERE asset = ? 
                  AND timestamp > ?
                  AND expiry_date >= ?
                  AND expiry_date <= ?
                  AND dte > 0
                GROUP BY expiry_date
                ORDER BY expiry_date ASC
                LIMIT 15
            ''', (asset, cutoff, now_str, max_exp_str))
            
            expirations = [(row[0], row[1]) for row in cursor.fetchall()]
            conn.close()
            
            if not expirations:
                logger.warning(f"No expirations for {asset} in rolling window")
                return None
            
            # Анализируем каждую экспирацию
            analyses = {}
            for expiry, dte in expirations:
                analysis = self._analyze_expiration_dynamics(asset, expiry, dte)
                if analysis:
                    analyses[expiry] = analysis
            
            return {
                'asset': asset,
                'timestamp': datetime.now().isoformat(),
                'analysis_window_days': self.days_forward,
                'window_start': now_str,
                'window_end': max_exp_str,
                'expirations_count': len(analyses),
                'expirations_analysis': analyses,
                'summary': self._generate_summary(analyses)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing OI dynamics for {asset}: {e}")
            return None

    def _analyze_expiration_dynamics(self, asset: str, expiry: str, dte: int) -> Optional[Dict[str, Any]]:
        """Анализ динамики для конкретной экспирации"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = int((datetime.now() - timedelta(hours=24)).timestamp())
            
            cursor.execute('''
                SELECT 
                    timestamp,
                    SUM(open_interest) as total_oi,
                    SUM(CASE WHEN option_type = 'Call' THEN open_interest ELSE 0 END) as calls_oi,
                    SUM(CASE WHEN option_type = 'Put' THEN open_interest ELSE 0 END) as puts_oi
                FROM all_positions_tracking
                WHERE asset = ? 
                  AND expiry_date = ?
                  AND timestamp > ?
                GROUP BY timestamp
                ORDER BY timestamp
            ''', (asset, expiry, cutoff))
            
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) < 3:
                return None
            
            # Группируем по часам
            hourly_data = {}
            for row in rows:
                ts = datetime.fromtimestamp(row[0])
                hour_key = ts.replace(minute=0, second=0, microsecond=0)
                
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = {
                        'total_oi': [],
                        'calls_oi': [],
                        'puts_oi': []
                    }
                
                hourly_data[hour_key]['total_oi'].append(row[1])
                hourly_data[hour_key]['calls_oi'].append(row[2])
                hourly_data[hour_key]['puts_oi'].append(row[3])
            
            # Усредняем по часам
            time_series = []
            for hour in sorted(hourly_data.keys()):
                data = hourly_data[hour]
                time_series.append({
                    'timestamp': hour,
                    'total_oi': sum(data['total_oi']) / len(data['total_oi']),
                    'calls_oi': sum(data['calls_oi']) / len(data['calls_oi']),
                    'puts_oi': sum(data['puts_oi']) / len(data['puts_oi'])
                })
            
            if len(time_series) < 3:
                return None
            
            return self._analyze_time_series(time_series, expiry, dte)
            
        except Exception as e:
            logger.error(f"Error analyzing expiration {expiry}: {e}")
            return None

    def _analyze_time_series(self, time_series: List[Dict], expiry: str, dte: int) -> Dict[str, Any]:
        """Анализ временного ряда OI"""
        
        initial = time_series[0]
        current = time_series[-1]
        
        # Изменение OI
        total_change = ((current['total_oi'] - initial['total_oi']) / initial['total_oi'] * 100) if initial['total_oi'] > 0 else 0
        calls_change = ((current['calls_oi'] - initial['calls_oi']) / initial['calls_oi'] * 100) if initial['calls_oi'] > 0 else 0
        puts_change = ((current['puts_oi'] - initial['puts_oi']) / initial['puts_oi'] * 100) if initial['puts_oi'] > 0 else 0
        
        # Тренд
        trend = self._calculate_trend([d['total_oi'] for d in time_series])
        calls_trend = self._calculate_trend([d['calls_oi'] for d in time_series])
        puts_trend = self._calculate_trend([d['puts_oi'] for d in time_series])
        
        # Скорость
        changes = []
        for i in range(1, len(time_series)):
            prev = time_series[i-1]['total_oi']
            curr = time_series[i]['total_oi']
            if prev > 0:
                changes.append((curr - prev) / prev * 100)
        
        velocity = sum(changes) / len(changes) if changes else 0
        
        signals = self._generate_signals(
            trend, total_change, calls_trend, puts_trend, 
            calls_change, puts_change, velocity, dte
        )
        
        return {
            'expiry': expiry,
            'dte': dte,
            'oi_analysis': {
                'current_oi': current['total_oi'],
                'initial_oi': initial['total_oi'],
                'change_pct': total_change,
                'calls_change_pct': calls_change,
                'puts_change_pct': puts_change,
                'trend': trend,
                'calls_trend': calls_trend,
                'puts_trend': puts_trend,
                'velocity': velocity,
                'data_points': len(time_series)
            },
            'signals': signals
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Расчёт тренда"""
        if len(values) < 3:
            return 'INSUFFICIENT_DATA'
        
        n = len(values)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'FLAT'
        
        slope = numerator / denominator
        normalized_slope = slope / y_mean if y_mean != 0 else 0
        
        if normalized_slope > 0.01:
            return 'STRONG_UP'
        elif normalized_slope > 0.002:
            return 'UP'
        elif normalized_slope < -0.01:
            return 'STRONG_DOWN'
        elif normalized_slope < -0.002:
            return 'DOWN'
        else:
            return 'FLAT'

    def _generate_signals(self, trend: str, change_pct: float,
                         calls_trend: str, puts_trend: str,
                         calls_change: float, puts_change: float,
                         velocity: float, dte: int) -> Dict[str, Any]:
        """Генерация сигналов"""
        
        signals = {
            'primary_signal': 'NEUTRAL',
            'confidence': 0.5,
            'reasoning': [],
            'implications': []
        }
        
        if trend == 'STRONG_DOWN' and change_pct < -20:
            signals['primary_signal'] = 'WALL_WEAKENING'
            signals['confidence'] = 0.7
            signals['reasoning'].append(f"Strong OI drop: {change_pct:.1f}%")
            signals['implications'].append("Breakout probability increased")
            
        elif trend == 'DOWN' and change_pct < -10:
            signals['primary_signal'] = 'WALL_WEAKENING'
            signals['confidence'] = 0.55
            signals['reasoning'].append(f"OI dropping: {change_pct:.1f}%")
            
        elif trend == 'STRONG_UP' and change_pct > 20:
            signals['primary_signal'] = 'WALL_STRENGTHENING'
            signals['confidence'] = 0.7
            signals['reasoning'].append(f"Strong OI growth: +{change_pct:.1f}%")
            signals['implications'].append("Bounce probability increased")
            
        elif trend == 'UP' and change_pct > 10:
            signals['primary_signal'] = 'WALL_STRENGTHENING'
            signals['confidence'] = 0.55
            signals['reasoning'].append(f"OI growing: +{change_pct:.1f}%")
        
        if calls_trend in ['STRONG_UP', 'UP'] and puts_trend in ['STRONG_DOWN', 'DOWN']:
            if calls_change > 15 and puts_change < -10:
                signals['primary_signal'] = 'BULLISH_SENTIMENT'
                signals['confidence'] = 0.65
                signals['reasoning'].append(f"Calls +{calls_change:.1f}%, Puts {puts_change:.1f}%")
        
        elif puts_trend in ['STRONG_UP', 'UP'] and calls_trend in ['STRONG_DOWN', 'DOWN']:
            if puts_change > 15 and calls_change < -10:
                signals['primary_signal'] = 'BEARISH_SENTIMENT'
                signals['confidence'] = 0.65
                signals['reasoning'].append(f"Puts +{puts_change:.1f}%, Calls {calls_change:.1f}%")
        
        if dte < 7:
            signals['reasoning'].append(f"Near expiration (DTE: {dte})")
            signals['confidence'] = min(0.8, signals['confidence'] + 0.05)
        
        if abs(velocity) > 5:
            signals['reasoning'].append(f"High velocity: {velocity:.1f}%/hour")
            signals['confidence'] = min(0.85, signals['confidence'] + 0.1)
        
        return signals

    def _generate_summary(self, analyses: Dict) -> Dict[str, Any]:
        """Сводка"""
        if not analyses:
            return {
                'overall_signal': 'NO_DATA',
                'confidence': 0.0,
                'expirations_analyzed': 0,
                'active_signals': 0
            }
        
        signals = []
        confidences = []
        
        for exp, analysis in analyses.items():
            signal = analysis['signals']['primary_signal']
            confidence = analysis['signals']['confidence']
            
            if signal != 'NEUTRAL' and confidence > 0.5:
                signals.append(signal)
                confidences.append(confidence)
        
        if not signals:
            return {
                'overall_signal': 'NEUTRAL',
                'confidence': 0.5,
                'expirations_analyzed': len(analyses),
                'active_signals': 0
            }
        
        avg_confidence = sum(confidences) / len(confidences)
        
        from collections import Counter
        signal_counts = Counter(signals)
        overall_signal = signal_counts.most_common(1)[0][0]
        
        return {
            'overall_signal': overall_signal,
            'confidence': avg_confidence,
            'expirations_analyzed': len(analyses),
            'active_signals': len(signals)
        }


def get_oi_dynamics_data(asset: str) -> Optional[Dict[str, Any]]:
    """Функция для DataIntegrator"""
    analyzer = OIDynamicsAnalyzer()
    analysis = analyzer.get_oi_dynamics(asset)
    
    if analysis:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/oi_dynamics/{asset}_dynamics_{timestamp}.json"
        
        os.makedirs('data/oi_dynamics', exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"✅ OI dynamics saved: {filename}")
    
    return analysis


if __name__ == '__main__':
    print("📈 OI DYNAMICS ANALYZER TEST")
    print("=" * 60)
    
    now = datetime.now()
    max_exp = now + timedelta(days=45)
    print(f"\n📅 СКОЛЬЗЯЩЕЕ ОКНО (ROLLING WINDOW):")
    print(f"   Today: {now.strftime('%Y-%m-%d')}")
    print(f"   Window: Next 45 days")
    print(f"   Until: {max_exp.strftime('%Y-%m-%d')}")
    print(f"   ⚡ Updates daily automatically!")
    
    analyzer = OIDynamicsAnalyzer()
    
    for asset in ['BTC', 'ETH', 'XRP', 'SOL', 'DOGE', 'MNT']:
        print(f"\n📊 {asset}:")
        print("-" * 40)
        
        analysis = analyzer.get_oi_dynamics(asset)
        
        if analysis and analysis.get('summary', {}).get('overall_signal') != 'NO_DATA':
            summary = analysis['summary']
            print(f"  Signal: {summary['overall_signal']:20s} ({summary['confidence']:.0%})")
            print(f"  Expirations: {summary['expirations_analyzed']}")
            print(f"  Active signals: {summary['active_signals']}")
            print(f"  Window: {analysis['window_start']} → {analysis['window_end']}")
            
            for exp, exp_analysis in list(analysis['expirations_analysis'].items())[:2]:
                signals = exp_analysis['signals']
                oi = exp_analysis['oi_analysis']
                dte = exp_analysis['dte']
                print(f"    {exp} (DTE:{dte:2d}): {signals['primary_signal']:20s} | OI: {oi['change_pct']:+6.1f}%")
        else:
            print(f"  ⚠️ No dynamics data")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
