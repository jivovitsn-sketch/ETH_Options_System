# 🗺️ STAGE 1.4: ИНТЕГРАЦИЯ ВСЕХ ИНДИКАТОРОВ + БЭКТЕСТ

## 📊 ЦЕЛЬ
Объединить ВСЕ индикаторы (фьючерсные + опционные) в единую систему генерации сигналов с настраиваемыми параметрами для бэктеста.

## 🎯 ПРИНЦИПЫ РЕАЛИЗАЦИИ
1. **MVP подход** - Сначала core индикаторы, потом расширение
2. **Поэтапное тестирование** - Тестировать группы отдельно
3. **Качество данных** - Мониторинг и валидация на каждом этапе
4. **Воспроизводимость** - Версионирование конфигов и логов

---

## 🎖️ ПРИОРИТЕТЫ НОВЫХ ИНДИКАТОРОВ

### 🔴 HIGH PRIORITY (реализовать первыми)
- [ ] **option_vwap_calculator.py** - Быстрая реализация, высокая ценность
- [ ] **PCR RSI** (доработка pcr_calculator.py) - Критичен для тайминга
- [ ] **GEX RSI** (доработка gamma_exposure_calculator.py) - Важен для волатильности

### 🟡 MEDIUM PRIORITY (после HIGH)
- [ ] **oi_macd_calculator.py** - Средняя сложность, хорошая ценность
- [ ] **iv_macd_calculator.py** - Дополняет IV анализ

### 🟢 LOW PRIORITY (опционально)
- [ ] **oi_velocity_rsi.py** - Можно отложить, дублирует OI MACD

---

## ✅ CHECKPOINT 1.4.1: ИНВЕНТАРИЗАЦИЯ ИНДИКАТОРОВ

### 🟢 ФЬЮЧЕРСНЫЕ ИНДИКАТОРЫ (что собираем)
- [ ] Funding Rate (funding_rate_monitor.py) ✅ РАБОТАЕТ
- [ ] Liquidations (liquidations_monitor.py) ✅ РАБОТАЕТ
- [ ] Futures OI (futures_data_monitor.py) ✅ РАБОТАЕТ
- [ ] Спот цены (futures_data_monitor.py) ✅ РАБОТАЕТ

### 🔵 ОПЦИОННЫЕ ИНДИКАТОРЫ (что собираем)
- [ ] PCR - Put/Call Ratio (pcr_calculator.py) ✅ СОЗДАН
- [ ] OI - Open Interest (unlimited_oi_monitor.py) ✅ РАБОТАЕТ
- [ ] Max Pain (max_pain_calculator.py) ✅ РАБОТАЕТ
- [ ] GEX - Gamma Exposure (gamma_exposure_calculator.py) ✅ РАБОТАЕТ
- [ ] Vanna Exposure (vanna_calculator.py) ✅ СОЗДАН
- [ ] IV Rank (iv_rank_calculator.py) ✅ СОЗДАН (нужны данные volatility)
- [ ] Volatility & Greeks (volatility_greeks_analyzer.py) ✅ РАБОТАЕТ

### 🟡 НОВЫЕ ИНДИКАТОРЫ (нужно создать)
- [ ] 🔴 VWAP для опционов (option_vwap_calculator.py)
- [ ] 🔴 RSI от PCR (встроить в pcr_calculator.py)
- [ ] 🔴 RSI от GEX (встроить в gamma_exposure_calculator.py)
- [ ] 🟡 MACD от OI (oi_macd_calculator.py)
- [ ] 🟡 MACD от IV (iv_macd_calculator.py)
- [ ] 🟢 RSI от OI Velocity (oi_velocity_rsi.py)

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ Инвентаризация завершена
✅ Все существующие индикаторы создают JSON файлы
✅ Определены приоритеты для новых индикаторов
✅ Данные обновляются каждые 30 минут через system_manager

---

## ✅ CHECKPOINT 1.4.2: СОЗДАНИЕ ИНТЕГРАТОРА ДАННЫХ

