#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVANCED SIGNALS GENERATOR - Stage 1.4 Integration
Интеграция DataIntegrator + SignalAnalyzer + SignalHistoryLogger
"""

import sqlite3
import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# NEW COMPONENTS
from data_integrator import DataIntegrator
from signal_analyzer import SignalAnalyzer
from signal_history_logger import SignalHistoryLogger
from backtest_params import get_default_config

# OLD IMPORTS (для совместимости)
from asset_config import get_min_confidence, get_min_interval
from option_pricing import (
    OptionPricing, 
    OptionPositionManager, 
    generate_option_strategies, 
    format_option_signal_message
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class SignalGenerator:
    def __init__(self):
        # Старые параметры
        self.db_path = 'data/oi_signals.db'
        self.assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        
        # НОВЫЕ КОМПОНЕНТЫ - STAGE 1.4
        logger.info("🚀 Initializing Stage 1.4 components...")
        self.config = get_default_config()
        self.data_integrator = DataIntegrator()
        self.signal_analyzer = SignalAnalyzer(self.config)
        self.history_logger = SignalHistoryLogger()
        
        logger.info(f"✅ Config: {self.signal_analyzer._get_config_hash()}")
        logger.info(f"✅ Min confidence: {self.config['min_confidence']}")
        
        # Инициализация БД для сигналов
        self._init_signals_db()
    
    def _init_signals_db(self):
        """Инициализация БД для сигналов (совместимость)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                asset TEXT,
                signal_type TEXT,
                confidence REAL,
                spot_price REAL,
                message TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_last_signal_time(self, asset):
        """Получить время последнего сигнала для актива"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp FROM signals
            WHERE asset = ? AND signal_type != 'NO_SIGNAL'
            ORDER BY timestamp DESC LIMIT 1
        ''', (asset,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return datetime.fromtimestamp(result[0])
        return None
    
    def should_send_signal(self, asset, signal_result):
        """Проверка нужно ли отправлять сигнал"""
        
        # Проверка confidence
        if signal_result['confidence'] < self.config['min_confidence']:
            return False
        
        # Проверка типа сигнала
        if signal_result['signal_type'] == 'NO_SIGNAL':
            return False
        
        # Проверка интервала
        last_time = self.get_last_signal_time(asset)
        if last_time:
            min_interval = get_min_interval(asset)
            time_diff = datetime.now() - last_time
            if time_diff.total_seconds() < min_interval * 60:
                return False
        
        return True
    
    def send_telegram_message(self, message, is_vip=False):
        """Отправка сообщения в Telegram"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            
            if is_vip:
                chat_id = os.getenv('VIP_CHAT_ID')
            else:
                chat_id = os.getenv('FREE_CHAT_ID')
            
            if not bot_token or not chat_id:
                logger.warning("⚠️ Telegram credentials not found")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram message sent")
                return True
            else:
                logger.error(f"❌ Telegram error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram exception: {e}")
            return False
    
    def save_signal_to_db(self, asset, signal_type, confidence, spot_price, message):
        """Сохранение сигнала в БД (совместимость)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals (timestamp, asset, signal_type, confidence, spot_price, message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                int(datetime.now().timestamp()),
                asset,
                signal_type,
                confidence,
                spot_price,
                message
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error saving to DB: {e}")
    
    def process_asset(self, asset):
        """Обработка одного актива - НОВАЯ ЛОГИКА STAGE 1.4"""
        logger.info(f"🔍 Анализируем {asset}...")
        
        try:
            # 1. СОБИРАЕМ ДАННЫЕ через DataIntegrator
            data = self.data_integrator.get_all_data(asset)
            
            quality = data.get('quality', {})
            logger.info(f"📊 Data quality: {quality.get('status')} ({quality.get('completeness', 0)*100:.0f}%)")
            
            # 2. АНАЛИЗИРУЕМ через SignalAnalyzer
            signal_result = self.signal_analyzer.analyze(data)
            
            if not signal_result:
                logger.info(f"➡️ {asset}: No signal generated (filters)")
                return False
            
            # 3. ПРОВЕРЯЕМ нужно ли отправлять
            if not self.should_send_signal(asset, signal_result):
                logger.info(f"➡️ {asset}: {signal_result['signal_type']} ({signal_result['confidence']*100:.0f}%) - skip")
                return False
            
            # 4. ГЕНЕРАЦИЯ ОПЦИОННЫХ СТРАТЕГИЙ
            spot_price = data.get('spot_price')
            if not spot_price:
                logger.warning(f"⚠️ {asset}: No spot price")
                return False
            
            strategies = generate_option_strategies(
                asset, 
                signal_result['signal_type'], 
                spot_price, 
                signal_result['confidence']
            )
            
            # 5. ФОРМИРОВАНИЕ СООБЩЕНИЯ
            message = format_option_signal_message(
                asset,
                signal_result['signal_type'],
                signal_result['confidence'],
                spot_price,
                strategies
            )
            
            # Добавляем reasoning
            if signal_result.get('reasoning'):
                message += "\n\n📊 **АНАЛИЗ:**\n"
                for reason in signal_result['reasoning'][:3]:
                    message += f"• {reason}\n"
            
            # 6. ОТПРАВКА В TELEGRAM
            self.send_telegram_message(message, is_vip=True)
            
            # 7. СОХРАНЕНИЕ
            # Старая БД (совместимость)
            self.save_signal_to_db(
                asset,
                signal_result['signal_type'],
                signal_result['confidence'],
                spot_price,
                message
            )
            
            # Новая система - SignalHistoryLogger
            history_entry = {
                'asset': asset,
                'signal': signal_result,
                'data_snapshot': data,
                'strategies': strategies
            }
            self.history_logger.log_signal(history_entry)
            
            logger.info(f"✅ {asset}: {signal_result['signal_type']} ({signal_result['confidence']*100:.0f}%) sent!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing {asset}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_analysis(self):
        """Запуск анализа для всех активов"""
        logger.info("=" * 80)
        logger.info(f"🚀 SIGNAL GENERATION: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📝 Config: {self.signal_analyzer._get_config_hash()}")
        logger.info("=" * 80)
        
        sent_count = 0
        
        for asset in self.assets:
            if self.process_asset(asset):
                sent_count += 1
            time.sleep(2)  # Пауза между активами
        
        logger.info("=" * 80)
        logger.info(f"✅ Analysis complete. Signals sent: {sent_count}/{len(self.assets)}")
        logger.info("=" * 80)


if __name__ == '__main__':
    generator = SignalGenerator()
    generator.run_analysis()
