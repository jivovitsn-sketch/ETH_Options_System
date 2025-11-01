#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIGNAL ANALYZER - Stage 1.4.3 (ROADMAP Implementation)
Анализирует данные и генерирует сигналы с настраиваемыми параметрами
"""

import logging
from typing import Dict, Any, List, Optional
import hashlib
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalAnalyzer:
    """Анализирует данные и генерирует сигнал с настраиваемыми параметрами"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = self._validate_config(config)
        self.signal_history = []
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация конфигурации"""
        total_weights = (
            config.get('futures_weight', 0) +
            config.get('options_weight', 0) +
            config.get('timing_weight', 0)
        )
        
        if abs(total_weights - 1.0) > 0.01:
            logger.warning(f"Group weights sum to {total_weights}, normalizing...")
            factor = 1.0 / total_weights
            config['futures_weight'] *= factor
            config['options_weight'] *= factor
            config['timing_weight'] *= factor
        
        logger.info("✅ Config validation passed")
        return config
    
    def analyze(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Анализ данных и генерация сигнала"""
        
        if not self._check_data_quality(data):
            logger.warning(f"Data quality too low for {data.get('asset')}")
            return None
        
        futures_signal = self._analyze_futures(data)
        options_signal = self._analyze_options(data)
        timing_signal = self._analyze_timing(data)
        
        if not self._pass_filters(futures_signal, options_signal, timing_signal):
            logger.info(f"Signal filters not passed for {data.get('asset')}")
            return None
        
        total_confidence = (
            futures_signal['confidence'] * self.config['futures_weight'] +
            options_signal['confidence'] * self.config['options_weight'] +
            timing_signal['confidence'] * self.config['timing_weight']
        )
        
        signal_type = self._determine_signal_type(
            futures_signal,
            options_signal,
            timing_signal
        )
        
        reasoning = self._build_reasoning(
            futures_signal,
            options_signal,
            timing_signal
        )
        
        result = {
            'signal_type': signal_type,
            'confidence': total_confidence,
            'strength': self._classify_strength(total_confidence),
            'components': {
                'futures': futures_signal,
                'options': options_signal,
                'timing': timing_signal
            },
            'reasoning': reasoning,
            'config_version': self._get_config_hash(),
            'data_quality': data.get('quality')
        }
        
        self.signal_history.append(result)
        return result
    
    def _check_data_quality(self, data: Dict[str, Any]) -> bool:
        """Проверка минимального качества данных"""
        quality = data.get('quality', {})
        
        min_sources = self.config.get('min_data_sources', 2)
        if quality.get('available_sources', 0) < min_sources:
            return False
        
        required_quality = self.config.get('min_data_quality', 'ACCEPTABLE')
        quality_levels = ['POOR', 'ACCEPTABLE', 'GOOD', 'EXCELLENT']
        
        actual = quality.get('status', 'POOR')
        if quality_levels.index(actual) < quality_levels.index(required_quality):
            return False
        
        return True
    
    def _analyze_futures(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ фьючерсных индикаторов"""
        confidence = 0.5
        signal = 'NEUTRAL'
        reasons = []
        
        # Funding Rate
        futures = data.get('futures')
        if futures and 'funding_rate' in futures:
            fr = futures['funding_rate']
            
            if fr and fr > 0.0001:
                confidence -= 0.15
                signal = 'BEARISH'
                reasons.append(f"High funding {fr*100:.4f}%")
            elif fr and fr < -0.0001:
                confidence += 0.15
                signal = 'BULLISH'
                reasons.append(f"Negative funding {fr*100:.4f}%")
        
        # Liquidations
        liq = data.get('liquidations')
        if liq and 'ratio' in liq:
            ratio = liq['ratio']
            
            if ratio and ratio > 2.0:
                confidence -= 0.20
                if signal == 'NEUTRAL':
                    signal = 'BEARISH'
                reasons.append(f"Liq ratio {ratio:.2f} (longs squeezed)")
            elif ratio and ratio < 0.5:
                confidence += 0.20
                if signal == 'NEUTRAL':
                    signal = 'BULLISH'
                reasons.append(f"Liq ratio {ratio:.2f} (shorts squeezed)")
        
        return {
            'signal': signal,
            'confidence': max(min(confidence, 1.0), 0.0),
            'reasoning': reasons,
            'data_used': ['futures', 'liquidations']
        }
    
    def _analyze_options(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ опционных индикаторов - С ПРОВЕРКАМИ None"""
        confidence = 0.5
        signal = 'NEUTRAL'
        reasons = []
        
        # Max Pain
        max_pain = data.get('max_pain')
        if max_pain and 'distance_pct' in max_pain:
            distance_pct = max_pain['distance_pct']
            
            if distance_pct is not None and abs(distance_pct) > 3:
                confidence += 0.10
                if distance_pct > 0:
                    reasons.append(f"Above Max Pain {distance_pct:.1f}%")
                else:
                    reasons.append(f"Below Max Pain {abs(distance_pct):.1f}%")
        
        # GEX
        gex = data.get('gex')
        if gex and 'total_gex' in gex:
            total_gex = gex['total_gex']
            
            if total_gex is not None and total_gex < 0:
                confidence += 0.10
                signal = 'BULLISH' if signal == 'NEUTRAL' else signal
                reasons.append("Negative GEX")
        
        # PCR
        pcr = data.get('pcr')
        if pcr and 'pcr_oi' in pcr:
            pcr_oi = pcr['pcr_oi']
            
            if pcr_oi is not None:
                if pcr_oi > 1.5:
                    confidence += 0.08
                    reasons.append(f"High PCR {pcr_oi:.2f}")
                elif pcr_oi < 0.7:
                    confidence -= 0.08
                    reasons.append(f"Low PCR {pcr_oi:.2f}")
        
        # Vanna
        vanna = data.get('vanna')
        if vanna and 'total_vanna' in vanna:
            total_vanna = vanna['total_vanna']
            
            if total_vanna is not None and abs(total_vanna) > 500:
                if total_vanna > 0:
                    confidence += 0.12
                    signal = 'BULLISH' if signal == 'NEUTRAL' else signal
                else:
                    confidence -= 0.12
                    signal = 'BEARISH' if signal == 'NEUTRAL' else signal
                reasons.append(f"Vanna {total_vanna:.0f}")
        
        return {
            'signal': signal,
            'confidence': max(min(confidence, 1.0), 0.0),
            'reasoning': reasons,
            'data_used': ['max_pain', 'gex', 'pcr', 'vanna']
        }
    
    def _analyze_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ тайминговых индикаторов"""
        confidence = 0.5
        signal = 'NEUTRAL'
        reasons = []
        
        # PCR RSI
        pcr = data.get('pcr')
        if pcr and 'pcr_rsi' in pcr:
            rsi_val = pcr['pcr_rsi']
            
            if rsi_val is not None:
                if rsi_val > 70:
                    confidence += 0.10
                    signal = 'BULLISH'
                    reasons.append(f"PCR RSI {rsi_val:.0f} (fear)")
                elif rsi_val < 30:
                    confidence -= 0.10
                    signal = 'BEARISH'
                    reasons.append(f"PCR RSI {rsi_val:.0f} (greed)")
        
        return {
            'signal': signal,
            'confidence': max(min(confidence, 1.0), 0.0),
            'reasoning': reasons,
            'data_used': ['pcr_rsi']
        }
    
    def _pass_filters(self, futures_sig, options_sig, timing_sig) -> bool:
        """Проверка фильтров"""
        
        if self.config.get('require_futures_confirm', False):
            if futures_sig['confidence'] < 0.5:
                return False
        
        if self.config.get('require_options_confirm', True):
            if options_sig['confidence'] < 0.5:
                return False
        
        return True
    
    def _determine_signal_type(self, futures_sig, options_sig, timing_sig) -> str:
        """Определение направления сигнала"""
        signals = [
            futures_sig['signal'],
            options_sig['signal'],
            timing_sig['signal']
        ]
        
        bullish_count = signals.count('BULLISH')
        bearish_count = signals.count('BEARISH')
        
        if bullish_count >= 2:
            return 'BULLISH'
        elif bearish_count >= 2:
            return 'BEARISH'
        else:
            return 'NO_SIGNAL'
    
    def _build_reasoning(self, futures_sig, options_sig, timing_sig) -> List[str]:
        """Объединение обоснований"""
        all_reasons = []
        all_reasons.extend(futures_sig['reasoning'])
        all_reasons.extend(options_sig['reasoning'])
        all_reasons.extend(timing_sig['reasoning'])
        return all_reasons[:8]
    
    def _classify_strength(self, confidence: float) -> str:
        """Классификация силы"""
        strong = self.config.get('strong_threshold', 0.75)
        min_conf = self.config.get('min_confidence', 0.60)
        
        if confidence >= strong:
            return 'STRONG'
        elif confidence >= min_conf:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    def _get_config_hash(self) -> str:
        """Хэш конфигурации"""
        config_str = json.dumps(self.config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Метрики производительности"""
        if not self.signal_history:
            return {'total_signals': 0}
        
        total = len(self.signal_history)
        bullish = sum(1 for s in self.signal_history if s['signal_type'] == 'BULLISH')
        bearish = sum(1 for s in self.signal_history if s['signal_type'] == 'BEARISH')
        
        return {
            'total_signals': total,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'avg_confidence': sum(s['confidence'] for s in self.signal_history) / total
        }


if __name__ == '__main__':
    from data_integrator import DataIntegrator
    from backtest_params import get_default_config
    
    print("=" * 60)
    print("🧪 SIGNAL ANALYZER - FIXED")
    print("=" * 60)
    
    config = get_default_config()
    integrator = DataIntegrator()
    analyzer = SignalAnalyzer(config)
    
    assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
    
    for asset in assets:
        print(f"\n📊 {asset}:")
        data = integrator.get_all_data(asset)
        signal = analyzer.analyze(data)
        
        if signal:
            print(f"  Signal: {signal['signal_type']}")
            print(f"  Confidence: {signal['confidence']*100:.1f}% [{signal['strength']}]")
            if signal['reasoning']:
                print(f"  Reasons: {', '.join(signal['reasoning'][:2])}")
        else:
            print(f"  ❌ No signal")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЁН")
    print("=" * 60)