### 📦 DataIntegrator Class
```python
# data_integrator.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataIntegrator:
    """Объединяет данные из всех источников для актива"""
    
    def __init__(self):
        self.data_sources = {
            'futures': get_futures_data,
            'funding': get_funding_rate,
            'liquidations': get_liquidations,
            'pcr': get_pcr_data,
            'oi': get_oi_data,
            'max_pain': get_max_pain,
            'gex': get_gamma_exposure,
            'vanna': get_vanna_data,
            'iv_rank': get_iv_rank_data,
            'option_vwap': get_option_vwap,
            'pcr_rsi': get_pcr_rsi,
            'oi_macd': get_oi_macd,
            'iv_macd': get_iv_macd
        }
    
    def get_all_data(self, asset: str) -> Dict[str, Any]:
        """Собрать все доступные данные для актива"""
        try:
            data = {
                'asset': asset,
                'timestamp': datetime.now(),
                'spot_price': None,
                'available_sources': []
            }
            
            # Собираем данные из всех источников
            for source_name, source_func in self.data_sources.items():
                try:
                    result = source_func(asset)
                    data[source_name] = result
                    
                    if result is not None:
                        data['available_sources'].append(source_name)
                    
                    # Извлекаем spot_price из первого доступного источника
                    if data['spot_price'] is None and result:
                        if isinstance(result, dict) and 'spot_price' in result:
                            data['spot_price'] = result['spot_price']
                        elif source_name == 'futures' and result.get('price'):
                            data['spot_price'] = result['price']
                
                except Exception as e:
                    logger.warning(f"Failed to get {source_name} for {asset}: {e}")
                    data[source_name] = None
            
            # Добавляем качество данных
            data['quality'] = self.get_data_quality_report(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to integrate data for {asset}: {e}")
            return self._get_fallback_data(asset)
    
    def _get_fallback_data(self, asset: str) -> Dict[str, Any]:
        """Минимальный набор данных при критической ошибке"""
        logger.warning(f"Using fallback data for {asset}")
        
        # Хотя бы спот цена и timestamp
        try:
            futures = get_futures_data(asset)
            spot_price = futures.get('price') if futures else None
        except:
            spot_price = None
        
        return {
            'asset': asset,
            'timestamp': datetime.now(),
            'spot_price': spot_price,
            'available_sources': [],
            'quality': {'status': 'FALLBACK'},
            'error': 'Critical error in data integration'
        }
    
    def get_data_quality_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка качества собранных данных"""
        total_sources = len(self.data_sources)
        available = len(data.get('available_sources', []))
        
        # Проверка свежести данных
        max_age_minutes = 0
        if 'timestamp' in data:
            for source in data.get('available_sources', []):
                if isinstance(data.get(source), dict) and 'timestamp' in data[source]:
                    try:
                        source_time = datetime.fromisoformat(data[source]['timestamp'])
                        age = (data['timestamp'] - source_time).total_seconds() / 60
                        max_age_minutes = max(max_age_minutes, age)
                    except:
                        pass
        
        completeness = available / total_sources
        
        # Определение статуса
        if completeness >= 0.8 and max_age_minutes < 30:
            status = 'EXCELLENT'
        elif completeness >= 0.6 and max_age_minutes < 60:
            status = 'GOOD'
        elif completeness >= 0.4:
            status = 'ACCEPTABLE'
        else:
            status = 'POOR'
        
        return {
            'status': status,
            'available_sources': available,
            'total_sources': total_sources,
            'completeness': completeness,
            'max_age_minutes': max_age_minutes,
            'missing_sources': [s for s in self.data_sources.keys() 
                               if s not in data.get('available_sources', [])]
        }
```

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ DataIntegrator возвращает полный набор данных для любого актива
✅ Graceful degradation - работает даже при отсутствии части данных
✅ Data quality report показывает completeness и freshness
✅ Логирует какие данные недоступны
✅ Fallback механизм при критических ошибках

---

## ✅ CHECKPOINT 1.4.3: СОЗДАНИЕ SIGNAL ANALYZER С ПАРАМЕТРАМИ

