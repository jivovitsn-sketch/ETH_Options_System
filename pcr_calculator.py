#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCR CALCULATOR - Put/Call Ratio с RSI
Анализирует соотношение путов и коллов по OI и объёму
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PCRCalculator:
    def __init__(self):
        self.oi_db = './data/unlimited_oi.db'
        self.output_dir = './data/pcr/'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def calculate_pcr(self, asset):
        """Рассчитать PCR для актива"""
        try:
            conn = sqlite3.connect(self.oi_db)
            cursor = conn.cursor()
            
            # Получаем данные за последние 24 часа
            since_ts = int((datetime.now() - timedelta(hours=24)).timestamp())
            
            cursor.execute("""
                SELECT 
                    option_type,
                    SUM(open_interest) as total_oi,
                    SUM(volume_24h) as total_volume,
                    COUNT(*) as contract_count
                FROM all_positions_tracking
                WHERE asset = ? AND timestamp > ?
                GROUP BY option_type
            """, (asset, since_ts))
            
            data = cursor.fetchall()
            conn.close()
            
            if not data:
                return None
            
            # Разделяем на путы и коллы
            put_oi = 0
            call_oi = 0
            put_volume = 0
            call_volume = 0
            
            for opt_type, oi, vol, count in data:
                if opt_type == 'Put':
                    put_oi = oi
                    put_volume = vol
                elif opt_type == 'Call':
                    call_oi = oi
                    call_volume = vol
            
            # Расчёт PCR
            pcr_oi = put_oi / call_oi if call_oi > 0 else 0
            pcr_volume = put_volume / call_volume if call_volume > 0 else 0
            
            # Получаем историю для RSI
            pcr_history = self._get_pcr_history(asset)
            pcr_rsi = self._calculate_rsi(pcr_history, pcr_oi) if pcr_history else 50
            
            result = {
                'asset': asset,
                'timestamp': datetime.now().isoformat(),
                'pcr_oi': round(pcr_oi, 3),
                'pcr_volume': round(pcr_volume, 3),
                'pcr_rsi': round(pcr_rsi, 1),
                'put_oi': round(put_oi, 2),
                'call_oi': round(call_oi, 2),
                'put_volume': round(put_volume, 2),
                'call_volume': round(call_volume, 2),
                'interpretation': self._interpret_pcr(pcr_oi, pcr_rsi)
            }
            
            # Сохраняем
            self._save_result(asset, result)
            
            logger.info(f"✅ {asset}: PCR={pcr_oi:.3f}, RSI={pcr_rsi:.1f} ({result['interpretation']})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчёта PCR для {asset}: {e}")
            return None
    
    def _get_pcr_history(self, asset):
        """Получить историю PCR за последние 14 дней"""
        try:
            files = [f for f in os.listdir(self.output_dir) if f.startswith(f"{asset}_pcr_")]
            if not files:
                return []
            
            # Берём последние 14 файлов
            files.sort(reverse=True)
            history = []
            
            for file in files[:14]:
                try:
                    with open(os.path.join(self.output_dir, file), 'r') as f:
                        data = json.load(f)
                        history.append(data['pcr_oi'])
                except:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"Ошибка получения истории PCR: {e}")
            return []
    
    def _calculate_rsi(self, history, current_value):
        """Рассчитать RSI для PCR"""
        try:
            if len(history) < 2:
                return 50
            
            # Добавляем текущее значение
            values = history + [current_value]
            
            # Рассчитываем изменения
            changes = [values[i] - values[i-1] for i in range(1, len(values))]
            
            gains = [c if c > 0 else 0 for c in changes]
            losses = [-c if c < 0 else 0 for c in changes]
            
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Ошибка расчёта RSI: {e}")
            return 50
    
    def _interpret_pcr(self, pcr_oi, pcr_rsi):
        """Интерпретация PCR"""
        if pcr_rsi > 70:
            return "BEARISH_EXTREME"  # Слишком много путов
        elif pcr_rsi > 60:
            return "BEARISH"
        elif pcr_rsi < 30:
            return "BULLISH_EXTREME"  # Слишком много коллов
        elif pcr_rsi < 40:
            return "BULLISH"
        else:
            return "NEUTRAL"
    
    def _save_result(self, asset, result):
        """Сохранить результат в JSON"""
        try:
            filename = f"{asset}_pcr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            logger.error(f"Ошибка сохранения PCR: {e}")
    
    def calculate_all(self):
        """Рассчитать PCR для всех активов"""
        assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        results = {}
        
        logger.info("=" * 60)
        logger.info("📊 PCR CALCULATOR")
        logger.info("=" * 60)
        
        for asset in assets:
            result = self.calculate_pcr(asset)
            if result:
                results[asset] = result
        
        logger.info("=" * 60)
        logger.info(f"✅ Обработано активов: {len(results)}")
        logger.info("=" * 60)
        
        return results


if __name__ == '__main__':
    calc = PCRCalculator()
    calc.calculate_all()
