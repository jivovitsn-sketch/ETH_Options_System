#!/usr/bin/env python3
"""
ADVANCED SIGNALS GENERATOR - ПОДДЕРЖИВАЕТ 3 ТЕЛЕГРАМ КАНАЛА
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
import requests
import json
import os
from datetime import datetime
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
        logging.FileHandler('logs/signals_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedSignalGenerator:
    def __init__(self):
        self.symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        
        # Telegram настройки
        self.telegram_bot_token = env_vars.get('TELEGRAM_BOT_TOKEN', '')
        self.admin_chat_id = env_vars.get('TELEGRAM_ADMIN_CHAT_ID', '')
        self.free_chat_id = env_vars.get('TELEGRAM_FREE_CHAT_ID', '')
        self.vip_chat_id = env_vars.get('TELEGRAM_VIP_CHAT_ID', '')
        
        logger.info(f"🔧 Настроены каналы: Admin={bool(self.admin_chat_id)}, Free={bool(self.free_chat_id)}, VIP={bool(self.vip_chat_id)}")
        
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
                return {"signal": "NO_DATA", "confidence": 0.0}
            
            # Группируем по timestamp и считаем общий OI
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            oi_by_time = df.groupby('timestamp')['open_interest'].sum().reset_index()
            oi_by_time = oi_by_time.sort_values('timestamp')
            
            if len(oi_by_time) < 5:
                return {"signal": "INSUFFICIENT_DATA", "confidence": 0.0}
            
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
                return {"signal": "BULLISH", "confidence": min(0.8, oi_trend), "oi_trend": oi_trend}
            elif oi_trend < -0.1 and call_put_ratio < 0.4:
                return {"signal": "BEARISH", "confidence": min(0.8, abs(oi_trend)), "oi_trend": oi_trend}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.4, "oi_trend": oi_trend}
                
        except Exception as e:
            logger.error(f"Ошибка анализа OI {symbol}: {e}")
            return {"signal": "ERROR", "confidence": 0.0}

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
                return {"signal": "NO_DATA", "confidence": 0.0}
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
            
            # Анализ тренда за разные периоды
            short_trend = (df['last_price'].iloc[-1] - df['last_price'].iloc[-5]) / df['last_price'].iloc[-5]
            medium_trend = (df['last_price'].iloc[-1] - df['last_price'].iloc[-20]) / df['last_price'].iloc[-20]
            
            # Комбинированный сигнал
            if short_trend > 0.02 and medium_trend > 0.05:
                return {"signal": "BULLISH", "confidence": min(0.8, (short_trend + medium_trend)/2), "trend": (short_trend + medium_trend)/2}
            elif short_trend < -0.02 and medium_trend < -0.05:
                return {"signal": "BEARISH", "confidence": min(0.8, abs(short_trend + medium_trend)/2), "trend": (short_trend + medium_trend)/2}
            else:
                return {"signal": "NEUTRAL", "confidence": 0.4, "trend": (short_trend + medium_trend)/2}
                
        except Exception as e:
            logger.error(f"Ошибка анализа цены {symbol}: {e}")
            return {"signal": "ERROR", "confidence": 0.0}

    def generate_combined_signal(self, symbol: str) -> dict:
        """Генерация комбинированного сигнала"""
        try:
            current_price = self.get_spot_price(symbol)
            if current_price == 0:
                return {"symbol": symbol, "signal": "NO_DATA", "confidence": 0.0}
            
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
            if bullish_score > bearish_score + 0.15:
                final_signal = "BULLISH"
                final_confidence = min(0.9, bullish_score)
            elif bearish_score > bullish_score + 0.15:
                final_signal = "BEARISH"
                final_confidence = min(0.9, bearish_score)
            else:
                final_signal = "NEUTRAL"
                final_confidence = 0.5
            
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
            return {"symbol": symbol, "signal": "ERROR", "confidence": 0.0}

    def send_telegram_to_channel(self, chat_id: str, message: str) -> bool:
        """Отправка сообщения в конкретный Telegram канал"""
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
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram канал {chat_id}: {e}")
            return False

    def distribute_signal(self, signal: dict):
        """Распределение сигналов по каналам в зависимости от уверенности"""
        emoji = "🟢" if signal['signal'] == "BULLISH" else "🔴" if signal['signal'] == "BEARISH" else "🟡"
        
        base_message = f"""
{emoji} *{signal['signal']} SIGNAL* {emoji}

*Asset:* {signal['symbol']}
*Price:* ${signal['price']:.2f}
*Confidence:* {signal['confidence']:.1%}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Админ канал - все сигналы
        if self.admin_chat_id:
            admin_message = f"👑 ADMIN {base_message}"
            self.send_telegram_to_channel(self.admin_chat_id, admin_message)
        
        # Free канал - только уверенные сигналы
        if self.free_chat_id and signal['confidence'] >= 0.7:
            free_message = f"🎯 FREE {base_message}"
            self.send_telegram_to_channel(self.free_chat_id, free_message)
        
        # VIP канал - все сигналы кроме нейтральных
        if self.vip_chat_id and signal['signal'] != "NEUTRAL" and signal['confidence'] >= 0.6:
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
                f"Combined signal: {signal['signal']} with {signal['confidence']:.1%} confidence",
                signal['price'],
                f"Monitor {signal['symbol']} for {signal['signal'].lower()} opportunities"
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сигнала: {e}")
            return False

    def run_analysis(self):
        """Запуск полного анализа"""
        logger.info("🚀 ЗАПУСК ADVANCED SIGNALS GENERATOR")
        logger.info(f"📊 Анализируем {len(self.symbols)} активов")
        logger.info("=" * 60)
        
        strong_signals = 0
        
        for symbol in self.symbols:
            logger.info(f"🔍 Анализируем {symbol}...")
            
            signal = self.generate_combined_signal(symbol)
            if signal and signal['signal'] not in ['NO_DATA', 'ERROR']:
                # Сохраняем в БД
                if self.save_signal(signal):
                    # Отправляем в соответствующие каналы
                    self.distribute_signal(signal)
                    
                    # Логируем результат
                    status_emoji = "✅" if signal['confidence'] >= 0.7 else "⚠️"
                    logger.info(f"{status_emoji} {symbol}: {signal['signal']} (confidence: {signal['confidence']:.1%}, price: ${signal['price']:.2f})")
                    
                    if signal['confidence'] >= 0.7:
                        strong_signals += 1
                else:
                    logger.error(f"❌ {symbol}: Не удалось сохранить сигнал в БД")
            else:
                logger.warning(f"❌ {symbol}: Не удалось сгенерировать сигнал")
        
        logger.info("=" * 60)
        logger.info(f"✅ Анализ завершен. Сильных сигналов: {strong_signals}/{len(self.symbols)}")
        
        # Отправляем итоговый отчет в админ канал
        if self.admin_chat_id and strong_signals > 0:
            report = f"📊 *ANALYSIS REPORT*\n\nСильных сигналов: {strong_signals}/{len(self.symbols)}\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.send_telegram_to_channel(self.admin_chat_id, report)

def main():
    """Основная функция"""
    Path('logs').mkdir(exist_ok=True)
    
    generator = AdvancedSignalGenerator()
    generator.run_analysis()

if __name__ == "__main__":
    main()