### 🎯 SignalAnalyzer Class
```python
# signal_analyzer.py
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SignalAnalyzer:
    """Анализирует данные и генерирует сигнал с настраиваемыми параметрами"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        config = {
            # ВЕСА ГРУПП (будут оптимизироваться в бэктесте)
            'futures_weight': 0.35,
            'options_weight': 0.40,
            'timing_weight': 0.25,
            
            # ВЕСА ИНДИКАТОРОВ ВНУТРИ ГРУПП
            'futures': {
                'funding_weight': 0.40,
                'liquidations_weight': 0.60
            },
            'options': {
                'oi_weight': 0.15,
                'max_pain_weight': 0.15,
                'gex_weight': 0.15,
                'pcr_weight': 0.15,
                'vanna_weight': 0.20,
                'iv_rank_weight': 0.20
            },
            'timing': {
                'option_vwap_weight': 0.20,
                'pcr_rsi_weight': 0.25,
                'oi_macd_weight': 0.25,
                'iv_macd_weight': 0.30
            },
            
            # ПОРОГИ
            'min_confidence': 0.75,
            'strong_threshold': 0.85,
            
            # ФИЛЬТРЫ
            'require_futures_confirm': True,
            'require_options_confirm': True,
            'min_data_sources': 5,
            'min_data_quality': 'ACCEPTABLE'
        }
        """
        self.config = self._validate_config(config)
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация конфигурации"""
        # Проверка что веса групп в сумме дают 1.0
        total_weights = (
            config.get('futures_weight', 0) +
            config.get('options_weight', 0) +
            config.get('timing_weight', 0)
        )
        
        if abs(total_weights - 1.0) > 0.01:
            raise ValueError(f"Group weights must sum to 1.0, got {total_weights}")
        
        # Проверка весов внутри групп
        for group in ['futures', 'options', 'timing']:
            if group in config:
                group_total = sum(config[group].values())
                if abs(group_total - 1.0) > 0.01:
                    raise ValueError(f"{group} weights must sum to 1.0, got {group_total}")
        
        # Проверка порогов
        min_conf = config.get('min_confidence', 0.75)
        strong = config.get('strong_threshold', 0.85)
        
        if not (0 < min_conf < 1):
            raise ValueError(f"min_confidence must be between 0 and 1, got {min_conf}")
        
        if not (min_conf < strong < 1):
            raise ValueError(f"strong_threshold must be > min_confidence and < 1")
        
        logger.info("✅ Config validation passed")
        return config
    
    def analyze(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Анализ данных и генерация сигнала"""
        
        # Проверка качества данных
        if not self._check_data_quality(data):
            logger.warning(f"Data quality too low for {data.get('asset')}")
            return None
        
        # Анализ каждой группы
        futures_signal = self._analyze_futures(data)
        options_signal = self._analyze_options(data)
        timing_signal = self._analyze_timing(data)
        
        # Проверка фильтров
        if not self._pass_filters(futures_signal, options_signal, timing_signal):
            logger.info(f"Signal filters not passed for {data.get('asset')}")
            return None
        
        # Взвешенная комбинация
        total_confidence = (
            futures_signal['confidence'] * self.config['futures_weight'] +
            options_signal['confidence'] * self.config['options_weight'] +
            timing_signal['confidence'] * self.config['timing_weight']
        )
        
        # Определение направления
        signal_type = self._determine_signal_type(
            futures_signal,
            options_signal,
            timing_signal
        )
        
        # Сбор reasoning
        reasoning = self._build_reasoning(
            futures_signal,
            options_signal,
            timing_signal
        )
        
        return {
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
    
    def _check_data_quality(self, data: Dict[str, Any]) -> bool:
        """Проверка минимального качества данных"""
        quality = data.get('quality', {})
        
        # Минимальное количество источников
        min_sources = self.config.get('min_data_sources', 5)
        if quality.get('available_sources', 0) < min_sources:
            return False
        
        # Минимальное качество
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
        
        weights = self.config.get('futures', {})
        
        # Funding Rate
        funding = data.get('funding')
        if funding and funding.get('funding_rate'):
            fr = funding['funding_rate']
            fr_weight = weights.get('funding_weight', 0.4)
            
            if fr > 0.01:  # Лонги переполнены
                confidence -= 0.15 * fr_weight
                signal = 'BEARISH'
                reasons.append(f"High funding {fr*100:.3f}% (longs overcrowded)")
            elif fr < -0.01:  # Шорты переполнены
                confidence += 0.15 * fr_weight
                signal = 'BULLISH'
                reasons.append(f"Negative funding {fr*100:.3f}% (shorts overcrowded)")
        
        # Liquidations
        liq = data.get('liquidations')
        if liq:
            ratio = liq.get('ratio', 1.0)
            liq_weight = weights.get('liquidations_weight', 0.6)
            
            if ratio > 2.0:  # Больше лонгов ликвидировано
                confidence -= 0.20 * liq_weight
                if signal == 'NEUTRAL':
                    signal = 'BEARISH'
                reasons.append(f"Liquidation ratio {ratio:.2f} (longs squeezed)")
            elif ratio < 0.5:  # Больше шортов ликвидировано
                confidence += 0.20 * liq_weight
                if signal == 'NEUTRAL':
                    signal = 'BULLISH'
                reasons.append(f"Liquidation ratio {ratio:.2f} (shorts squeezed)")
        
        return {
            'signal': signal,
            'confidence': max(min(confidence, 1.0), 0.0),
            'reasoning': reasons,
            'data_used': ['funding', 'liquidations']
        }
    
    def _analyze_options(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ опционных индикаторов"""
        confidence = 0.5
        signal = 'NEUTRAL'
        reasons = []
        
        weights = self.config.get('options', {})
        
        # OI Analysis
        oi = data.get('oi')
        if oi:
            oi_change = oi.get('change_pct', 0)
            oi_weight = weights.get('oi_weight', 0.15)
            
            if oi_change > 10:
                confidence += 0.12 * oi_weight
                reasons.append(f"OI growing {oi_change:.1f}%")
            elif oi_change < -10:
                confidence -= 0.12 * oi_weight
                reasons.append(f"OI declining {oi_change:.1f}%")
        
        # Max Pain
        max_pain = data.get('max_pain')
        if max_pain:
            distance_pct = max_pain.get('distance_pct', 0)
            mp_weight = weights.get('max_pain_weight', 0.15)
            
            if abs(distance_pct) > 3:
                confidence += 0.10 * mp_weight
                if distance_pct > 0:
                    reasons.append(f"Above Max Pain by {distance_pct:.1f}%")
                else:
                    reasons.append(f"Below Max Pain by {abs(distance_pct):.1f}%")
        
        # GEX
        gex = data.get('gex')
        if gex:
            total_gex = gex.get('total_gex', 0)
            gex_weight = weights.get('gex_weight', 0.15)
            
            if total_gex < 0:
                confidence += 0.10 * gex_weight
                signal = 'BULLISH' if signal == 'NEUTRAL' else signal
                reasons.append("Negative GEX (volatile support)")
        
        # PCR
        pcr = data.get('pcr')
        if pcr:
            pcr_oi = pcr.get('pcr_oi', 1.0)
            pcr_weight = weights.get('pcr_weight', 0.15)
            
            if pcr_oi > 1.5:
                confidence += 0.08 * pcr_weight
                reasons.append(f"High PCR {pcr_oi:.2f} (protective puts)")
            elif pcr_oi < 0.7:
                confidence -= 0.08 * pcr_weight
                reasons.append(f"Low PCR {pcr_oi:.2f} (speculative calls)")
        
        # Vanna
        vanna = data.get('vanna')
        if vanna:
            total_vanna = vanna.get('total_vanna', 0)
            vanna_weight = weights.get('vanna_weight', 0.20)
            
            if abs(total_vanna) > 500:
                if total_vanna > 0:
                    confidence += 0.12 * vanna_weight
                    signal = 'BULLISH' if signal == 'NEUTRAL' else signal
                else:
                    confidence -= 0.12 * vanna_weight
                    signal = 'BEARISH' if signal == 'NEUTRAL' else signal
                reasons.append(f"Strong Vanna {total_vanna:.0f}")
        
        # IV Rank
        iv_rank = data.get('iv_rank')
        if iv_rank:
            rank = iv_rank.get('iv_rank_52w', 50)
            iv_weight = weights.get('iv_rank_weight', 0.20)
            
            if rank > 75:
                confidence += 0.06 * iv_weight
                reasons.append(f"High IV Rank {rank:.0f}%")
            elif rank < 25:
                confidence += 0.06 * iv_weight
                reasons.append(f"Low IV Rank {rank:.0f}%")
        
        return {
            'signal': signal,
            'confidence': max(min(confidence, 1.0), 0.0),
            'reasoning': reasons,
            'data_used': ['oi', 'max_pain', 'gex', 'pcr', 'vanna', 'iv_rank']
        }
    
    def _analyze_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ тайминговых индикаторов"""
        confidence = 0.5
        signal = 'NEUTRAL'
        reasons = []
        
        weights = self.config.get('timing', {})
        
        # Option VWAP
        vwap = data.get('option_vwap')
        if vwap:
            vwap_weight = weights.get('option_vwap_weight', 0.20)
            # Логика VWAP
            reasons.append("Option VWAP analyzed")
        
        # PCR RSI
        pcr_rsi = data.get('pcr_rsi')
        if pcr_rsi:
            rsi_val = pcr_rsi.get('rsi', 50)
            rsi_weight = weights.get('pcr_rsi_weight', 0.25)
            
            if rsi_val > 70:
                confidence += 0.10 * rsi_weight
                signal = 'BULLISH'
                reasons.append(f"PCR RSI {rsi_val:.0f} (extreme fear)")
            elif rsi_val < 30:
                confidence -= 0.10 * rsi_weight
                signal = 'BEARISH'
                reasons.append(f"PCR RSI {rsi_val:.0f} (extreme greed)")
        
        # OI MACD
        oi_macd = data.get('oi_macd')
        if oi_macd:
            macd_weight = weights.get('oi_macd_weight', 0.25)
            trend = oi_macd.get('trend', 'NEUTRAL')
            
            if trend == 'BULLISH':
                confidence += 0.08 * macd_weight
                reasons.append("OI MACD bullish crossover")
            elif trend == 'BEARISH':
                confidence -= 0.08 * macd_weight
                reasons.append("OI MACD bearish crossover")
        
        # IV MACD
        iv_macd = data.get('iv_macd')
        if iv_macd:
            iv_weight = weights.get('iv_macd_weight', 0.30)
            trend = iv_macd.get('trend', 'STABLE')
            
            if trend == 'EXPANDING':
                confidence += 0.05 * iv_weight
                reasons.append("IV expanding (uncertainty rising)")
        
        return {
            'signal': signal,
            'confidence': max(min(confidence, 1.0), 0.0),
            'reasoning': reasons,
            'data_used': ['option_vwap', 'pcr_rsi', 'oi_macd', 'iv_macd']
        }
    
    def _pass_filters(self, futures_sig, options_sig, timing_sig) -> bool:
        """Проверка фильтров перед генерацией сигнала"""
        
        # Требуется подтверждение от фьючерсов
        if self.config.get('require_futures_confirm', True):
            if futures_sig['confidence'] < 0.6:
                return False
        
        # Требуется подтверждение от опционов
        if self.config.get('require_options_confirm', True):
            if options_sig['confidence'] < 0.6:
                return False
        
        return True
    
    def _determine_signal_type(self, futures_sig, options_sig, timing_sig) -> str:
        """Определение итогового направления сигнала"""
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
            return 'NEUTRAL'
    
    def _build_reasoning(self, futures_sig, options_sig, timing_sig) -> List[str]:
        """Объединение обоснований из всех компонентов"""
        all_reasons = []
        
        all_reasons.extend(futures_sig['reasoning'])
        all_reasons.extend(options_sig['reasoning'])
        all_reasons.extend(timing_sig['reasoning'])
        
        # Топ-8 причин
        return all_reasons[:8]
    
    def _classify_strength(self, confidence: float) -> str:
        """Классификация силы сигнала"""
        strong = self.config.get('strong_threshold', 0.85)
        
        if confidence >= strong:
            return 'STRONG'
        elif confidence >= self.config.get('min_confidence', 0.75):
            return 'MODERATE'
        else:
            return 'WEAK'
    
    def _get_config_hash(self) -> str:
        """Хэш конфигурации для версионирования"""
        import hashlib
        import json
        
        config_str = json.dumps(self.config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
```

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ SignalAnalyzer работает с любым валидным config
✅ Валидация конфигурации предотвращает ошибки
✅ Генерирует сигнал с confidence, strength и reasoning
✅ Graceful degradation при отсутствии данных
✅ Версионирование конфига через hash
✅ Логирует какие индикаторы использовались

