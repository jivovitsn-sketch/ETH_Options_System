#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADVANCED SIGNALS GENERATOR - С РЕАЛЬНЫМ АНАЛИЗОМ ДАННЫХ
НЕ СПАМИТ В TELEGRAM!
"""

from data_integration import *
from data_integration import get_pcr_data, get_vanna_data, get_iv_rank_data
import sqlite3
import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from option_pricing import OptionPricing, OptionPositionManager, generate_option_strategies, format_option_signal_message

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/smart_signals.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self):
        self.db_path = './data/oi_signals.db'
        self.oi_db_path = './data/unlimited_oi.db'
        self.last_signals = {}  # Кэш последних сигналов
        self._init_database()
        self._load_last_signals()
    
    def _init_database(self):
        """Инициализация БД для сигналов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                date TEXT,
                asset TEXT,
                signal_type TEXT,
                symbol TEXT,
                strike REAL,
                option_type TEXT,
                signal_strength REAL,
                message TEXT,
                spot_price REAL,
                entry_suggestion TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _load_last_signals(self):
        """Загрузить последние отправленные сигналы"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT asset, signal_type, signal_strength, timestamp
                FROM signals
                WHERE timestamp > ?
                GROUP BY asset
                HAVING timestamp = MAX(timestamp)
            """, (int((datetime.now() - timedelta(hours=2)).timestamp()),))
            
            for asset, signal_type, strength, ts in cursor.fetchall():
                self.last_signals[asset] = {
                    'signal_type': signal_type,
                    'strength': strength,
                    'timestamp': ts
                }
            conn.close()
            logger.info(f"Загружено {len(self.last_signals)} последних сигналов")
        except Exception as e:
            logger.error(f"Ошибка загрузки последних сигналов: {e}")
    
    def should_send_signal(self, asset, new_signal_type, new_confidence):
        """
        УМНАЯ ЛОГИКА: отправлять только если:
        1. Изменился тип сигнала (BULLISH→BEARISH)
        2. Изменилась confidence на 10%+
        3. Прошло больше 1 часа с последней отправки
        """
        if asset not in self.last_signals:
            return True  # Первый сигнал - отправляем
        
        last = self.last_signals[asset]
        
        # Проверка времени
        time_diff = time.time() - last['timestamp']
        if time_diff < 3600:  # Меньше часа
            logger.info(f"⏰ {asset}: Прошло только {time_diff/60:.1f} мин с последней отправки")
            return False
        
        # Проверка изменения типа сигнала
        if last['signal_type'] != new_signal_type:
            logger.info(f"🔄 {asset}: Изменился сигнал {last['signal_type']}→{new_signal_type}")
            return True
        
        # Проверка изменения confidence
        confidence_diff = abs(new_confidence - last['strength'])
        if confidence_diff >= 0.10:  # 10%+ изменение
            logger.info(f"📊 {asset}: Изменилась confidence на {confidence_diff*100:.1f}%")
            return True
        
        logger.info(f"⏭️ {asset}: Нет значительных изменений, не отправляем")
        return False
    
    def analyze_oi_volume(self, asset):
        """РЕАЛЬНЫЙ анализ с использованием ВСЕХ данных + НОВЫЕ ИНДИКАТОРЫ"""
        try:
            # 1. Получаем все данные
            futures = get_futures_data(asset)
            liquidations = get_recent_liquidations(asset, hours=4)
            gamma = get_gamma_exposure(asset)
            max_pain_data = get_max_pain(asset)
            oi_trend = self._get_oi_trend(asset)
            
            # НОВЫЕ ИНДИКАТОРЫ
            pcr_data = get_pcr_data(asset)
            vanna_data = get_vanna_data(asset)
            iv_rank_data = get_iv_rank_data(asset)
            
            # Базовые значения
            confidence = 0.5
            signal = 'NEUTRAL'
            reasons = []
            
            # 2. АНАЛИЗ ЛИКВИДАЦИЙ (вес 15%)
            if liquidations and liquidations['total_count'] > 10:
                ratio = liquidations['ratio']
                if ratio > 2.0:
                    signal = 'BEARISH'
                    confidence += 0.12
                    reasons.append(f"Liq ratio {ratio:.2f} (больше лонгов)")
                elif ratio < 0.5:
                    signal = 'BULLISH'
                    confidence += 0.12
                    reasons.append(f"Liq ratio {ratio:.2f} (больше шортов)")
            
            # 3. АНАЛИЗ GAMMA EXPOSURE (вес 15%)
            if gamma and gamma.get('total_gex') and gamma.get('zero_gamma_level'):
                spot = gamma.get('spot_price', 0)
                zero_gamma = gamma.get('zero_gamma_level', 0)
                
                if spot > 0 and zero_gamma > 0:
                    distance = (spot - zero_gamma) / zero_gamma * 100
                    
                    if distance > 2:
                        confidence += 0.10
                        reasons.append(f"GEX: выше zero gamma на {distance:.1f}%")
                        if signal == 'NEUTRAL':
                            signal = 'BULLISH'
                    elif distance < -2:
                        confidence += 0.10
                        reasons.append(f"GEX: ниже zero gamma на {abs(distance):.1f}%")
                        if signal == 'NEUTRAL':
                            signal = 'BEARISH'
            
            # 4. АНАЛИЗ MAX PAIN (вес 12%)
            if max_pain_data and max_pain_data.get('distance_pct') is not None:
                distance = max_pain_data['distance_pct']
                pcr = max_pain_data.get('put_call_ratio', 1.0)
                
                if abs(distance) > 3:
                    confidence += 0.08
                    if distance > 0:
                        reasons.append(f"Max Pain: выше на {distance:.1f}%")
                    else:
                        reasons.append(f"Max Pain: ниже на {abs(distance):.1f}%")
                
                if pcr > 1.5:
                    if signal == 'NEUTRAL':
                        signal = 'BULLISH'
                    confidence += 0.06
                    reasons.append(f"PCR {pcr:.2f} (путов больше)")
                elif pcr < 0.7:
                    if signal == 'NEUTRAL':
                        signal = 'BEARISH'
                    confidence += 0.06
                    reasons.append(f"PCR {pcr:.2f} (коллов больше)")
            
            # 5. АНАЛИЗ OI ТРЕНДА (вес 15%)
            if oi_trend:
                oi_change = oi_trend.get('change_pct', 0)
                volume = oi_trend.get('recent_volume', 0)
                
                if volume > 1000:
                    if oi_change > 10:
                        confidence += 0.10
                        reasons.append(f"OI рост {oi_change:.1f}%")
                        if signal == 'NEUTRAL':
                            signal = 'BULLISH'
                    elif oi_change < -10:
                        confidence += 0.10
                        reasons.append(f"OI падение {oi_change:.1f}%")
                        if signal == 'NEUTRAL':
                            signal = 'BEARISH'
            
            # 6. АНАЛИЗ FUNDING RATE (вес 8%)
            if futures and futures.get('funding_rate'):
                fr = futures['funding_rate']
                if abs(fr) > 0.01:
                    confidence += 0.06
                    if fr > 0.01:
                        reasons.append(f"Funding {fr*100:.3f}% (лонги перегреты)")
                        if signal != 'BULLISH':
                            signal = 'BEARISH'
                    elif fr < -0.01:
                        reasons.append(f"Funding {fr*100:.3f}% (шорты перегреты)")
                        if signal != 'BEARISH':
                            signal = 'BULLISH'
            
            # 7. 🆕 АНАЛИЗ PCR RSI (вес 12%)
            if pcr_data and pcr_data.get('pcr_rsi') is not None:
                pcr_rsi = pcr_data['pcr_rsi']
                pcr_interp = pcr_data.get('interpretation', 'NEUTRAL')
                
                if pcr_interp == 'BEARISH_EXTREME':
                    confidence += 0.10
                    if signal == 'NEUTRAL':
                        signal = 'BULLISH'  # Много путов = bullish contrarian
                    reasons.append(f"PCR RSI {pcr_rsi:.0f} (крайне медвежий = разворот)")
                elif pcr_interp == 'BULLISH_EXTREME':
                    confidence += 0.10
                    if signal == 'NEUTRAL':
                        signal = 'BEARISH'  # Много коллов = bearish contrarian
                    reasons.append(f"PCR RSI {pcr_rsi:.0f} (крайне бычий = разворот)")
                elif pcr_interp in ['BEARISH', 'BULLISH']:
                    confidence += 0.06
                    reasons.append(f"PCR RSI {pcr_rsi:.0f} ({pcr_interp.lower()})")
            
            # 8. 🆕 АНАЛИЗ VANNA EXPOSURE (вес 10%)
            if vanna_data and vanna_data.get('total_vanna') is not None:
                vanna = vanna_data['total_vanna']
                vanna_interp = vanna_data.get('interpretation', 'NEUTRAL')
                
                if vanna_interp in ['BULLISH_STRONG', 'BEARISH_STRONG']:
                    confidence += 0.08
                    if 'BULLISH' in vanna_interp and signal != 'BEARISH':
                        signal = 'BULLISH'
                    elif 'BEARISH' in vanna_interp and signal != 'BULLISH':
                        signal = 'BEARISH'
                    reasons.append(f"Vanna {abs(vanna):.0f} ({vanna_interp})")
                elif vanna_interp in ['BULLISH', 'BEARISH']:
                    confidence += 0.05
                    reasons.append(f"Vanna {abs(vanna):.0f} ({vanna_interp})")
            
            # 9. 🆕 АНАЛИЗ IV RANK (вес 8%)
            if iv_rank_data and iv_rank_data.get('iv_rank') is not None:
                iv_rank = iv_rank_data['iv_rank']
                iv_interp = iv_rank_data.get('interpretation', 'NEUTRAL')
                
                # IV Rank > 75 = хорошо для продажи опционов (нейтрально для направления)
                # IV Rank < 25 = хорошо для покупки опционов
                if iv_rank > 75:
                    confidence += 0.06
                    reasons.append(f"IV Rank {iv_rank:.0f}% (высокая IV)")
                elif iv_rank < 25:
                    confidence += 0.06
                    reasons.append(f"IV Rank {iv_rank:.0f}% (низкая IV)")
            
            # 10. ФИНАЛЬНАЯ НОРМАЛИЗАЦИЯ
            confidence = min(confidence, 0.95)
            confidence = max(confidence, 0.30)
            
            # Если нашли мало данных - снижаем confidence
            if len(reasons) < 3:
                confidence = max(confidence * 0.7, 0.30)
                reasons.append("Недостаточно данных для высокой confidence")
            
            logger.info(f"📊 {asset}: {signal} {int(confidence*100)}% | Причины: {', '.join(reasons)}")
            
            return signal, confidence
            
        except Exception as e:
            logger.error(f"Ошибка анализа {asset}: {e}")
            return 'NEUTRAL', 0.30

    def _get_oi_trend(self, asset):
        """Анализ тренда OI из unlimited_oi.db"""
        try:
            conn = sqlite3.connect(self.oi_db_path)
            cursor = conn.cursor()
            
            # Получаем OI за последние 4 часа
            since_ts = int((datetime.now() - timedelta(hours=4)).timestamp())
            cursor.execute("""
                SELECT timestamp, SUM(open_interest) as total_oi, COUNT(*) as count
                FROM all_positions_tracking
                WHERE asset = ? AND timestamp > ?
                GROUP BY CAST(timestamp/3600 AS INT)
                ORDER BY timestamp DESC
                LIMIT 4
            """, (asset, since_ts))
            
            data = cursor.fetchall()
            conn.close()
            
            if len(data) < 2:
                return None
            
            # Рассчитываем изменение
            latest_oi = data[0][1]
            oldest_oi = data[-1][1]
            change_pct = (latest_oi - oldest_oi) / oldest_oi * 100 if oldest_oi > 0 else 0
            
            total_volume = sum([row[2] for row in data])
            
            return {
                'change_pct': change_pct,
                'recent_volume': total_volume,
                'latest_oi': latest_oi
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа OI тренда {asset}: {e}")
            return None
    
    def save_signal(self, asset, signal_type, confidence, spot_price, strategies=None):
        """Сохранить сигнал в БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = int(time.time())
            date = datetime.now().strftime('%Y-%m-%d')
            
            if strategies and len(strategies) > 0:
                strategy = strategies[0]
                cursor.execute('''
                    INSERT INTO signals 
                    (timestamp, date, asset, signal_type, symbol, strike, option_type, 
                     signal_strength, message, spot_price, entry_suggestion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, date, asset, signal_type,
                    strategy.get('symbol', ''),
                    strategy.get('strike', 0),
                    strategy.get('type', ''),
                    confidence,
                    f"{signal_type} signal for {asset}",
                    spot_price,
                    strategy.get('entry_suggestion', '')
                ))
            else:
                cursor.execute('''
                    INSERT INTO signals 
                    (timestamp, date, asset, signal_type, signal_strength, spot_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (timestamp, date, asset, signal_type, confidence, spot_price))
            
            conn.commit()
            conn.close()
            
            # Обновляем кэш
            self.last_signals[asset] = {
                'signal_type': signal_type,
                'strength': confidence,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сигнала {asset}: {e}")
    
    def send_telegram_message(self, message, is_vip=False):
        """Отправка сообщения в Telegram"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID' if is_vip else 'TELEGRAM_ADMIN_CHAT_ID')
            proxy_url = os.getenv('TELEGRAM_PROXY_URL')
            proxy_user = os.getenv('TELEGRAM_PROXY_USERNAME')
            proxy_pass = os.getenv('TELEGRAM_PROXY_PASSWORD')
            
            if not bot_token or not chat_id:
                logger.warning("❌ Telegram credentials not set")
                return
            
            proxies = None
            if proxy_url:
                if proxy_user and proxy_pass:
                    proxy_with_auth = f"http://{proxy_user}:{proxy_pass}@{proxy_url.split('//')[1]}"
                else:
                    proxy_with_auth = proxy_url
                proxies = {'http': proxy_with_auth, 'https': proxy_with_auth}
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, proxies=proxies, timeout=20)
            if response.status_code == 200:
                logger.info("✅ Сообщение отправлено в Telegram")
            else:
                logger.error(f"❌ Ошибка Telegram: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в Telegram: {e}")
    
    def run(self):
        """Главный цикл анализа"""
        logger.info("=" * 60)
        logger.info(f"🚀 ЗАПУСК АНАЛИЗА: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        sent_count = 0
        skipped_count = 0
        
        for asset in assets:
            logger.info(f"\n🔍 Анализируем {asset}...")
            
            try:
                # Анализ
                signal_type, confidence = self.analyze_oi_volume(asset)
                
                # Проверка минимальной confidence
                if confidence < 0.70:
                    logger.info(f"📊 {asset}: Слишком низкая уверенность {confidence*100:.1f}%")
                    logger.info(f"➡️ {asset}: {signal_type} (уверенность: {confidence*100:.1f}%) - не отправляем")
                    skipped_count += 1
                    continue
                
                # Проверка нужно ли отправлять
                if not self.should_send_signal(asset, signal_type, confidence):
                    logger.info(f"➡️ {asset}: {signal_type} (уверенность: {confidence*100:.1f}%) - уже отправляли недавно")
                    skipped_count += 1
                    continue
                
                # Получаем spot price
                futures = get_futures_data(asset)
                spot_price = futures['price'] if futures else 0
                
                # Генерируем опционные стратегии
                strategies = generate_option_strategies(asset, signal_type, spot_price, confidence)
                
                # Сохраняем сигнал
                self.save_signal(asset, signal_type, confidence, spot_price, strategies)
                
                # Формируем и отправляем сообщение
                message = format_option_signal_message(asset, signal_type, confidence, spot_price, strategies)
                self.send_telegram_message(message, is_vip=True)
                
                logger.info(f"✅ {asset}: Отправлен {signal_type} сигнал (уверенность: {confidence*100:.1f}%)")
                sent_count += 1
                
                time.sleep(2)  # Задержка между отправками
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки {asset}: {e}")
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ Анализ завершен. Отправлено: {sent_count} сигналов, пропущено: {skipped_count}")
        logger.info("=" * 60)


if __name__ == '__main__':
    generator = SignalGenerator()
    generator.run()
