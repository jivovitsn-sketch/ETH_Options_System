#!/usr/bin/env python3
"""
SMART SIGNALS GENERATOR - ТОЛЬКО НА ЗАКРЫТИИ СВЕЧИ И ПРИ ИЗМЕНЕНИИ СИГНАЛА
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Загружаем переменные из .env
def load_env():
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
        print("✅ .env файл загружен")
    except FileNotFoundError:
        print("❌ .env файл не найден")
    return env_vars

env_vars = load_env()

# Настройка логирования
logging.basicConfig(
    level=env_vars.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/smart_signals.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartSignalGenerator:
    def __init__(self):
        self.symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        
        # Telegram настройки
        self.telegram_bot_token = env_vars.get('TELEGRAM_BOT_TOKEN', '')
        self.admin_chat_id = env_vars.get('TELEGRAM_ADMIN_CHAT_ID', '')
        self.free_chat_id = env_vars.get('TELEGRAM_FREE_CHAT_ID', '')
        self.vip_chat_id = env_vars.get('TELEGRAM_VIP_CHAT_ID', '')
        
        # Прокси настройки
        self.proxy_url = env_vars.get('TELEGRAM_PROXY_URL', '')
        self.proxy_username = env_vars.get('TELEGRAM_PROXY_USERNAME', '')
        self.proxy_password = env_vars.get('TELEGRAM_PROXY_PASSWORD', '')
        
        # Настраиваем прокси
        self.proxies = None
        if self.proxy_url:
            proxy_auth = f"{self.proxy_username}:{self.proxy_password}@" if self.proxy_username else ""
            self.proxies = {
                'http': f"http://{proxy_auth}{self.proxy_url.replace('http://', '')}",
                'https': f"http://{proxy_auth}{self.proxy_url.replace('http://', '')}",
            }
        
        # Настройки сигналов
        self.min_confidence = 0.7  # Минимальная уверенность для отправки
        self.signal_timeframe = 15  # Таймфрейм в минутах для закрытия свечи
        
        logger.info(f"🔧 Умные сигналы: уверенность ≥{self.min_confidence}, таймфрейм {self.signal_timeframe}мин")
        
    def get_last_signal(self, symbol: str) -> dict:
        """Получаем последний отправленный сигнал для символа"""
        try:
            conn = sqlite3.connect('data/oi_signals.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT signal_type, signal_strength, timestamp 
                FROM signals 
                WHERE asset = ? AND signal_strength >= ?
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (symbol, self.min_confidence))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'signal_type': result[0],
                    'confidence': result[1],
                    'timestamp': result[2]
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения последнего сигнала {symbol}: {e}")
            return None

    def should_send_signal(self, symbol: str, new_signal: dict) -> bool:
        """Определяем, нужно ли отправлять сигнал"""
        last_signal = self.get_last_signal(symbol)
        
        # Если нет предыдущего сигнала - отправляем сильный сигнал
        if not last_signal:
            return new_signal['confidence'] >= self.min_confidence
        
        # Проверяем время - отправляем только на закрытии свечи
        current_time = datetime.now()
        last_signal_time = datetime.fromtimestamp(last_signal['timestamp'])
        time_diff = (current_time - last_signal_time).total_seconds() / 60
        
        # Если не прошло достаточно времени с последнего сигнала - не отправляем
        if time_diff < self.signal_timeframe:
            logger.info(f"⏰ {symbol}: Пропускаем - прошло всего {time_diff:.1f} мин")
            return False
        
        # Проверяем изменение сигнала
        signal_changed = (
            last_signal['signal_type'] != new_signal['signal'] or
            abs(last_signal['confidence'] - new_signal['confidence']) > 0.2
        )
        
        # Отправляем только если сигнал изменился И он сильный
        should_send = signal_changed and new_signal['confidence'] >= self.min_confidence
        
        if should_send:
            logger.info(f"🔄 {symbol}: Сигнал изменился {last_signal['signal_type']}→{new_signal['signal']}")
        else:
            logger.info(f"➡️ {symbol}: Сигнал не изменился или слабый")
        
        return should_send

    def get_spot_price(self, symbol: str) -> float:
        """Получаем актуальную спотовую цену"""
        try:
            conn = sqlite3.connect('data/futures_data.db')
            query = "SELECT last_price FROM spot_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
            df = pd.read_sql_query(query, conn, params=(f"{symbol}USDT",))
            conn.close()
            
            if not df.empty:
                return float(df.iloc[0]['last_price'])
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}")
            return 0.0

    def analyze_oi_data(self, symbol: str) -> dict:
        """Анализ OI данных"""
        try:
            conn = sqlite3.connect('data/unlimited_oi.db')
            
            query = """
                SELECT timestamp, open_interest, strike, option_type
                FROM all_positions_tracking 
                WHERE asset = ? 
                ORDER BY timestamp DESC 
                LIMIT 200
            """
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty or len(df) < 10:
                return {"signal": "NEUTRAL", "confidence": 0.3}
            
            # Группируем по timestamp и считаем общий OI
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            oi_by_time = df.groupby('timestamp')['open_interest'].sum().reset_index()
            oi_by_time = oi_by_time.sort_values('timestamp')
            
            if len(oi_by_time) < 5:
                return {"signal": "NEUTRAL", "confidence": 0.3}
            
            # Анализируем тренд OI
            recent_oi = oi_by_time['open_interest'].tail(5)
            oi_trend = (recent_oi.iloc[-1] - recent_oi.iloc[0]) / recent_oi.iloc[0] if recent_oi.iloc[0] != 0 else 0
            
            # Анализ распределения по страйкам
            current_data = df[df['timestamp'] == df['timestamp'].max()]
            call_oi = current_data[current_data['option_type'] == 'CALL']['open_interest'].sum()
            put_oi = current_data[current_data['option_type'] == 'PUT']['open_interest'].sum()
            
            if call_oi + put_oi == 0:
                return {"signal": "NEUTRAL", "confidence": 0.3}
            
            call_put_ratio = call_oi / (call_oi + put_oi)
            
            # Логика сигналов на основе OI
            if oi_trend > 0.1 and call_put_ratio > 0.6:
                return {"signal": "BULLISH", "confidence": min(0.9, oi_trend), "oi_trend": oi_trend}
            elif oi_trend < -0.1 and call_put_ratio < 0.4:
                return {"signal": "BEARISH", "confidence": min(0.9, abs(oi_trend)), "oi_trend": oi_trend}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.3, "oi_trend": oi_trend}
                
        except Exception as e:
            logger.error(f"Ошибка анализа OI {symbol}: {e}")
            return {"signal": "NEUTRAL", "confidence": 0.3}

    def analyze_price_trend(self, symbol: str) -> dict:
        """Анализ ценового тренда"""
        try:
            conn = sqlite3.connect('data/futures_data.db')
            
            query = """
                SELECT last_price, timestamp 
                FROM spot_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            """
            df = pd.read_sql_query(query, conn, params=(f"{symbol}USDT",))
            conn.close()
            
            if df.empty or len(df) < 10:
                return {"signal": "NEUTRAL", "confidence": 0.3}
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
            
            # Анализ тренда за разные периоды
            short_trend = (df['last_price'].iloc[-1] - df['last_price'].iloc[-5]) / df['last_price'].iloc[-5]
            medium_trend = (df['last_price'].iloc[-1] - df['last_price'].iloc[-20]) / df['last_price'].iloc[-20]
            
            # Комбинированный сигнал
            if short_trend > 0.03 and medium_trend > 0.05:
                return {"signal": "BULLISH", "confidence": min(0.9, (short_trend + medium_trend)/2), "trend": (short_trend + medium_trend)/2}
            elif short_trend < -0.03 and medium_trend < -0.05:
                return {"signal": "BEARISH", "confidence": min(0.9, abs(short_trend + medium_trend)/2), "trend": (short_trend + medium_trend)/2}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.3, "trend": (short_trend + medium_trend)/2}
                
        except Exception as e:
            logger.error(f"Ошибка анализа цены {symbol}: {e}")
            return {"signal": "NEUTRAL", "confidence": 0.3}

    def generate_combined_signal(self, symbol: str) -> dict:
        """Генерация комбинированного сигнала"""
        try:
            current_price = self.get_spot_price(symbol)
            if current_price == 0:
                return {"symbol": symbol, "signal": "NEUTRAL", "confidence": 0.3}
            
            # Собираем сигналы от всех источников
            signals = {
                'oi': self.analyze_oi_data(symbol),
                'price': self.analyze_price_trend(symbol)
            }
            
            # Взвешиваем сигналы
            weights = {'oi': 0.6, 'price': 0.4}
            bullish_score = 0.0
            bearish_score = 0.0
            
            for source, data in signals.items():
                weight = weights[source]
                if data['signal'] == 'BULLISH':
                    bullish_score += data['confidence'] * weight
                elif data['signal'] == 'BEARISH':
                    bearish_score += data['confidence'] * weight
            
            # Определяем финальный сигнал
            if bullish_score > bearish_score + 0.2:
                final_signal = "BULLISH"
                final_confidence = min(0.95, bullish_score)
            elif bearish_score > bullish_score + 0.2:
                final_signal = "BEARISH"
                final_confidence = min(0.95, bearish_score)
            else:
                final_signal = "NEUTRAL"
                final_confidence = max(0.3, (bullish_score + bearish_score) / 2)
            
            return {
                "symbol": symbol,
                "signal": final_signal,
                "confidence": final_confidence,
                "price": current_price,
                "components": signals,
                "timestamp": int(datetime.now().timestamp())
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации сигнала для {symbol}: {e}")
            return {"symbol": symbol, "signal": "NEUTRAL", "confidence": 0.3}

    def send_telegram_to_channel(self, chat_id: str, message: str) -> bool:
        """Отправка сообщения в конкретный Telegram канал через прокси"""
        try:
            if not self.telegram_bot_token or not chat_id:
                return False
                
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            # Используем прокси если настроен
            if self.proxies:
                response = requests.post(url, json=payload, timeout=30, proxies=self.proxies)
            else:
                response = requests.post(url, json=payload, timeout=30)
            
            return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram канал {chat_id}: {e}")
            return False

    def send_signal_alert(self, signal: dict, is_cancellation: bool = False):
        """Отправка сигнала или отмены"""
        emoji = "🟢" if signal['signal'] == "BULLISH" else "🔴" if signal['signal'] == "BEARISH" else "🟡"
        
        if is_cancellation:
            base_message = f"""