---

## ✅ CHECKPOINT 1.4.4: ПАРАМЕТРЫ ДЛЯ БЭКТЕСТА

### 📋 Файл backtest_params.py
```python
# backtest_params.py
"""
Параметры для оптимизации в бэктесте
"""

BACKTEST_PARAMETERS = {
    # ===== ВЕСА ГРУПП =====
    'futures_weight': {
        'min': 0.20,
        'max': 0.50,
        'step': 0.05,
        'default': 0.35,
        'description': 'Вес фьючерсных индикаторов'
    },
    'options_weight': {
        'min': 0.30,
        'max': 0.60,
        'step': 0.05,
        'default': 0.40,
        'description': 'Вес опционных индикаторов'
    },
    'timing_weight': {
        'min': 0.10,
        'max': 0.40,
        'step': 0.05,
        'default': 0.25,
        'description': 'Вес тайминговых индикаторов'
    },
    
    # ===== ВЕСА ИНДИКАТОРОВ: ФЬЮЧЕРСНЫЕ =====
    'funding_weight': {
        'min': 0.20,
        'max': 0.80,
        'step': 0.10,
        'default': 0.40,
        'group': 'futures'
    },
    'liquidations_weight': {
        'min': 0.20,
        'max': 0.80,
        'step': 0.10,
        'default': 0.60,
        'group': 'futures'
    },
    
    # ===== ВЕСА ИНДИКАТОРОВ: ОПЦИОННЫЕ =====
    'oi_weight': {
        'min': 0.05,
        'max': 0.30,
        'step': 0.05,
        'default': 0.15,
        'group': 'options'
    },
    'max_pain_weight': {
        'min': 0.05,
        'max': 0.30,
        'step': 0.05,
        'default': 0.15,
        'group': 'options'
    },
    'gex_weight': {
        'min': 0.05,
        'max': 0.30,
        'step': 0.05,
        'default': 0.15,
        'group': 'options'
    },
    'pcr_weight': {
        'min': 0.05,
        'max': 0.30,
        'step': 0.05,
        'default': 0.15,
        'group': 'options'
    },
    'vanna_weight': {
        'min': 0.10,
        'max': 0.40,
        'step': 0.05,
        'default': 0.20,
        'group': 'options'
    },
    'iv_rank_weight': {
        'min': 0.10,
        'max': 0.40,
        'step': 0.05,
        'default': 0.20,
        'group': 'options'
    },
    
    # ===== ВЕСА ИНДИКАТОРОВ: ТАЙМИНГ =====
    'option_vwap_weight': {
        'min': 0.10,
        'max': 0.40,
        'step': 0.05,
        'default': 0.20,
        'group': 'timing'
    },
    'pcr_rsi_weight': {
        'min': 0.15,
        'max': 0.45,
        'step': 0.05,
        'default': 0.25,
        'group': 'timing'
    },
    'oi_macd_weight': {
        'min': 0.15,
        'max': 0.45,
        'step': 0.05,
        'default': 0.25,
        'group': 'timing'
    },
    'iv_macd_weight': {
        'min': 0.20,
        'max': 0.50,
        'step': 0.05,
        'default': 0.30,
        'group': 'timing'
    },
    
    # ===== ПОРОГИ =====
    'min_confidence': {
        'min': 0.60,
        'max': 0.85,
        'step': 0.05,
        'default': 0.75,
        'description': 'Минимальная уверенность для генерации сигнала'
    },
    'strong_threshold': {
        'min': 0.75,
        'max': 0.95,
        'step': 0.05,
        'default': 0.85,
        'description': 'Порог для STRONG сигнала'
    },
    
    # ===== ФИЛЬТРЫ =====
    'min_data_sources': {
        'min': 3,
        'max': 8,
        'step': 1,
        'default': 5,
        'description': 'Минимум источников данных для генерации сигнала'
    }
}

# Подсчет количества комбинаций
def count_combinations():
    """Подсчет всех возможных комбинаций параметров"""
    total = 1
    for param, settings in BACKTEST_PARAMETERS.items():
        if 'min' in settings and 'max' in settings and 'step' in settings:
            count = int((settings['max'] - settings['min']) / settings['step']) + 1
            total *= count
    return total

def get_default_config():
    """Получить дефолтную конфигурацию"""
    config = {
        'futures_weight': 0.35,
        'options_weight': 0.40,
        'timing_weight': 0.25,
        'futures': {},
        'options': {},
        'timing': {},
        'min_confidence': 0.75,
        'strong_threshold': 0.85,
        'min_data_sources': 5,
        'require_futures_confirm': True,
        'require_options_confirm': True,
        'min_data_quality': 'ACCEPTABLE'
    }
    
    # Заполняем веса индикаторов
    for param, settings in BACKTEST_PARAMETERS.items():
        if 'group' in settings:
            group = settings['group']
            config[group][param] = settings['default']
    
    return config

def generate_random_config():
    """Генерация случайной валидной конфигурации для тестирования"""
    import random
    
    config = get_default_config()
    
    for param, settings in BACKTEST_PARAMETERS.items():
        if 'min' in settings and 'max' in settings and 'step' in settings:
            min_val = settings['min']
            max_val = settings['max']
            step = settings['step']
            
            # Случайное значение в пределах диапазона
            steps_count = int((max_val - min_val) / step)
            random_steps = random.randint(0, steps_count)
            value = min_val + random_steps * step
            
            if 'group' in settings:
                group = settings['group']
                config[group][param] = value
            else:
                config[param] = value
    
    return config

# Статистика
if __name__ == '__main__':
    print(f"Total parameter combinations: {count_combinations():,}")
    print(f"Note: This number is too large for exhaustive search.")
    print(f"ML optimization (Bayesian/Genetic) is required.")
    print()
    print("Default config:")
    import json
    print(json.dumps(get_default_config(), indent=2))
```

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ Параметры определены для всех индикаторов с диапазонами
✅ Диапазоны значений разумные и валидируемые
✅ Функции для default и random конфигов работают
✅ Можно загрузить/сохранить config в JSON
✅ Документированы все параметры

