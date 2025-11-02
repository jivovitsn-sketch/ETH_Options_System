#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART SIGNAL SENDER v2 - С интеграцией OI Dynamics и Walls Analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os
from config import ASSETS, MIN_CONFIDENCE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/smart_signals.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SmartSignalSenderV2:
    """Генератор сигналов с OI Dynamics и Walls"""
    
    def __init__(self):
        self.min_confidence = MIN_CONFIDENCE
        self.signal_history_file = 'data/signal_history_v2.json'
        self.last_signals = self._load_history()
    
    def _load_history(self) -> Dict:
        """Загрузка истории сигналов"""
        import json
        if os.path.exists(self.signal_history_file):
            try:
                with open(self.signal_history_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_history(self):
        """Сохранение истории"""
        import json
        os.makedirs('data', exist_ok=True)
        with open(self.signal_history_file, 'w') as f:
            json.dump(self.last_signals, f, indent=2)
    
    def _is_duplicate(self, asset: str, signal_type: str) -> bool:
        """Проверка дубликата"""
        key = f"{asset}_{signal_type}"
        if key in self.last_signals:
            last_time = datetime.fromisoformat(self.last_signals[key])
            if datetime.now() - last_time < timedelta(hours=4):
                return True
        return False
    
    def _mark_sent(self, asset: str, signal_type: str):
        """Отметить отправленный сигнал"""
        key = f"{asset}_{signal_type}"
        self.last_signals[key] = datetime.now().isoformat()
        self._save_history()
    
    def generate_signal(self, asset: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Генерация сигнала с учётом OI Dynamics и Walls"""
        
        # Базовый анализ (существующий)
        base_signal = self._analyze_base_indicators(asset, data)
        
        # Анализ стенок
        walls_boost = self._analyze_walls(asset, data)
        
        # Анализ динамики OI
        oi_dynamics_boost = self._analyze_oi_dynamics(asset, data)
        
        # Комбинированный confidence
        total_confidence = base_signal['confidence']
        total_confidence += walls_boost['confidence_boost']
        total_confidence += oi_dynamics_boost['confidence_boost']
        total_confidence = min(1.0, total_confidence)
        
        # Проверка порога
        if total_confidence < self.min_confidence:
            logger.info(f"{asset}: Confidence {total_confidence:.0%} < {self.min_confidence:.0%}")
            return None
        
        # Определяем тип сигнала
        signal_type = self._determine_signal_type(
            base_signal,
            walls_boost,
            oi_dynamics_boost
        )
        
        # Проверка дубликатов
        if self._is_duplicate(asset, signal_type):
            logger.info(f"{asset}: Duplicate signal {signal_type} blocked")
            return None
        
        # Формируем полный сигнал
        full_signal = {
            'asset': asset,
            'timestamp': datetime.now().isoformat(),
            'signal_type': signal_type,
            'confidence': total_confidence,
            'base_analysis': base_signal,
            'walls_analysis': walls_boost,
            'oi_dynamics_analysis': oi_dynamics_boost,
            'recommended_strategies': self._get_strategies(
                asset, data, signal_type, walls_boost, oi_dynamics_boost
            )
        }
        
        # Отмечаем как отправленный
        self._mark_sent(asset, signal_type)
        
        return full_signal
    
    def _analyze_base_indicators(self, asset: str, data: Dict) -> Dict[str, Any]:
        """Базовый анализ индикаторов"""
        
        confidence = 0.5
        signals = []
        
        # Funding Rate
        funding = data.get('funding_rate')
        if funding:
            rate = funding.get('current_rate', 0)
            if rate > 0.01:
                confidence += 0.05
                signals.append("High positive funding")
            elif rate < -0.01:
                confidence += 0.05
                signals.append("High negative funding")
        
        # Liquidations
        liq = data.get('liquidations')
        if liq:
            ratio = liq.get('long_short_ratio', 1.0)
            if ratio > 2.0:
                confidence += 0.05
                signals.append("Heavy short liquidations")
            elif ratio < 0.5:
                confidence += 0.05
                signals.append("Heavy long liquidations")
        
        # PCR
        pcr = data.get('pcr')
        if pcr:
            value = pcr.get('current', 1.0)
            if value > 1.2:
                confidence += 0.03
                signals.append("High put/call ratio")
            elif value < 0.8:
                confidence += 0.03
                signals.append("Low put/call ratio")
        
        return {
            'confidence': min(0.7, confidence),
            'signals': signals
        }
    
    def _analyze_walls(self, asset: str, data: Dict) -> Dict[str, Any]:
        """Анализ стенок экспираций"""
        
        walls = data.get('expiration_walls')
        if not walls:
            return {'confidence_boost': 0.0, 'signals': [], 'walls_data': None}
        
        magnetic = walls.get('magnetic_levels', {})
        pressure = walls.get('pressure_analysis', {})
        
        boost = 0.0
        signals = []
        
        # Сила стенок
        call_wall = magnetic.get('call_wall')
        put_wall = magnetic.get('put_wall')
        call_oi = magnetic.get('call_wall_oi', 0)
        put_oi = magnetic.get('put_wall_oi', 0)
        
        if call_oi > 10000:  # Сильная call wall
            boost += 0.05
            signals.append(f"Strong call wall at ${call_wall:,.0f}")
        
        if put_oi > 10000:  # Сильная put wall
            boost += 0.05
            signals.append(f"Strong put wall at ${put_wall:,.0f}")
        
        # Pressure direction
        direction = pressure.get('direction')
        if direction in ['BEARISH', 'BULLISH']:
            boost += 0.03
            signals.append(f"{direction} pressure detected")
        
        return {
            'confidence_boost': min(0.15, boost),
            'signals': signals,
            'walls_data': magnetic
        }
    
    def _analyze_oi_dynamics(self, asset: str, data: Dict) -> Dict[str, Any]:
        """Анализ динамики OI"""
        
        dynamics = data.get('oi_dynamics')
        if not dynamics:
            return {'confidence_boost': 0.0, 'signals': [], 'oi_signal': None}
        
        summary = dynamics.get('summary', {})
        signal = summary.get('overall_signal', 'NEUTRAL')
        oi_confidence = summary.get('confidence', 0.0)
        
        boost = 0.0
        signals = []
        
        if signal == 'WALL_STRENGTHENING':
            boost = oi_confidence * 0.15  # До 15% boost
            signals.append(f"🔒 Wall strengthening ({oi_confidence:.0%} conf)")
        
        elif signal == 'WALL_WEAKENING':
            boost = oi_confidence * 0.15
            signals.append(f"💥 Wall weakening ({oi_confidence:.0%} conf)")
        
        elif signal == 'BULLISH_SENTIMENT':
            boost = oi_confidence * 0.10
            signals.append(f"🐂 Bullish sentiment shift ({oi_confidence:.0%} conf)")
        
        elif signal == 'BEARISH_SENTIMENT':
            boost = oi_confidence * 0.10
            signals.append(f"🐻 Bearish sentiment shift ({oi_confidence:.0%} conf)")
        
        return {
            'confidence_boost': boost,
            'signals': signals,
            'oi_signal': signal
        }
    
    def _determine_signal_type(self, base: Dict, walls: Dict, oi: Dict) -> str:
        """Определение типа сигнала"""
        
        oi_signal = oi.get('oi_signal', 'NEUTRAL')
        
        # Приоритет OI Dynamics сигналам
        if oi_signal == 'WALL_STRENGTHENING':
            return 'BOUNCE_EXPECTED'
        elif oi_signal == 'WALL_WEAKENING':
            return 'BREAKOUT_POSSIBLE'
        elif oi_signal == 'BULLISH_SENTIMENT':
            return 'BULLISH'
        elif oi_signal == 'BEARISH_SENTIMENT':
            return 'BEARISH'
        
        # Fallback на базовый анализ
        if 'High positive funding' in base.get('signals', []):
            return 'BEARISH'
        elif 'High negative funding' in base.get('signals', []):
            return 'BULLISH'
        
        return 'NEUTRAL'
    
    def _get_strategies(self, asset: str, data: Dict, 
                       signal_type: str, walls: Dict, oi: Dict) -> List[str]:
        """Рекомендованные стратегии"""
        
        strategies = []
        walls_data = walls.get('walls_data', {})
        
        if signal_type == 'BOUNCE_EXPECTED':
            call_wall = walls_data.get('call_wall')
            put_wall = walls_data.get('put_wall')
            
            if call_wall:
                strategies.append(f"Bear Call Spread near ${call_wall:,.0f}")
            if put_wall:
                strategies.append(f"Bull Put Spread near ${put_wall:,.0f}")
            if call_wall and put_wall:
                strategies.append(f"Iron Condor ${put_wall:,.0f}-${call_wall:,.0f}")
        
        elif signal_type == 'BREAKOUT_POSSIBLE':
            call_wall = walls_data.get('call_wall')
            put_wall = walls_data.get('put_wall')
            
            if call_wall:
                strategies.append(f"Long Call above ${call_wall:,.0f}")
            if put_wall:
                strategies.append(f"Long Put below ${put_wall:,.0f}")
        
        elif signal_type == 'BULLISH':
            strategies.append("Bull Call Spread")
            strategies.append("Long Call")
        
        elif signal_type == 'BEARISH':
            strategies.append("Bear Put Spread")
            strategies.append("Long Put")
        
        return strategies
    
    def format_telegram_message(self, signal: Dict[str, Any]) -> str:
        """Форматирование сообщения для Telegram"""
        
        asset = signal['asset']
        signal_type = signal['signal_type']
        confidence = signal['confidence']
        
        # Эмодзи для типов сигналов
        emoji_map = {
            'BOUNCE_EXPECTED': '🔒',
            'BREAKOUT_POSSIBLE': '💥',
            'BULLISH': '🐂',
            'BEARISH': '🐻',
            'NEUTRAL': '😐'
        }
        emoji = emoji_map.get(signal_type, '📊')
        
        msg = f"{emoji} <b>{asset} SIGNAL</b>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        msg += f"🎯 <b>Type:</b> {signal_type}\n"
        msg += f"💪 <b>Confidence:</b> {confidence:.0%}\n\n"
        
        # Base indicators
        base_signals = signal['base_analysis'].get('signals', [])
        if base_signals:
            msg += f"📊 <b>Base Indicators:</b>\n"
            for s in base_signals[:3]:
                msg += f"  • {s}\n"
            msg += "\n"
        
        # Walls analysis
        walls_signals = signal['walls_analysis'].get('signals', [])
        if walls_signals:
            msg += f"🧱 <b>Walls:</b>\n"
            for s in walls_signals:
                msg += f"  • {s}\n"
            msg += "\n"
        
        # OI Dynamics
        oi_signals = signal['oi_dynamics_analysis'].get('signals', [])
        if oi_signals:
            msg += f"🔄 <b>OI Dynamics:</b>\n"
            for s in oi_signals:
                msg += f"  • {s}\n"
            msg += "\n"
        
        # Strategies
        strategies = signal.get('recommended_strategies', [])
        if strategies:
            msg += f"💡 <b>Strategies:</b>\n"
            for i, strat in enumerate(strategies[:3], 1):
                msg += f"  {i}. {strat}\n"
            msg += "\n"
        
        msg += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        
        return msg
    
    def send_to_telegram(self, message: str) -> bool:
        """Отправка в Telegram"""
        try:
            from telegram_sender import send_telegram_message
            return send_telegram_message(message)
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False


def main():
    """Главная функция"""
    from data_integrator import DataIntegrator
    
    print("🚀 SMART SIGNAL SENDER V2")
    print("=" * 60)
    print("📊 Enhanced with OI Dynamics + Walls Analysis")
    print()
    
    integrator = DataIntegrator()
    sender = SmartSignalSenderV2()
    
    signals_sent = 0
    
    for asset in ASSETS:
        print(f"\n🔍 Analyzing {asset}...")
        
        # Получаем все данные
        data = integrator.get_all_data(asset)
        quality = data.get('quality', {})
        
        print(f"   Data quality: {quality.get('status')} ({quality.get('completeness', 0)*100:.0f}%)")
        
        # Генерируем сигнал
        signal = sender.generate_signal(asset, data)
        
        if signal:
            print(f"   ✅ SIGNAL: {signal['signal_type']} ({signal['confidence']:.0%})")
            
            # Форматируем и отправляем
            message = sender.format_telegram_message(signal)
            
            print("\n" + "="*60)
            print("MESSAGE PREVIEW:")
            print("="*60)
            # Убираем HTML теги для консольного вывода
            import re
            clean_msg = re.sub('<[^<]+?>', '', message)
            print(clean_msg)
            print("="*60)
            
            # Отправляем
            if sender.send_to_telegram(message):
                print("   📤 Sent to Telegram!")
                signals_sent += 1
            else:
                print("   ⚠️ Telegram send failed")
        else:
            print(f"   ⏸️ No signal (below threshold)")
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY: {signals_sent} signals sent")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