🚫 *CANCELLATION* 🚫

*Asset:* {signal['symbol']}
*Previous Signal:* {signal['signal']}
*Price:* ${signal['price']:.2f}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            base_message = f"""
{emoji} *{signal['signal']} SIGNAL* {emoji}

*Asset:* {signal['symbol']}
*Price:* ${signal['price']:.2f}
*Confidence:* {signal['confidence']:.1%}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Админ канал - все сигналы и отмены
        if self.admin_chat_id:
            admin_message = f"👑 ADMIN {base_message}"
            self.send_telegram_to_channel(self.admin_chat_id, admin_message)
        
        # VIP канал - только сильные сигналы (не отмены)
        if self.vip_chat_id and not is_cancellation and signal['confidence'] >= 0.7:
            vip_message = f"💎 VIP {base_message}"
            if signal['confidence'] >= 0.8:
                vip_message += "\n🚨 *HIGH CONFIDENCE* - Consider position"
            self.send_telegram_to_channel(self.vip_chat_id, vip_message)

    def save_signal(self, signal: dict) -> bool:
        """Сохранение сигнала в БД"""
        try:
            conn = sqlite3.connect('data/oi_signals.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals (
                    timestamp, date, asset, signal_type, symbol, 
                    signal_strength, message, spot_price, entry_suggestion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal['timestamp'],
                datetime.now().strftime('%Y-%m-%d'),
                signal['symbol'],
                signal['signal'],
                signal['symbol'],
                signal['confidence'],
                f"Smart signal: {signal['signal']} with {signal['confidence']:.1%} confidence",
                signal['price'],
                f"Monitor {signal['symbol']} for {signal['signal'].lower()} opportunities"
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сигнала: {e}")
            return False

    def check_signal_cancellation(self, symbol: str) -> bool:
        """Проверяем, нужно ли отправить отмену сигнала"""
        last_signal = self.get_last_signal(symbol)
        
        if not last_signal or last_signal['signal_type'] == 'NEUTRAL':
            return False
        
        # Генерируем текущий сигнал
        current_signal = self.generate_combined_signal(symbol)
        
        # Если был сильный сигнал, а сейчас стал нейтральный или слабый - отменяем
        if (last_signal['confidence'] >= self.min_confidence and 
            current_signal['confidence'] < self.min_confidence):
            return True
        
        return False

    def run_analysis(self):
        """Запуск умного анализа"""
        logger.info("🧠 ЗАПУСК УМНОГО ГЕНЕРАТОРА СИГНАЛОВ")
        logger.info(f"📊 Анализируем {len(self.symbols)} активов")
        logger.info("=" * 60)
        
        signals_sent = 0
        cancellations_sent = 0
        
        for symbol in self.symbols:
            logger.info(f"🔍 Анализируем {symbol}...")
            
            # Сначала проверяем отмены
            if self.check_signal_cancellation(symbol):
                last_signal = self.get_last_signal(symbol)
                cancellation_signal = {
                    'symbol': symbol,
                    'signal': last_signal['signal_type'],
                    'confidence': last_signal['confidence'],
                    'price': self.get_spot_price(symbol),
                    'timestamp': int(datetime.now().timestamp())
                }
                
                self.send_signal_alert(cancellation_signal, is_cancellation=True)
                logger.info(f"🚫 {symbol}: Отмена предыдущего сигнала {last_signal['signal_type']}")
                cancellations_sent += 1
            
            # Генерируем новый сигнал
            signal = self.generate_combined_signal(symbol)
            
            # Сохраняем в БД (все сигналы для истории)
            self.save_signal(signal)
            
            # Проверяем, нужно ли отправлять новый сигнал
            if self.should_send_signal(symbol, signal):
                self.send_signal_alert(signal)
                logger.info(f"✅ {symbol}: Отправлен сигнал {signal['signal']} (уверенность: {signal['confidence']:.1%})")
                signals_sent += 1
            else:
                logger.info(f"➡️ {symbol}: {signal['signal']} (уверенность: {signal['confidence']:.1%}) - не отправляем")
        
        logger.info("=" * 60)
        logger.info(f"✅ Анализ завершен. Отправлено: {signals_sent} сигналов, {cancellations_sent} отмен")

def main():
    """Основная функция"""
    Path('logs').mkdir(exist_ok=True)
    
    generator = SmartSignalGenerator()
    generator.run_analysis()

if __name__ == "__main__":
    main()