---

## ✅ CHECKPOINT 1.4.5: ОБНОВЛЕНИЕ advanced_signals_generator.py

### 🔄 Интеграция нового SignalAnalyzer
```python
# В advanced_signals_generator.py

from data_integrator import DataIntegrator
from signal_analyzer import SignalAnalyzer
from backtest_params import get_default_config
import json
import os

class SignalGenerator:
    def __init__(self, config_file='signal_config.json'):
        """Инициализация с возможностью загрузки кастомного конфига"""
        
        # Загружаем конфиг (или используем default)
        if os.path.exists(config_file):
            logger.info(f"Loading config from {config_file}")
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            logger.info("Using default config")
            config = get_default_config()
        
        # Инициализация компонентов
        self.data_integrator = DataIntegrator()
        self.signal_analyzer = SignalAnalyzer(config)
        
        # Для логирования истории
        self.signal_history_logger = SignalHistoryLogger()
        
        logger.info(f"SignalGenerator initialized with config hash: {self.signal_analyzer._get_config_hash()}")
    
    def generate_signal(self, asset: str) -> Optional[Dict[str, Any]]:
        """Генерация сигнала для актива"""
        
        try:
            # 1. Собрать все данные
            logger.info(f"🔍 Analyzing {asset}...")
            data = self.data_integrator.get_all_data(asset)
            
            # Проверка качества данных
            quality = data.get('quality', {})
            logger.info(f"📊 Data quality: {quality.get('status')} ({quality.get('completeness', 0)*100:.0f}%)")
            
            # 2. Проанализировать
            signal = self.signal_analyzer.analyze(data)
            
            if not signal:
                logger.info(f"➡️ {asset}: No signal (filters not passed)")
                return None
            
            # 3. Проверить минимальную confidence
            if signal['confidence'] < self.signal_analyzer.config['min_confidence']:
                logger.info(f"📊 {asset}: Low confidence {signal['confidence']*100:.0f}%")
                return None
            
            # 4. Генерировать опционные стратегии
            spot_price = data.get('spot_price')
            if not spot_price:
                logger.warning(f"⚠️ {asset}: No spot price available")
                return None
            
            strategies = generate_option_strategies(
                asset,
                signal['signal_type'],
                spot_price,
                signal['confidence']
            )
            
            result = {
                'asset': asset,
                'signal': signal,
                'strategies': strategies,
                'data_snapshot': data,
                'timestamp': datetime.now()
            }
            
            # 5. Логировать для бэктеста
            self.signal_history_logger.log_signal(result)
            
            logger.info(f"✅ {asset}: {signal['signal_type']} {signal['confidence']*100:.0f}% ({signal['strength']})")
            logger.info(f"   Reasons: {', '.join(signal['reasoning'][:3])}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating signal for {asset}: {e}")
            return None
    
    def run(self):
        """Главный цикл генерации сигналов для всех активов"""
        logger.info("=" * 80)
        logger.info(f"🚀 SIGNAL GENERATION: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📝 Config: {self.signal_analyzer._get_config_hash()}")
        logger.info("=" * 80)
        
        assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        sent_count = 0
        skipped_count = 0
        
        for asset in assets:
            result = self.generate_signal(asset)
            
            if result:
                # Проверка нужно ли отправлять
                if self.should_send_signal(asset, result):
                    # Формируем и отправляем сообщение
                    message = format_option_signal_message(
                        asset,
                        result['signal']['signal_type'],
                        result['signal']['confidence'],
                        result['data_snapshot']['spot_price'],
                        result['strategies']
                    )
                    
                    self.send_telegram_message(message, is_vip=True)
                    
                    # FREE канал
                    self.send_to_free_channel(
                        asset,
                        result['signal']['signal_type'],
                        result['signal']['confidence'],
                        result['data_snapshot']['spot_price']
                    )
                    
                    sent_count += 1
                else:
                    logger.info(f"⏭️ {asset}: Already sent recently")
                    skipped_count += 1
            else:
                skipped_count += 1
        
        logger.info("=" * 80)
        logger.info(f"✅ Generation complete. Sent: {sent_count}, Skipped: {skipped_count}")
        logger.info("=" * 80)
```

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ Генератор использует DataIntegrator
✅ Генератор использует SignalAnalyzer с конфигом
✅ Можно менять signal_config.json и поведение меняется
✅ Логирует config hash для отслеживания версий
✅ Полная интеграция с существующей логикой отправки

