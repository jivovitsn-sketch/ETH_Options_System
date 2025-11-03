#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART SIGNAL SENDER - FIXED
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram_sender import send_message
from data_integrator import DataIntegrator
from signal_analyzer import SignalAnalyzer
from backtest_params import get_default_config
import logging

# Загружаем .env ПЕРЕД импортом telegram_sender
load_dotenv()

from telegram_sender import send_to_telegram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartSignalSender:
    """Умная отправка сигналов"""
    
    def __init__(self):
        self.config = get_default_config()
        
        # ВАЖНО: Поднимаем порог до 65%!
        self.config['min_confidence'] = 0.65
        
        self.integrator = DataIntegrator()
        self.analyzer = SignalAnalyzer(self.config)
        
        self.vip_chat = os.getenv('VIP_CHAT_ID')
        self.free_chat = os.getenv('FREE_CHAT_ID')
        
        # Проверяем credentials
        if not self.vip_chat:
            logger.error("❌ VIP_CHAT_ID not configured!")
        else:
            logger.info(f"✅ VIP_CHAT_ID configured")
        
        self.history_file = './data/sent_signals_history.json'
        self.load_history()
    
    def load_history(self):
        """Загрузить историю"""
        try:
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        except:
            self.history = {}
    
    def save_history(self):
        """Сохранить историю"""
        os.makedirs('./data', exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def get_signal_hash(self, asset: str, signal_type: str, confidence: float) -> str:
        """Хэш сигнала"""
        conf_rounded = round(confidence, 2)
        key = f"{asset}_{signal_type}_{conf_rounded}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def is_duplicate(self, signal_hash: str, min_hours: int = 4) -> bool:
        """Проверка на дубликат"""
        if signal_hash not in self.history:
            return False
        
        last_sent = datetime.fromisoformat(self.history[signal_hash])
        age = (datetime.now() - last_sent).total_seconds() / 3600
        
        return age < min_hours
    
    def format_message(self, asset: str, signal: dict, data: dict) -> str:
        """Форматирование сообщения"""
        
        msg = f"🎯 **{signal['signal_type']} SIGNAL: {asset}**\n"
        msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        msg += f"📊 **CONFIDENCE: {signal['confidence']*100:.1f}%**\n"
        msg += f"💪 Strength: {signal['strength']}\n"
        msg += f"💰 Spot: ${data['spot_price']:,.2f}\n\n"
        
        # DATA QUALITY
        quality = data.get('quality', {})
        msg += f"🔍 **DATA:**\n"
        msg += f"  Quality: {quality.get('status', 'UNKNOWN')}\n"
        msg += f"  Sources: {quality.get('available_sources', 0)}/{quality.get('total_sources', 0)}\n\n"
        
        # TOP REASONS
        if signal.get('reasoning'):
            msg += f"💡 **KEY FACTORS:**\n"
            for i, reason in enumerate(signal['reasoning'][:5], 1):
                msg += f"  {i}. {reason}\n"
            msg += "\n"
        
        # KEY INDICATORS
        msg += f"📈 **INDICATORS:**\n"
        
        if data.get('pcr'):
            msg += f"  • PCR: {data['pcr'].get('ratio', 0):.2f}\n"
        
        if data.get('pcr_rsi'):
            msg += f"  • PCR RSI: {data['pcr_rsi']:.0f}\n"
        
        if data.get('gex_rsi'):
            msg += f"  • GEX RSI: {data['gex_rsi']:.0f}\n"
        
        msg += "\n⚠️ Not financial advice • DYOR • Manage risk\n"
        
        return msg
    
    def process_asset(self, asset: str):
        """Обработать актив"""
        logger.info(f"🔍 {asset}...")
        
        # Собираем данные
        data = self.integrator.get_all_data(asset)
        
        # Анализируем
        signal = self.analyzer.analyze(data)
        
        if not signal:
            logger.info(f"  ➡️ NO SIGNAL")
            return False
        
        conf_pct = signal['confidence'] * 100
        
        # ФИЛЬТР: только сильные сигналы!
        if signal['confidence'] < self.config['min_confidence']:
            logger.info(f"  ➡️ {signal['signal_type']} ({conf_pct:.0f}%) - TOO WEAK, skipped")
            return False
        
        # Проверяем дубликат
        signal_hash = self.get_signal_hash(
            asset,
            signal['signal_type'],
            signal['confidence']
        )
        
        if self.is_duplicate(signal_hash, min_hours=4):
            logger.info(f"  ⚠️ DUPLICATE (sent <4h ago)")
            return False
        
        # Форматируем
        message = self.format_message(asset, signal, data)
        
        # Отправляем
        success = send_to_telegram(message, self.vip_chat)
        
        if success:
            # Если >70%, отправляем и в FREE
            if signal['confidence'] > 0.70 and self.free_chat and self.free_chat != self.vip_chat:
                send_to_telegram(message, self.free_chat)
            
            # Сохраняем в историю
            self.history[signal_hash] = datetime.now().isoformat()
            self.save_history()
            
            logger.info(f"  ✅ {signal['signal_type']} ({conf_pct:.0f}%) SENT!")
            return True
        else:
            logger.error(f"  ❌ Failed to send")
            return False
    
    def run(self):
        """Запуск"""
        logger.info("=" * 60)
        logger.info("🚀 SMART SIGNAL SENDER")
        logger.info("=" * 60)
        
        assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        
        sent_count = 0
        for asset in assets:
            if self.process_asset(asset):
                sent_count += 1
        
        logger.info("=" * 60)
        logger.info(f"✅ Sent {sent_count}/{len(assets)} signals")
        logger.info("=" * 60)


if __name__ == '__main__':
    sender = SmartSignalSender()
    sender.run()
