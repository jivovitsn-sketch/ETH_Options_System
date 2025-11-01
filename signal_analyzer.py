#!/usr/bin/env python3
"""
Signal Analyzer v3 - оптимизирован для бэктеста Stage 1.5
"""

import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime

class SignalAnalyzer:
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger('SignalAnalyzer')
        self.config = config or self._get_default_config()
        self.signal_history = []

    def _get_default_config(self) -> Dict[str, Any]:
        """Получить конфигурацию по умолчанию для бэктеста"""
        return {
            # Веса групп (будут оптимизироваться)
            'futures_weight': 0.35,
            'options_weight': 0.45,
            'timing_weight': 0.20,
            
            # Пороги (будут оптимизироваться)
            'min_confidence': 0.60,  # Оптимизировано для текущих данных
            'strong_threshold': 0.75,
            'min_data_sources': 2,
            
            # Параметры для ML оптимизации
            'pcr_bullish_threshold': 0.8,
            'pcr_bearish_threshold': 1.2,
            'max_pain_threshold': 0.02,  # 2%
            'vanna_threshold': 0
        }

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализировать данные и генерировать сигнал"""
        self.logger.info(f"Analyzing data for {data.get('asset', 'unknown')}")

        # Реальный анализ на основе доступных данных
        futures_analysis = self._analyze_futures(data)
        options_analysis = self._analyze_options(data)
        timing_analysis = self._analyze_timing(data)

        # Взвешенная уверенность
        total_confidence = (
            futures_analysis['confidence'] * self.config['futures_weight'] +
            options_analysis['confidence'] * self.config['options_weight'] +
            timing_analysis['confidence'] * self.config['timing_weight']
        )

        # Определение сигнала
        signal_type = self._determine_signal_type(
            futures_analysis, options_analysis, timing_analysis, total_confidence
        )

        signal_result = {
            'signal_type': signal_type,
            'confidence': round(total_confidence, 3),
            'timestamp': datetime.now().isoformat(),
            'asset': data.get('asset', 'unknown'),
            'components': {
                'futures': futures_analysis,
                'options': options_analysis,
                'timing': timing_analysis
            },
            'reasoning': self._build_reasoning(signal_type, total_confidence, futures_analysis, options_analysis),
            'data_quality': data.get('data_quality', {})
        }
        
        # Сохраняем для истории (для бэктеста)
        self.signal_history.append(signal_result)
        
        return signal_result

    def _analyze_futures(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ фьючерсных данных"""
        indicators_used = []
        confidence = 0.5
        direction = 'neutral'
        details = []

        # Используем опционные данные как прокси пока нет фьючерсных
        if data.get('pcr'):
            pcr_data = data['pcr']
            if 'ratio' in pcr_data:
                pcr_ratio = pcr_data['ratio']
                indicators_used.append('pcr_proxy')
                
                # Адаптивная логика на основе конфига
                if pcr_ratio > self.config['pcr_bearish_threshold']:
                    direction = 'bearish'
                    confidence = 0.7
                    details.append(f"PCR медвежий: {pcr_ratio:.2f}")
                elif pcr_ratio < self.config['pcr_bullish_threshold']:
                    direction = 'bullish'
                    confidence = 0.7
                    details.append(f"PCR бычий: {pcr_ratio:.2f}")

        return {
            'confidence': confidence,
            'direction': direction,
            'indicators_used': indicators_used,
            'details': details
        }

    def _analyze_options(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ опционных данных"""
        indicators_used = []
        confidence_scores = []
        direction_votes = []
        details = []

        # Анализ PCR
        if data.get('pcr'):
            pcr_data = data['pcr']
            if 'ratio' in pcr_data:
                pcr_ratio = pcr_data['ratio']
                indicators_used.append('pcr')
                
                if pcr_ratio > self.config['pcr_bearish_threshold']:
                    direction_votes.append('bearish')
                    confidence_scores.append(0.8)
                    details.append(f"Сильный медвежий PCR: {pcr_ratio:.2f}")
                elif pcr_ratio > 1.0:
                    direction_votes.append('bearish')
                    confidence_scores.append(0.6)
                    details.append(f"Медвежий PCR: {pcr_ratio:.2f}")
                elif pcr_ratio < self.config['pcr_bullish_threshold']:
                    direction_votes.append('bullish')
                    confidence_scores.append(0.8)
                    details.append(f"Сильный бычий PCR: {pcr_ratio:.2f}")
                elif pcr_ratio < 1.0:
                    direction_votes.append('bullish')
                    confidence_scores.append(0.6)
                    details.append(f"Бычий PCR: {pcr_ratio:.2f}")

        # Анализ Max Pain
        if data.get('max_pain'):
            max_pain_data = data['max_pain']
            if 'max_pain_price' in max_pain_data and 'current_price' in max_pain_data:
                max_pain = max_pain_data['max_pain_price']
                current = max_pain_data['current_price']
                price_diff_pct = (current - max_pain) / max_pain
                indicators_used.append('max_pain')
                
                threshold = self.config['max_pain_threshold']
                if price_diff_pct > threshold:
                    direction_votes.append('bullish')
                    confidence_scores.append(0.7)
                    details.append(f"Цена выше Max Pain на {price_diff_pct*100:.1f}%")
                elif price_diff_pct < -threshold:
                    direction_votes.append('bearish')
                    confidence_scores.append(0.7)
                    details.append(f"Цена ниже Max Pain на {abs(price_diff_pct)*100:.1f}%")

        # Анализ Vanna
        if data.get('vanna'):
            vanna_data = data['vanna']
            if 'total_vanna' in vanna_data:
                total_vanna = vanna_data['total_vanna']
                indicators_used.append('vanna')
                
                if total_vanna > self.config['vanna_threshold']:
                    direction_votes.append('bullish')
                    confidence_scores.append(0.6)
                    details.append(f"Положительная Vanna: {total_vanna:,.0f}")
                else:
                    direction_votes.append('bearish')
                    confidence_scores.append(0.6)
                    details.append(f"Отрицательная Vanna: {total_vanna:,.0f}")

        # Определяем общее направление и уверенность
        if not direction_votes:
            return {
                'confidence': 0.5,
                'direction': 'neutral',
                'indicators_used': indicators_used,
                'details': details
            }
        
        # Голосование по направлению
        bullish_count = direction_votes.count('bullish')
        bearish_count = direction_votes.count('bearish')
        
        if bullish_count > bearish_count:
            direction = 'bullish'
        elif bearish_count > bullish_count:
            direction = 'bearish'
        else:
            direction = 'neutral'
        
        # Средняя уверенность
        confidence = np.mean(confidence_scores) if confidence_scores else 0.5

        return {
            'confidence': confidence,
            'direction': direction,
            'indicators_used': indicators_used,
            'details': details
        }

    def _analyze_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ тайминговых данных"""
        return {
            'confidence': 0.5,
            'direction': 'neutral',
            'indicators_used': [],
            'details': ['Timing indicators not yet implemented']
        }

    def _determine_signal_type(self, futures: Dict, options: Dict, timing: Dict, confidence: float) -> str:
        """Определить тип сигнала"""
        if confidence < self.config['min_confidence']:
            return 'NO_SIGNAL'
        
        # Определяем общее направление
        directions = {
            'bullish': 0,
            'bearish': 0,
            'neutral': 0
        }
        
        for analysis in [futures, options, timing]:
            directions[analysis['direction']] += 1
        
        if directions['bullish'] > directions['bearish']:
            signal_direction = 'BULLISH'
        elif directions['bearish'] > directions['bullish']:
            signal_direction = 'BEARISH'
        else:
            signal_direction = 'NEUTRAL'

        if confidence >= self.config['strong_threshold']:
            return f"STRONG_{signal_direction}"
        else:
            return f"WEAK_{signal_direction}"

    def _build_reasoning(self, signal_type: str, confidence: float, futures: Dict, options: Dict) -> str:
        """Построить объяснение сигнала"""
        if signal_type == 'NO_SIGNAL':
            return f"Confidence too low: {confidence} < {self.config['min_confidence']}"
        
        reasoning_parts = []
        
        if futures['details']:
            reasoning_parts.append(f"Futures: {', '.join(futures['details'])}")
        if options['details']:
            reasoning_parts.append(f"Options: {', '.join(options['details'])}")
            
        if reasoning_parts:
            return f"{signal_type} with {confidence} confidence. " + ". ".join(reasoning_parts)
        else:
            return f"{signal_type} signal with {confidence} confidence"
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получить метрики производительности для оптимизации"""
        if not self.signal_history:
            return {}
        
        signals = [s for s in self.signal_history if s['signal_type'] != 'NO_SIGNAL']
        total_signals = len(signals)
        
        if total_signals == 0:
            return {}
        
        bullish_signals = len([s for s in signals if 'BULLISH' in s['signal_type']])
        bearish_signals = len([s for s in signals if 'BEARISH' in s['signal_type']])
        avg_confidence = np.mean([s['confidence'] for s in signals])
        
        return {
            'total_signals': total_signals,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'avg_confidence': avg_confidence,
            'signal_frequency': total_signals / len(self.signal_history) if self.signal_history else 0
        }

# Тестовый запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from data_integrator import DataIntegrator
    
    integrator = DataIntegrator()
    analyzer = SignalAnalyzer()
    
    print("🧪 SignalAnalyzer v3 - ОПТИМИЗИРОВАН ДЛЯ БЭКТЕСТА")
    print("=" * 50)
    
    data = integrator.get_all_data('ETH')
    signal = analyzer.analyze(data)
    
    print(f"📊 Данные: {data['data_quality']['available_sources']} источников")
    print(f"📈 Сигнал: {signal['signal_type']}")
    print(f"🎯 Уверенность: {signal['confidence']}")
    print(f"🧠 Обоснование: {signal['reasoning']}")
    
    metrics = analyzer.get_performance_metrics()
    print(f"📈 Метрики: {metrics}")