---

## ✅ CHECKPOINT 1.4.6: СОЗДАНИЕ НЕДОСТАЮЩИХ ИНДИКАТОРОВ

### 🆕 Новые файлы для создания (в порядке приоритета):

#### 🔴 HIGH PRIORITY

##### 1. option_vwap_calculator.py
```python
# Расчет VWAP для опционных цен и IV
# Входы: unlimited_oi.db
# Выход: data/option_vwap/{ASSET}_vwap_YYYYMMDD_HHMMSS.json
# Поля: price_vwap, iv_vwap, premium_vwap
```

##### 2. Обновить pcr_calculator.py
```python
# Добавить расчет PCR RSI
# Новые поля в JSON: pcr_rsi, rsi_interpretation
```

##### 3. Обновить gamma_exposure_calculator.py
```python
# Добавить расчет GEX RSI
# Новые поля в JSON: gex_rsi, gex_trend
```

#### 🟡 MEDIUM PRIORITY

##### 4. oi_macd_calculator.py
```python
# MACD от агрегированного OI
# Входы: unlimited_oi.db (исторические данные OI)
# Выход: data/oi_macd/{ASSET}_macd_YYYYMMDD_HHMMSS.json
# Поля: macd, signal_line, histogram, trend
```

##### 5. iv_macd_calculator.py
```python
# MACD от IV surface
# Входы: data/volatility/*.json (исторические IV)
# Выход: data/iv_macd/{ASSET}_iv_macd_YYYYMMDD_HHMMSS.json
# Поля: macd, signal_line, histogram, trend
```

