#!/usr/bin/env python3
"""
STAGE 1.3.4: PROFESSIONAL COMBINED SIGNALS GENERATOR
Автор: Реальный разработчик, а не ChatGPT
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
import requests
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/signals_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Signal:
    symbol: str
    signal_type: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float  # 0.0 - 1.0
    components: Dict
    timestamp: datetime

class ProfessionalSignalGenerator:
    def __init__(self):
        self.symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        self.telegram_bot_token = "YOUR_BOT_TOKEN"  # ЗАМЕНИ НА РЕАЛЬНЫЙ
        self.telegram_chat_id = "YOUR_CHAT_ID"      # ЗАМЕНИ НА РЕАЛЬНЫЙ
        
    def get_spot_price(self, symbol: str) -> Optional[float]:
        """Получаем актуальную спотовую цену"""
        try:
            conn = sqlite3.connect('data/futures_data.db')
            query = "SELECT last_price FROM spot_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
            df = pd.read_sql_query(query, conn, params=(f"{symbol}USDT",))
            conn.close()
            
            if not df.empty:
                return float(df.iloc[0]['last_price'])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}")
            return None

    def analyze_oi_data(self, symbol: str) -> Dict:
        """Профессиональный анализ OI данных"""
        try:
            conn = sqlite3.connect('data/unlimited_oi.db')
            
            # Получаем последние 100 записей
            query = """
                SELECT timestamp, total_oi, mark_price 
                FROM all_positions_tracking 
                WHERE asset = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            """
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty or len(df) < 10:
                return {"signal": "NO_DATA", "confidence": 0.0}
            
            # Конвертируем timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
            
            # Рассчитываем тренды
            oi_trend = (df['total_oi'].iloc[-1] - df['total_oi'].iloc[0]) / df['total_oi'].iloc[0]
            price_trend = (df['mark_price'].iloc[-1] - df['mark_price'].iloc[0]) / df['mark_price'].iloc[0]
            
            # Логика сигналов
            if oi_trend > 0.05 and price_trend > 0.02:  # 5% рост OI + 2% рост цены
                return {"signal": "BULLISH", "confidence": min(0.8, abs(oi_trend)), "oi_trend": oi_trend}
            elif oi_trend < -0.05 and price_trend < -0.02:  # 5% падение OI + 2% падение цены
                return {"signal": "BEARISH", "confidence": min(0.8, abs(oi_trend)), "oi_trend": oi_trend}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.3, "oi_trend": oi_trend}
                
        except Exception as e:
            logger.error(f"Ошибка анализа OI {symbol}: {e}")
            return {"signal": "ERROR", "confidence": 0.0}

    def analyze_futures_data(self, symbol: str) -> Dict:
        """Анализ фьючерсных данных"""
        try:
            conn = sqlite3.connect('data/futures_data.db')
            
            # Получаем фьючерсные данные
            query = """
                SELECT funding_rate, open_interest, timestamp 
                FROM futures_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 50
            """
            df = pd.read_sql_query(query, conn, params=(f"{symbol}USDT",))
            conn.close()
            
            if df.empty:
                return {"signal": "NO_DATA", "confidence": 0.0}
            
            # Анализ funding rate
            current_funding = float(df['funding_rate'].iloc[0])
            avg_funding = float(df['funding_rate'].mean())
            
            if current_funding > avg_funding * 1.3:  # Высокий funding rate
                return {"signal": "BEARISH", "confidence": 0.6, "funding_rate": current_funding}
            elif current_funding < avg_funding * 0.7:  # Низкий funding rate
                return {"signal": "BULLISH", "confidence": 0.6, "funding_rate": current_funding}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.4, "funding_rate": current_funding}
                
        except Exception as e:
            logger.error(f"Ошибка анализа фьючерсов {symbol}: {e}")
            return {"signal": "ERROR", "confidence": 0.0}

    def analyze_gamma_exposure(self, symbol: str) -> Dict:
        """Анализ Gamma Exposure"""
        try:
            conn = sqlite3.connect('data/options_data.db')
            
            query = """
                SELECT total_gamma, timestamp 
                FROM gamma_exposure 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            """
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return {"signal": "NO_DATA", "confidence": 0.0}
            
            gamma = float(df['total_gamma'].iloc[0])
            
            if gamma > 0:
                return {"signal": "BULLISH", "confidence": 0.5, "gamma": gamma}
            elif gamma < 0:
                return {"signal": "BEARISH", "confidence": 0.5, "gamma": gamma}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.3, "gamma": gamma}
                
        except Exception as e:
            logger.error(f"Ошибка анализа Gamma {symbol}: {e}")
            return {"signal": "ERROR", "confidence": 0.0}

    def analyze_max_pain(self, symbol: str, current_price: float) -> Dict:
        """Анализ Max Pain"""
        try:
            conn = sqlite3.connect('data/options_data.db')
            
            query = """
                SELECT max_pain_price, timestamp 
                FROM max_pain 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return {"signal": "NO_DATA", "confidence": 0.0}
            
            max_pain_price = float(df['max_pain_price'].iloc[0])
            price_diff_pct = (current_price - max_pain_price) / max_pain_price
            
            if price_diff_pct > 0.03:  # Цена на 3% выше max pain
                return {"signal": "BEARISH", "confidence": 0.6, "max_pain": max_pain_price}
            elif price_diff_pct < -0.03:  # Цена на 3% ниже max pain
                return {"signal": "BULLISH", "confidence": 0.6, "max_pain": max_pain_price}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.4, "max_pain": max_pain_price}
                
        except Exception as e:
            logger.error(f"Ошибка анализа Max Pain {symbol}: {e}")
            return {"signal": "ERROR", "confidence": 0.0}

    def generate_combined_signal(self, symbol: str) -> Optional[Signal]:
        """Генерация комбинированного сигнала"""
        try:
            # Получаем текущую цену
            current_price = self.get_spot_price(symbol)
            if not current_price:
                logger.warning(f"Нет данных о цене для {symbol}")
                return None
            
            # Собираем сигналы от всех источников
            signals = {
                'oi': self.analyze_oi_data(symbol),
                'futures': self.analyze_futures_data(symbol),
                'gamma': self.analyze_gamma_exposure(symbol),
                'max_pain': self.analyze_max_pain(symbol, current_price)
            }
            
            # Считаем взвешенный сигнал
            bullish_score = 0.0
            bearish_score = 0.0
            total_confidence = 0.0
            
            for source, data in signals.items():
                if data['signal'] == 'BULLISH':
                    bullish_score += data['confidence']
                elif data['signal'] == 'BEARISH':
                    bearish_score += data['confidence']
                total_confidence += data['confidence']
            
            # Определяем финальный сигнал
            if total_confidence == 0:
                final_signal = "NEUTRAL"
                final_confidence = 0.3
            else:
                net_score = (bullish_score - bearish_score) / total_confidence
                
                if net_score > 0.3:
                    final_signal = "BULLISH"
                    final_confidence = min(0.9, net_score)
                elif net_score < -0.3:
                    final_signal = "BEARISH" 
                    final_confidence = min(0.9, abs(net_score))
                else:
                    final_signal = "NEUTRAL"
                    final_confidence = 0.5
            
            return Signal(
                symbol=symbol,
                signal_type=final_signal,
                confidence=final_confidence,
                components=signals,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации сигнала для {symbol}: {e}")
            return None

    def save_signal_to_db(self, signal: Signal) -> bool:
        """Сохранение сигнала в базу данных"""
        try:
            conn = sqlite3.connect('data/oi_signals.db')
            cursor = conn.cursor()
            
            # Создаем таблицу если нет
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    components_json TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Вставляем сигнал
            cursor.execute('''
                INSERT INTO signals (symbol, signal_type, confidence, components_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                signal.symbol,
                signal.signal_type,
                signal.confidence,
                json.dumps(signal.components),
                signal.timestamp.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сигнала в БД: {e}")
            return False

    def send_telegram_alert(self, signal: Signal) -> bool:
        """Отправка сигнала в Telegram"""
        try:
            if signal.confidence < 0.6:  # Отправляем только уверенные сигналы
                return False
                
            emoji = "🟢" if signal.signal_type == "BULLISH" else "🔴" if signal.signal_type == "BEARISH" else "🟡"
            
            message = f"""
{emoji} *SIGNAL ALERT* {emoji}

*Asset:* {signal.symbol}
*Signal:* {signal.signal_type}
*Confidence:* {signal.confidence:.1%}

*Components:*
• OI: {signal.components['oi']['signal']} ({signal.components['oi']['confidence']:.1%})
• Futures: {signal.components['futures']['signal']} 
• Gamma: {signal.components['gamma']['signal']}
• Max Pain: {signal.components['max_pain']['signal']}

*Time:* {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return False

    def run_analysis(self):
        """Запуск полного анализа"""
        logger.info("🚀 ЗАПУСК PROFESSIONAL SIGNALS GENERATOR")
        logger.info("=" * 60)
        
        signals_generated = 0
        
        for symbol in self.symbols:
            logger.info(f"🔍 Анализируем {symbol}...")
            
            signal = self.generate_combined_signal(symbol)
            if signal:
                # Сохраняем в БД
                self.save_signal_to_db(signal)
                
                # Отправляем в Telegram если уверенный сигнал
                if signal.confidence >= 0.6:
                    self.send_telegram_alert(signal)
                
                # Логируем результат
                status_emoji = "✅" if signal.confidence >= 0.6 else "⚠️"
                logger.info(f"{status_emoji} {symbol}: {signal.signal_type} (confidence: {signal.confidence:.1%})")
                signals_generated += 1
            else:
                logger.warning(f"❌ {symbol}: Не удалось сгенерировать сигнал")
        
        logger.info("=" * 60)
        logger.info(f"✅ Анализ завершен. Сгенерировано сигналов: {signals_generated}/{len(self.symbols)}")

def main():
    """Основная функция"""
    # Создаем директории
    Path('logs').mkdir(exist_ok=True)
    Path('data/signals').mkdir(exist_ok=True)
    
    # Запускаем генератор
    generator = ProfessionalSignalGenerator()
    generator.run_analysis()

if __name__ == "__main__":
    main()
