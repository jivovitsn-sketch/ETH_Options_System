#!/usr/bin/env python3
"""
Signal Analyzer v2 - реальная логика анализа на основе данных
"""

import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime

class SignalAnalyzer:
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger('SignalAnalyzer')
        self.config = config or self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Получить конфигурацию по умолчанию"""
        return {
            # Веса групп
            'futures_weight': 0.35,
            'options_weight': 0.40,
            'timing_weight': 0.25,
            
            # Пороги
            'min_confidence': 0.65,  # Снизим для тестирования
            'strong_threshold': 0.75,
            'min_data_sources': 2
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

        return {
            'signal_type': signal_type,
            'confidence': round(total_confidence, 3),
            'timestamp': datetime.now().isoformat(),
            'asset': data.get('asset', 'unknown'),
            'components': {
                'futures': futures_analysis,
                'options': options_analysis,
                'timing': timing_analysis
            },
            'reasoning': self._build_reasoning(signal_type, total_confidence, futures_analysis, options_analysis)
        }

    def _analyze_futures(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ фьючерсных данных"""
        indicators_used = []
        confidence = 0.5  # нейтральная уверенность по умолчанию
        direction = 'neutral'
        details = []

        # TODO: Добавить реальную логику, когда появятся фьючерсные данные
        # Пока используем опционные данные как прокси
        
        if data.get('pcr'):
            pcr_data = data['pcr']
            if 'ratio' in pcr_data:
                pcr_ratio = pcr_data['ratio']
                indicators_used.append('pcr')
                # PCR > 1 - медвежий, < 1 - бычий
                if pcr_ratio > 1.2:
                    direction = 'bearish'
                    confidence = 0.7
                    details.append(f"PCR высокий: {pcr_ratio}")
                elif pcr_ratio < 0.8:
                    direction = 'bullish' 
                    confidence = 0.7
                    details.append(f"PCR низкий: {pcr_ratio}")
                else:
                    details.append(f"PCR нейтральный: {pcr_ratio}")

        return {
            'confidence': confidence,
            'direction': direction,
            'indicators_used': indicators_used,
            'details': details
        }

    def _analyze_options(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ опционных данных"""
        indicators_used = []
        confidence = 0.5
        direction = 'neutral'
        details = []

        # Анализ PCR
        if data.get('pcr'):
            pcr_data = data['pcr']
            if 'ratio' in pcr_data:
                pcr_ratio = pcr_data['ratio']
                indicators_used.append('pcr')
                
                # Логика PCR
                if pcr_ratio > 1.3:
                    direction = 'bearish'
                    confidence = max(confidence, 0.8)
                    details.append(f"Сильный медвежий PCR: {pcr_ratio}")
                elif pcr_ratio > 1.1:
                    direction = 'bearish'
                    confidence = max(confidence, 0.6)
                    details.append(f"Медвежий PCR: {pcr_ratio}")
                elif pcr_ratio < 0.7:
                    direction = 'bullish'
                    confidence = max(confidence, 0.8)
                    details.append(f"Сильный бычий PCR: {pcr_ratio}")
                elif pcr_ratio < 0.9:
                    direction = 'bullish'
                    confidence = max(confidence, 0.6)
                    details.append(f"Бычий PCR: {pcr_ratio}")

        # Анализ Max Pain
        if data.get('max_pain'):
            max_pain_data = data['max_pain']
            if 'max_pain_price' in max_pain_data and 'current_price' in max_pain_data:
                max_pain = max_pain_data['max_pain_price']
                current = max_pain_data['current_price']
                indicators_used.append('max_pain')
                
                # Текущая цена выше max pain - бычье давление
                if current > max_pain * 1.02:  # +2%
                    direction = 'bullish'
                    confidence = max(confidence, 0.7)
                    details.append(f"Цена выше Max Pain: {current} > {max_pain}")
                elif current < max_pain * 0.98:  # -2%
                    direction = 'bearish'
                    confidence = max(confidence, 0.7)
                    details.append(f"Цена ниже Max Pain: {current} < {max_pain}")

        # Анализ Vanna
        if data.get('vanna'):
            vanna_data = data['vanna']
            if 'total_vanna' in vanna_data:
                total_vanna = vanna_data['total_vanna']
                indicators_used.append('vanna')
                
                # Положительная vanna - бычья, отрицательная - медвежья
                if total_vanna > 0:
                    direction = 'bullish'
                    confidence = max(confidence, 0.6)
                    details.append(f"Положительная Vanna: {total_vanna}")
                else:
                    direction = 'bearish'
                    confidence = max(confidence, 0.6)
                    details.append(f"Отрицательная Vanna: {total_vanna}")

        return {
            'confidence': confidence,
            'direction': direction,
            'indicators_used': indicators_used,
            'details': details
        }

    def _analyze_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ тайминговых данных"""
        # TODO: Реализовать когда появятся timing индикаторы
        return {
            'confidence': 0.5,
            'direction': 'neutral',
            'indicators_used': [],
            'details': ['Timing analysis pending implementation']
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

# Тестовый запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Тестируем с реальными данными
    from data_integrator import DataIntegrator
    
    integrator = DataIntegrator()
    analyzer = SignalAnalyzer()
    
    print("🧪 SignalAnalyzer v2 - ТЕСТ С РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 50)
    
    data = integrator.get_all_data('ETH')
    signal = analyzer.analyze(data)
    
    print(f"📊 Данные: {data['data_quality']['available_sources']} источников")
    print(f"📈 Сигнал: {signal['signal_type']}")
    print(f"🎯 Уверенность: {signal['confidence']}")
    print(f"🧠 Обоснование: {signal['reasoning']}")
    print(f"🔧 Компоненты: {signal['components']}")
