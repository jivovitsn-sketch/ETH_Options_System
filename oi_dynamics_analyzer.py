#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OI DYNAMICS ANALYZER - Анализ изменения Open Interest во времени
С учётом экспираций до последней пятницы следующего месяца
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os
from calendar import monthrange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_last_friday_next_month() -> datetime:
    """Получить последнюю пятницу следующего месяца"""
    now = datetime.now()
    
    # Переходим к следующему месяцу
    if now.month == 12:
        next_month = 1
        year = now.year + 1
    else:
        next_month = now.month + 1
        year = now.year
    
    # Находим последний день следующего месяца
    last_day = monthrange(year, next_month)[1]
    last_date = datetime(year, next_month, last_day)
    
    # Идём назад до пятницы (weekday: 0=Mon, 4=Fri)
    while last_date.weekday() != 4:  # 4 = Friday
        last_date -= timedelta(days=1)
    
    # Устанавливаем время экспирации 8:00 UTC
    last_date = last_date.replace(hour=8, minute=0, second=0, microsecond=0)
    
    return last_date


class OIDynamicsAnalyzer:
    """Анализ динамики OI для выявления ранних сигналов"""

    def __init__(self, db_path: str = './data/unlimited_oi.db'):
        self.db_path = db_path
        self.analysis_period_hours = 24  # Анализ за последние 24 часа
        self.max_expiration = get_last_friday_next_month()
        
        logger.info(f"Max expiration date: {self.max_expiration.strftime('%Y-%m-%d %H:%M UTC')}")

    def get_oi_dynamics(self, asset: str) -> Optional[Dict[str, Any]]:
        """Получить динамику OI для актива по всем релевантным экспирациям"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем список экспираций до последней пятницы следующего месяца
            cutoff = int((datetime.now() - timedelta(hours=48)).timestamp())
            max_exp_str = self.max_expiration.strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT DISTINCT expiry_date, MIN(dte) as min_dte
                FROM all_positions_tracking
                WHERE asset = ? 
                  AND timestamp > ?
                  AND expiry_date <= ?
                  AND dte > 0
                GROUP BY expiry_date
                ORDER BY expiry_date ASC
                LIMIT 10
            ''', (asset, cutoff, max_exp_str))
            
            expirations = [(row[0], row[1]) for row in cursor.fetchall()]
            conn.close()
            
            if not expirations:
                logger.warning(f"No expirations found for {asset} up to {max_exp_str}")
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
                'max_expiration': max_exp_str,
                'expirations_count': len(analyses),
                'expirations_analysis': analyses,
                'summary': self._generate_summary(analyses)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing OI dynamics for {asset}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _analyze_expiration_dynamics(self, asset: str, expiry: str, dte: int) -> Optional[Dict[str, Any]]:
        """Анализ динамики для конкретной экспирации"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Берём данные за последние 24 часа по часам
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
        
        # Тренд (линейная регрессия)
        trend = self._calculate_trend([d['total_oi'] for d in time_series])
        calls_trend = self._calculate_trend([d['calls_oi'] for d in time_series])
        puts_trend = self._calculate_trend([d['puts_oi'] for d in time_series])
        
        # Скорость (средняя за час)
        changes = []
        for i in range(1, len(time_series)):
            prev = time_series[i-1]['total_oi']
            curr = time_series[i]['total_oi']
            if prev > 0:
                changes.append((curr - prev) / prev * 100)
        
        velocity = sum(changes) / len(changes) if changes else 0
        
        # Генерируем сигналы
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
        
        # Линейная регрессия
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'FLAT'
        
        slope = numerator / denominator
        
        # Нормализуем slope относительно среднего значения
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
        """Генерация сигналов на основе динамики"""
        
        signals = {
            'primary_signal': 'NEUTRAL',
            'confidence': 0.5,
            'reasoning': [],
            'implications': []
        }
        
        # Сигналы ослабления/укрепления стенки
        if trend == 'STRONG_DOWN' and change_pct < -20:
            signals['primary_signal'] = 'WALL_WEAKENING'
            signals['confidence'] = 0.7
            signals['reasoning'].append(f"Strong OI drop: {change_pct:.1f}% over 24h")
            signals['implications'].append("Wall magnetic effect weakening")
            signals['implications'].append("Increased breakout probability")
            
        elif trend == 'DOWN' and change_pct < -10:
            signals['primary_signal'] = 'WALL_WEAKENING'
            signals['confidence'] = 0.55
            signals['reasoning'].append(f"OI dropping: {change_pct:.1f}%")
            
        elif trend == 'STRONG_UP' and change_pct > 20:
            signals['primary_signal'] = 'WALL_STRENGTHENING'
            signals['confidence'] = 0.7
            signals['reasoning'].append(f"Strong OI growth: +{change_pct:.1f}%")
            signals['implications'].append("Wall magnetic effect strengthening")
            signals['implications'].append("Increased bounce probability")
            
        elif trend == 'UP' and change_pct > 10:
            signals['primary_signal'] = 'WALL_STRENGTHENING'
            signals['confidence'] = 0.55
            signals['reasoning'].append(f"OI growing: +{change_pct:.1f}%")
        
        # Сигналы дисбаланса
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
        
        # Корректировка на DTE
        if dte < 7:
            signals['reasoning'].append(f"Near expiration (DTE: {dte})")
            signals['confidence'] = min(0.8, signals['confidence'] + 0.05)
        
        # Высокая скорость
        if abs(velocity) > 5:
            signals['reasoning'].append(f"High velocity: {velocity:.1f}%/hour")
            signals['confidence'] = min(0.85, signals['confidence'] + 0.1)
        
        return signals

    def _generate_summary(self, analyses: Dict) -> Dict[str, Any]:
        """Сводка по всем экспирациям"""
        if not analyses:
            return {'overall_signal': 'NO_DATA', 'confidence': 0.0}
        
        signals = []
        confidences = []
        
        for exp, analysis in analyses.items():
            signal = analysis['signals']['primary_signal']
            confidence = analysis['signals']['confidence']
            
            if signal != 'NEUTRAL' and confidence > 0.5:
                signals.append(signal)
                confidences.append(confidence)
        
        if not signals:
            return {'overall_signal': 'NEUTRAL', 'confidence': 0.5}
        
        avg_confidence = sum(confidences) / len(confidences)
        
        # Преобладающий сигнал
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
    
    # Показываем диапазон анализа
    max_exp = get_last_friday_next_month()
    print(f"\n📅 Analysis period:")
    print(f"   Today: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"   Max expiration: {max_exp.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   (Last Friday of next month at 8:00 UTC)")
    
    analyzer = OIDynamicsAnalyzer()
    
    for asset in ['BTC', 'ETH', 'XRP', 'SOL', 'DOGE', 'MNT']:
        print(f"\n📊 {asset}:")
        print("-" * 40)
        
        analysis = analyzer.get_oi_dynamics(asset)
        
        if analysis and analysis.get('summary', {}).get('overall_signal') != 'NO_DATA':
            summary = analysis['summary']
            print(f"  Overall: {summary['overall_signal']} ({summary['confidence']:.0%})")
            print(f"  Expirations: {summary['expirations_analyzed']}")
            print(f"  Active signals: {summary['active_signals']}")
            
            # Детали по экспирациям
            for exp, exp_analysis in list(analysis['expirations_analysis'].items())[:3]:
                signals = exp_analysis['signals']
                oi = exp_analysis['oi_analysis']
                dte = exp_analysis['dte']
                print(f"    {exp} (DTE:{dte}): {signals['primary_signal']} | OI: {oi['change_pct']:+.1f}%")
        else:
            print(f"  ⚠️ No dynamics data")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
