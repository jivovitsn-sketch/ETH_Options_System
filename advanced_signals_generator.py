from data_integration import *
from asset_config import get_min_confidence, get_min_interval
from data_integration import *
from asset_config import get_min_confidence, get_min_interval
import sqlite3
import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from option_pricing import OptionPricing, OptionPositionManager, generate_option_strategies, format_option_signal_message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/smart_signals.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

load_dotenv()

class SignalGenerator:
    def __init__(self):
        self.db_path = 'data/oi_signals.db'
        self.assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        self.min_confidence = 0.7
        self.min_interval_minutes = 15
        
    def get_last_signal_time(self, asset):
        """Получить время последнего сигнала для актива"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp FROM signals 
            WHERE asset = ? AND signal_type != 'NEUTRAL'
            ORDER BY timestamp DESC LIMIT 1
        ''', (asset,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def should_send_signal(self, asset, new_signal_type, new_confidence):
        """Проверить, нужно ли отправлять сигнал"""
        last_time = self.get_last_signal_time(asset)
        current_time = int(time.time())
        time_diff_minutes = (current_time - last_time) / 60
        
        # Проверка временного интервала
        if time_diff_minutes < self.min_interval_minutes:
            logger.info(f"⏰ {asset}: Пропускаем - прошло всего {time_diff_minutes:.1f} мин")
            return False
        
        # Проверка уверенности
        if new_confidence < self.min_confidence:
            logger.info(f"📊 {asset}: Слишком низкая уверенность {new_confidence:.1%}")
            return False
            
        return True
    
    def analyze_oi_volume(self, asset):
        """Анализ OI и Volume (упрощенная версия)"""
        # В реальной системе здесь будет анализ данных из БД
        # Сейчас используем тестовые данные
        
        if asset == 'BTC':
            return 'BULLISH', 0.82
        elif asset == 'ETH':
            return 'BEARISH', 0.78
        else:
            return 'NEUTRAL', 0.3
    
    
    def send_telegram_message(self, message, is_vip=False):
        """Отправка сообщения в Telegram с использованием прокси"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_VIP_CHAT_ID' if is_vip else 'TELEGRAM_ADMIN_CHAT_ID')
            proxy_url = os.getenv('TELEGRAM_PROXY_URL')
            proxy_user = os.getenv('TELEGRAM_PROXY_USERNAME')
            proxy_pass = os.getenv('TELEGRAM_PROXY_PASSWORD')
            
            if not bot_token or not chat_id:
                logger.warning("❌ Telegram credentials not set")
                return
            
            # Настраиваем прокси
            proxies = None
            if proxy_url:
                if proxy_user and proxy_pass:
                    proxy_with_auth = f"http://{proxy_user}:{proxy_pass}@{proxy_url.split('//')[1]}"
                else:
                    proxy_with_auth = proxy_url
                proxies = {
                    'http': proxy_with_auth,
                    'https': proxy_with_auth
                }
                logger.info(f"🔗 Using proxy: {proxy_url}")
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            # Увеличиваем таймаут и пробуем с прокси
            response = requests.post(url, json=payload, proxies=proxies, timeout=20)
            if response.status_code == 200:
                logger.info("✅ Сообщение отправлено в Telegram")
            else:
                logger.error(f"❌ Ошибка отправки в Telegram: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка Telegram: {e}")
            # Пробуем без прокси как fallback
            try:
                if proxies:
                    logger.info("🔄 Пробуем без прокси...")
                    response = requests.post(url, json=payload, timeout=20)
                    if response.status_code == 200:
                        logger.info("✅ Сообщение отправлено без прокси")
                    else:
                        logger.error(f"❌ Ошибка без прокси: {response.text}")
            except Exception as e2:
                logger.error(f"❌ Ошибка при fallback: {e2}")

    
    def save_signal_to_db(self, asset, signal_type, confidence, spot_price, message):
        """Сохранение сигнала в БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals 
                (timestamp, date, asset, signal_type, symbol, signal_strength, message, spot_price, entry_suggestion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(time.time()),
                datetime.now().strftime('%Y-%m-%d'),
                asset,
                signal_type,
                asset + '-USD',
                confidence,
                message,
                spot_price,
                'Options strategies generated'
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"💾 Сигнал сохранен в БД: {asset} {signal_type}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в БД: {e}")
    
    def manage_option_positions(self, asset, signal_type, confidence):
        """Управление опционными позициями на основе сигнала"""
        try:
            position_manager = OptionPositionManager()
            active_positions = position_manager.get_active_positions(asset)
            actions = []
            
            for position in active_positions:
                # Исправляем распаковку - берем только нужные поля по индексам
                pos_id = position[0]
                pos_asset = position[1]
                pos_strategy = position[2]
                pos_type = position[3]
                strike = position[4]
                entry_prem = position[6]
                pnl = position[17]
                
                # Логика управления на основе нового сигнала
                if signal_type == "NEUTRAL":
                    if float(pnl) > 0.3 * float(entry_prem):  # 30% прибыли
                        actions.append("CLOSE {} @ {} - Take profit 30%".format(pos_type, strike))
                    elif float(pnl) < -0.5 * float(entry_prem):  # -50% убыток
                        actions.append("CLOSE {} @ {} - Stop loss 50%".format(pos_type, strike))
                
                elif signal_type == "BEARISH" and pos_type == "CALL":
                    if confidence > 0.7:
                        actions.append("CLOSE CALL @ {} - Signal reversal".format(strike))
                    else:
                        actions.append("HEDGE PUT for CALL @ {}".format(strike))
                        
                elif signal_type == "BULLISH" and pos_type == "PUT":
                    if confidence > 0.7:
                        actions.append("CLOSE PUT @ {} - Signal reversal".format(strike)) 
                    else:
                        actions.append("HEDGE CALL for PUT @ {}".format(strike))
            
            return actions
        except Exception as e:
            logger.error(f"❌ Ошибка управления позициями: {e}")
            return []
    
    def process_asset(self, asset):
        """Обработка одного актива"""
        logger.info("🔍 Анализируем {}...".format(asset))
        
        # Получаем текущую цену (в реальной системе - из API)
        spot_prices = {'BTC': 112500, 'ETH': 4000, 'SOL': 145, 'XRP': 0.6, 'DOGE': 0.15, 'MNT': 0.8}
        spot_price = spot_prices.get(asset, 1000)
        
        # Анализ OI и Volume
        signal_type, confidence = self.analyze_oi_volume(asset)
        
        # Проверяем нужно ли отправлять сигнал
        if not self.should_send_signal(asset, signal_type, confidence):
            logger.info("➡️ {}: {} (уверенность: {:.1%}) - не отправляем".format(asset, signal_type, confidence))
            return False
        
        # Генерация опционных стратегий для сильных сигналов
        if signal_type in ['BULLISH', 'BEARISH'] and confidence >= self.min_confidence:
            try:
                strategies = generate_option_strategies(asset, signal_type, spot_price, confidence)
                
                # Управление позициями
                position_actions = self.manage_option_positions(asset, signal_type, confidence)
                
                # Форматирование сообщения
                message = format_option_signal_message(asset, signal_type, confidence, spot_price, strategies)
                
                # Добавляем информацию о действиях с позициями
                if position_actions:
                    message += "\n\n🔄 **ДЕЙСТВИЯ С ПОЗИЦИЯМИ:**\n"
                    for action in position_actions:
                        message += "• {}\n".format(action)
                
                # Отправка в Telegram
                self.send_telegram_message(message, is_vip=True)
                
                # Сохранение в БД
                self.save_signal_to_db(asset, signal_type, confidence, spot_price, message)
                
                logger.info("✅ {}: {} сигнал отправлен (уверенность: {:.1%})".format(asset, signal_type, confidence))
                return True
            except Exception as e:
                logger.error("❌ Ошибка генерации стратегий для {}: {}".format(asset, e))
                return False
        
        return False
    
    def run_analysis(self):
        """Запуск анализа всех активов"""
        logger.info("🧠 ЗАПУСК УМНОГО ГЕНЕРАТОРА СИГНАЛОВ")
        logger.info("🔧 Умные сигналы: уверенность ≥{}, таймфрейм {}мин".format(self.min_confidence, self.min_interval_minutes))
        logger.info("📊 Анализируем {} активов".format(len(self.assets)))
        logger.info("=" * 60)
        
        signals_sent = 0
        cancellations = 0
        
        for asset in self.assets:
            try:
                result = self.process_asset(asset)
                if result:
                    signals_sent += 1
            except Exception as e:
                logger.error("❌ Ошибка обработки {}: {}".format(asset, e))
        
        logger.info("=" * 60)
        logger.info("✅ Анализ завершен. Отправлено: {} сигналов, {} отмен".format(signals_sent, cancellations))

if __name__ == "__main__":
    generator = SignalGenerator()
    generator.run_analysis()
