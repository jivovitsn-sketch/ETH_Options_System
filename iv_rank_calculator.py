#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IV RANK CALCULATOR - IV Rank и IV Percentile
Показывает где текущая IV относительно исторического диапазона
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IVRankCalculator:
    def __init__(self):
        self.oi_db = './data/unlimited_oi.db'
        self.volatility_dir = './data/volatility/'
        self.output_dir = './data/iv_rank/'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_current_iv(self, asset):
        """Получить текущую IV из последнего файла volatility"""
        try:
            if not os.path.exists(self.volatility_dir):
                return None
            
            # Ищем последний файл с volatility данными
            files = [f for f in os.listdir(self.volatility_dir) if f.endswith('.json')]
            if not files:
                return None
            
            latest_file = max(files)
            with open(os.path.join(self.volatility_dir, latest_file), 'r') as f:
                data = json.load(f)
            
            # Ищем данные по активу
            for item in data.get('assets', []):
                if item.get('asset') == asset:
                    return item.get('realized_vol')
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения текущей IV для {asset}: {e}")
            return None
    
    def get_historical_iv(self, asset, days=252):
        """Получить историческую IV за период"""
        try:
            history = []
            
            # Читаем все файлы volatility за период
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            if not os.path.exists(self.volatility_dir):
                return []
            
            files = [f for f in os.listdir(self.volatility_dir) 
                    if f.endswith('.json') and f.split('_')[1] >= cutoff_date]
            
            for file in files:
                try:
                    with open(os.path.join(self.volatility_dir, file), 'r') as f:
                        data = json.load(f)
                    
                    for item in data.get('assets', []):
                        if item.get('asset') == asset:
                            iv = item.get('realized_vol')
                            if iv:
                                history.append(iv)
                except:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"Ошибка получения истории IV для {asset}: {e}")
            return []
    
    def calculate_iv_rank(self, asset):
        """Рассчитать IV Rank и IV Percentile"""
        try:
            # Получаем текущую IV
            current_iv = self.get_current_iv(asset)
            if current_iv is None:
                logger.warning(f"⚠️ {asset}: Нет текущей IV")
                return None
            
            # Получаем историю
            history_52w = self.get_historical_iv(asset, days=252)  # 52 недели
            history_30d = self.get_historical_iv(asset, days=30)   # 30 дней
            
            if not history_52w:
                logger.warning(f"⚠️ {asset}: Нет истории IV")
                return None
            
            # Рассчитываем IV Rank (52 недели)
            iv_min = min(history_52w)
            iv_max = max(history_52w)
            
            if iv_max == iv_min:
                iv_rank = 50
            else:
                iv_rank = ((current_iv - iv_min) / (iv_max - iv_min)) * 100
            
            # Рассчитываем IV Percentile (52 недели)
            below_current = len([iv for iv in history_52w if iv < current_iv])
            iv_percentile = (below_current / len(history_52w)) * 100
            
            # Средняя IV за 30 дней
            avg_iv_30d = sum(history_30d) / len(history_30d) if history_30d else current_iv
            
            result = {
                'asset': asset,
                'timestamp': datetime.now().isoformat(),
                'current_iv': round(current_iv, 2),
                'iv_rank_52w': round(iv_rank, 1),
                'iv_percentile_52w': round(iv_percentile, 1),
                'iv_min_52w': round(iv_min, 2),
                'iv_max_52w': round(iv_max, 2),
                'avg_iv_30d': round(avg_iv_30d, 2),
                'interpretation': self._interpret_iv_rank(iv_rank, iv_percentile)
            }
            
            # Сохраняем
            self._save_result(asset, result)
            
            logger.info(f"✅ {asset}: IV={current_iv:.2f}, Rank={iv_rank:.1f}%, Percentile={iv_percentile:.1f}% ({result['interpretation']})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчёта IV Rank для {asset}: {e}")
            return None
    
    def _interpret_iv_rank(self, iv_rank, iv_percentile):
        """Интерпретация IV Rank"""
        # IV Rank > 50 = высокая волатильность (выгодно продавать опционы)
        # IV Rank < 50 = низкая волатильность (выгодно покупать опционы)
        
        if iv_rank > 75:
            return "VERY_HIGH"  # Отличное время для продажи опционов
        elif iv_rank > 50:
            return "HIGH"       # Хорошее время для продажи
        elif iv_rank < 25:
            return "VERY_LOW"   # Отличное время для покупки опционов
        elif iv_rank < 50:
            return "LOW"        # Хорошее время для покупки
        else:
            return "NEUTRAL"
    
    def _save_result(self, asset, result):
        """Сохранить результат"""
        try:
            filename = f"{asset}_ivrank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            logger.error(f"Ошибка сохранения IV Rank: {e}")
    
    def calculate_all(self):
        """Рассчитать IV Rank для всех активов"""
        assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        results = {}
        
        logger.info("=" * 60)
        logger.info("📊 IV RANK CALCULATOR")
        logger.info("=" * 60)
        
        for asset in assets:
            result = self.calculate_iv_rank(asset)
            if result:
                results[asset] = result
        
        logger.info("=" * 60)
        logger.info(f"✅ Обработано активов: {len(results)}")
        logger.info("=" * 60)
        
        return results


if __name__ == '__main__':
    calc = IVRankCalculator()
    calc.calculate_all()