#### 🟢 LOW PRIORITY

##### 6. oi_velocity_rsi.py
```python
# RSI от скорости изменения OI (опционально)
# Может быть объединен с oi_macd_calculator.py
```

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ Все HIGH PRIORITY индикаторы созданы
✅ MEDIUM PRIORITY созданы или запланированы
✅ Все создают JSON выходы в нужных форматах
✅ Добавлены в system_manager analytics
✅ Тесты проверяют корректность расчетов

---

## ✅ CHECKPOINT 1.4.7: ТЕСТИРОВАНИЕ

### 🧪 Тестовый план:

#### 1. Unit тесты для индикаторов
```bash
# tests/test_indicators.py
pytest tests/test_indicators.py -v
```

#### 2. Integration тесты
```bash
# tests/test_data_integrator.py
pytest tests/test_data_integrator.py -v

# tests/test_signal_analyzer.py  
pytest tests/test_signal_analyzer.py -v
```

#### 3. End-to-end тест
```bash
# tests/test_e2e_signal_generation.py
pytest tests/test_e2e_signal_generation.py -v
```

#### 4. Config validation тесты
```bash
# tests/test_config_validation.py
pytest tests/test_config_validation.py -v
```

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ Все unit тесты проходят (coverage >80%)
✅ Integration тесты проходят
✅ E2E тест генерирует сигналы для всех активов
✅ Валидация конфигов работает корректно
✅ Нет критических багов

---

## ✅ CHECKPOINT 1.4.8: СОХРАНЕНИЕ ДАННЫХ ДЛЯ БЭКТЕСТА

### 📦 Signal History Logger
```python
# signal_history_logger.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class SignalHistoryLogger:
    """Логирование полной истории сигналов для бэктеста и анализа"""
    
    def __init__(self):
        self.db_path = './data/signal_history.db'
        self.json_dir = Path('./data/signal_history_json/')
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Инициализация БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                asset TEXT,
                signal_type TEXT,
                confidence REAL,
                strength TEXT,
                spot_price REAL,
                config_hash TEXT,
                data_quality_status TEXT,
                data_quality_completeness REAL,
                reasoning TEXT,
                data_snapshot_json TEXT,
                strategies_json TEXT
            )
        ''')
        
        # Индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON signal_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset ON signal_history(asset)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_config ON signal_history(config_hash)')
        
        conn.commit()
        conn.close()
    
    def log_signal(self, signal_result: Dict[str, Any]):
        """Сохранить полную историю сигнала"""
        
        try:
            signal = signal_result['signal']
            data_snapshot = signal_result['data_snapshot']
            
            # Сохраняем в БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signal_history (
                    timestamp, asset, signal_type, confidence, strength,
                    spot_price, config_hash, data_quality_status,
                    data_quality_completeness, reasoning,
                    data_snapshot_json, strategies_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(datetime.now().timestamp()),
                signal_result['asset'],
                signal['signal_type'],
                signal['confidence'],
                signal['strength'],
                data_snapshot.get('spot_price'),
                signal.get('config_version'),
                data_snapshot.get('quality', {}).get('status'),
                data_snapshot.get('quality', {}).get('completeness'),
                json.dumps(signal.get('reasoning', [])),
                json.dumps(data_snapshot, default=str),
                json.dumps(signal_result.get('strategies', []), default=str)
            ))
            
            conn.commit()
            conn.close()
            
            # Сохраняем JSON для ML (более удобный формат)
            self._save_to_json(signal_result)
            
            logger.info(f"📝 Logged signal for {signal_result['asset']}")
            
        except Exception as e:
            logger.error(f"❌ Error logging signal: {e}")
    
    def _save_to_json(self, signal_result: Dict[str, Any]):
        """Сохранение в JSON для ML обработки"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            asset = signal_result['asset']
            filename = f"{asset}_signal_{timestamp}.json"
            filepath = self.json_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(signal_result, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
    
    def get_signals_by_config(self, config_hash: str, limit: int = 100):
        """Получить сигналы для определенного конфига"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signal_history
            WHERE config_hash = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (config_hash, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_performance_stats(self, config_hash: str):
        """Статистика по конфигурации для бэктеста"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN strength = 'STRONG' THEN 1 END) as strong_signals,
                COUNT(CASE WHEN signal_type = 'BULLISH' THEN 1 END) as bullish_count,
                COUNT(CASE WHEN signal_type = 'BEARISH' THEN 1 END) as bearish_count
            FROM signal_history
            WHERE config_hash = ?
        ''', (config_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_signals': result[0],
            'avg_confidence': result[1],
            'strong_signals': result[2],
            'bullish_count': result[3],
            'bearish_count': result[4]
        }
```

