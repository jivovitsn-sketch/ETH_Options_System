#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIGNAL LOGIC ANALYZER - показывает КАК принимается решение
"""

from data_integrator import DataIntegrator
from signal_analyzer import SignalAnalyzer
from backtest_params import get_default_config
import json

class SignalLogicAnalyzer:
    """Детальный анализ логики"""
    
    def __init__(self):
        self.config = get_default_config()
        self.integrator = DataIntegrator()
        self.analyzer = SignalAnalyzer(self.config)
    
    def analyze_detailed(self, asset: str):
        """Детальный анализ для актива"""
        
        print("=" * 80)
        print(f"🔬 ДЕТАЛЬНЫЙ АНАЛИЗ ЛОГИКИ: {asset}")
        print("=" * 80)
        
        # 1. СОБИРАЕМ ДАННЫЕ
        print("\n📊 ШАГ 1: СБОР ДАННЫХ")
        print("-" * 80)
        data = self.integrator.get_all_data(asset)
        
        print(f"Spot Price: ${data['spot_price']:,.2f}")
        print(f"Доступно источников: {len(data['available_sources'])}/{len(self.integrator.data_sources)}")
        print(f"Качество данных: {data['quality']['status']}")
        
        # 2. АНАЛИЗ ПО ГРУППАМ
        print("\n🔍 ШАГ 2: АНАЛИЗ ПО ГРУППАМ")
        print("-" * 80)
        
        # FUTURES
        print("\n1️⃣ FUTURES GROUP (вес: {:.0%})".format(self.config['futures_weight']))
        futures_result = self.analyzer._analyze_futures(data)
        print(f"   Сигнал: {futures_result['signal']}")
        print(f"   Confidence: {futures_result['confidence']*100:.1f}%")
        print(f"   Reasoning:")
        for reason in futures_result['reasoning']:
            print(f"     • {reason}")
        
        # OPTIONS
        print("\n2️⃣ OPTIONS GROUP (вес: {:.0%})".format(self.config['options_weight']))
        options_result = self.analyzer._analyze_options(data)
        print(f"   Сигнал: {options_result['signal']}")
        print(f"   Confidence: {options_result['confidence']*100:.1f}%")
        print(f"   Reasoning:")
        for reason in options_result['reasoning']:
            print(f"     • {reason}")
        
        # TIMING
        print("\n3️⃣ TIMING GROUP (вес: {:.0%})".format(self.config['timing_weight']))
        timing_result = self.analyzer._analyze_timing(data)
        print(f"   Сигнал: {timing_result['signal']}")
        print(f"   Confidence: {timing_result['confidence']*100:.1f}%")
        print(f"   Reasoning:")
        for reason in timing_result['reasoning']:
            print(f"     • {reason}")
        
        # 3. КОМБИНИРОВАНИЕ
        print("\n🧮 ШАГ 3: КОМБИНИРОВАНИЕ ГРУПП")
        print("-" * 80)
        
        results = {
            'futures': futures_result,
            'options': options_result,
            'timing': timing_result
        }
        
        # Взвешенные confidence
        futures_weighted = futures_result['confidence'] * self.config['futures_weight']
        options_weighted = options_result['confidence'] * self.config['options_weight']
        timing_weighted = timing_result['confidence'] * self.config['timing_weight']
        
        print(f"Futures: {futures_result['confidence']*100:.1f}% × {self.config['futures_weight']:.0%} = {futures_weighted*100:.1f}%")
        print(f"Options: {options_result['confidence']*100:.1f}% × {self.config['options_weight']:.0%} = {options_weighted*100:.1f}%")
        print(f"Timing:  {timing_result['confidence']*100:.1f}% × {self.config['timing_weight']:.0%} = {timing_weighted*100:.1f}%")
        
        total_confidence = futures_weighted + options_weighted + timing_weighted
        print(f"\n📊 ИТОГОВЫЙ CONFIDENCE: {total_confidence*100:.1f}%")
        
        # Определение сигнала
        signals_count = {
            'BULLISH': sum(1 for r in results.values() if r['signal'] == 'BULLISH'),
            'BEARISH': sum(1 for r in results.values() if r['signal'] == 'BEARISH'),
            'NEUTRAL': sum(1 for r in results.values() if r['signal'] == 'NEUTRAL')
        }
        
        print(f"\n🎯 ГОЛОСОВАНИЕ:")
        print(f"   BULLISH: {signals_count['BULLISH']}/3")
        print(f"   BEARISH: {signals_count['BEARISH']}/3")
        print(f"   NEUTRAL: {signals_count['NEUTRAL']}/3")
        
        # Итоговый сигнал
        if signals_count['BULLISH'] >= 2:
            final_signal = 'BULLISH'
        elif signals_count['BEARISH'] >= 2:
            final_signal = 'BEARISH'
        else:
            final_signal = 'NO_SIGNAL'
        
        print(f"\n✅ ИТОГОВЫЙ СИГНАЛ: {final_signal}")
        
        # 4. ФИЛЬТРЫ
        print("\n🚦 ШАГ 4: ПРОВЕРКА ФИЛЬТРОВ")
        print("-" * 80)
        
        min_conf = self.config['min_confidence']
        print(f"Min confidence: {min_conf*100:.0f}%")
        
        if total_confidence >= min_conf:
            print(f"✅ PASS: {total_confidence*100:.1f}% >= {min_conf*100:.0f}%")
        else:
            print(f"❌ FAIL: {total_confidence*100:.1f}% < {min_conf*100:.0f}%")
            print(f"   → Сигнал НЕ будет отправлен")
        
        # Strength
        if total_confidence >= 0.75:
            strength = 'STRONG'
        elif total_confidence >= 0.60:
            strength = 'MODERATE'
        else:
            strength = 'WEAK'
        
        print(f"\n💪 STRENGTH: {strength}")
        
        # 5. ПОКАЗЫВАЕМ КОНКРЕТНЫЕ ЗНАЧЕНИЯ
        print("\n📈 ШАГ 5: КОНКРЕТНЫЕ ЗНАЧЕНИЯ ИНДИКАТОРОВ")
        print("-" * 80)
        
        print("\n🔹 FUTURES:")
        if data.get('futures'):
            f = data['futures']
            print(f"   Funding Rate: {f.get('funding_rate', 0)*100:.3f}%")
            print(f"   Price: ${f.get('price', 0):,.2f}")
        
        if data.get('liquidations'):
            liq = data['liquidations']
            print(f"   Liq Ratio: {liq.get('ratio', 0):.2f}")
            print(f"   Total: ${liq.get('total_usd', 0):,.0f}")
        
        print("\n🔹 OPTIONS:")
        if data.get('pcr'):
            print(f"   PCR: {data['pcr'].get('ratio', 0):.2f}")
        
        if data.get('gex'):
            print(f"   GEX: ${data['gex'].get('total_gamma', 0):,.0f}")
        
        if data.get('max_pain'):
            print(f"   Max Pain: ${data['max_pain'].get('price', 0):,.2f}")
        
        if data.get('vanna'):
            print(f"   Vanna: {data['vanna'].get('total_vanna', 0):,.0f}")
        
        if data.get('iv_rank'):
            print(f"   IV Rank: {data['iv_rank'].get('rank', 0):.1f}%")
        
        print("\n🔹 TIMING:")
        if data.get('pcr_rsi'):
            print(f"   PCR RSI: {data['pcr_rsi']:.1f}")
        
        if data.get('gex_rsi'):
            print(f"   GEX RSI: {data['gex_rsi']:.1f}")
        
        if data.get('oi_macd'):
            macd = data['oi_macd']
            print(f"   OI MACD: {macd.get('histogram', 0):.2f}")
        
        if data.get('option_vwap'):
            vwap = data['option_vwap']
            print(f"   Option VWAP: ${vwap.get('vwap', 0):,.2f}")
        
        print("\n" + "=" * 80)
        print("✅ АНАЛИЗ ЗАВЕРШЁН")
        print("=" * 80)


if __name__ == '__main__':
    analyzer = SignalLogicAnalyzer()
    
    # Анализируем несколько активов
    for asset in ['BTC', 'ETH', 'XRP', 'SOL', 'DOGE', 'MNT']:
        analyzer.analyze_detailed(asset)
        print("\n\n")