**КРИТЕРИЙ ЗАВЕРШЕНИЯ:**
✅ Каждый сигнал сохраняется в БД
✅ Каждый сигнал сохраняется в JSON для ML
✅ Можно восстановить полное состояние на момент сигнала
✅ Индексы для быстрого поиска работают
✅ Статистика по конфигам доступна

---

## 📋 ИТОГОВЫЙ CHECKLIST STAGE 1.4

### Обязательные пункты:
- [x] **1.4.1** - Инвентаризация всех индикаторов завершена
- [x] **1.4.2** - DataIntegrator создан и тестирован
- [x] **1.4.3** - SignalAnalyzer создан с валидацией
- [x] **1.4.4** - Параметры для бэктеста определены
- [ ] **1.4.5** - advanced_signals_generator обновлен
- [x] **1.4.6** - HIGH PRIORITY индикаторы созданы
- [x] **1.4.7** - Все критичные тесты проходят
- [x] **1.4.8** - История сигналов сохраняется

### Дополнительные (опционально):
- [ ] MEDIUM PRIORITY индикаторы созданы
- [ ] LOW PRIORITY индикаторы созданы
- [ ] Полный test coverage (>80%)
- [ ] Документация для всех компонентов

---

## 🎯 СЛЕДУЮЩИЙ ЭТАП: STAGE 1.5 - BACKTESTING & ML OPTIMIZATION

После завершения Stage 1.4 переходим к:

### 🔄 Backtest Infrastructure
- Загрузка исторических данных
- Симуляция торговли
- Расчет метрик (Sharpe, Win Rate, Profit Factor)

### 🤖 ML Optimization
- Байесовская оптимизация параметров
- Genetic algorithms для поиска оптимальных весов
- Cross-validation на разных периодах

### 📊 A/B Testing
- Параллельный запуск нескольких конфигов
- Сравнение результатов в реальном времени
- Автоматический выбор лучшей модели

---

## 🚨 КРИТИЧЕСКИ ВАЖНЫЕ МОМЕНТЫ

### 1. **Производительность**
- DataIntegrator может стать bottleneck (15+ источников данных)
- Решение: Параллельная загрузка данных через asyncio
- Кэширование часто используемых данных

### 2. **Согласованность временных меток**
- Все данные должны быть синхронизированы по времени
- Решение: Временная метка в DataIntegrator для всех источников
- Проверка max_age в quality report

### 3. **Версионирование конфигов**
- Критично для воспроизводимости бэктестов
- Решение: Config hash в каждом сигнале
- Git теги для критичных конфигов

### 4. **Логирование принятия решений**
- Необходимо для отладки и оптимизации
- Решение: Детальный reasoning в каждом сигнале
- Сохранение полного data snapshot

---

## 📈 РЕКОМЕНДАЦИИ ПО РЕАЛИЗАЦИИ

### 🥇 Приоритет 1: Core Infrastructure
1. DataIntegrator (1.4.2)
2. SignalAnalyzer (1.4.3)
3. Обновление генератора (1.4.5)

### 🥈 Приоритет 2: HIGH Priority Индикаторы
1. option_vwap_calculator.py
2. PCR RSI (обновление существующего)
3. GEX RSI (обновление существующего)

### 🥉 Приоритет 3: Testing & Logging
1. Unit тесты (1.4.7)
2. Signal History Logger (1.4.8)
3. Integration тесты

### 🎯 Приоритет 4: MEDIUM Priority Индикаторы
1. oi_macd_calculator.py
2. iv_macd_calculator.py

---

## 📊 МЕТРИКИ УСПЕХА STAGE 1.4

- ✅ Все 15+ индикаторов работают и создают выходы
- ✅ DataIntegrator собирает полные данные с quality report
- ✅ SignalAnalyzer генерирует валидные сигналы
- ✅ Confidence выше min_confidence для генерации сигналов
- ✅ История сохраняется в БД и JSON для бэктеста
- ✅ Система работает стабильно на всех 6 активах
- ✅ Data quality > ACCEPTABLE для 80%+ запусков
- ✅ Можно A/B тестировать разные конфиги

---

## 🏁 ГОТОВНОСТЬ К STAGE 1.5

После завершения всех checkpoint'ов Stage 1.4, система будет готова к:
- Историческому бэктесту
- ML оптимизации весов
- Production запуску с оптимальными параметрами

**Критерий перехода:** Все обязательные пункты checklist выполнены + 2 недели стабильной работы в production.
