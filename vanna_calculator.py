#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VANNA CALCULATOR - Vanna Exposure
Анализирует чувствительность дельты к изменению IV
"""

import sqlite3
import json
import os
from datetime import datetime
import logging
from scipy.stats import norm
from math import log, sqrt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VannaCalculator:
    def __init__(self):
        self.oi_db = './data/unlimited_oi.db'
        self.output_dir = './data/vanna/'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def calculate_vanna(self, S, K, T, r, sigma):
        """Рассчитать Vanna для одного опциона"""
        try:
            if T <= 0 or sigma <= 0:
                return 0
            
            d1 = (log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*sqrt(T))
            d2 = d1 - sigma*sqrt(T)
            
            vanna = -norm.pdf(d1) * d2 / sigma
            
            return vanna
            
        except Exception as e:
            logger.error(f"Ошибка расчёта Vanna: {e}")
            return 0
    
    def calculate_asset_vanna(self, asset):
        """Рассчитать Vanna Exposure для актива"""
        try:
            conn = sqlite3.connect(self.oi_db)
            cursor = conn.cursor()
            
            # Получаем опционы
            cursor.execute("""
                SELECT 
                    strike, option_type, open_interest, spot_price, dte
                FROM all_positions_tracking
                WHERE asset = ? AND dte > 0
                ORDER BY strike
            """, (asset,))
            
            options = cursor.fetchall()
            conn.close()
            
            if not options:
                logger.warning(f"⚠️ {asset}: Нет данных опционов")
                return None
            
            # Группируем по страйкам
            vanna_by_strike = {}
            total_vanna = 0
            spot_price = options[0][3] if options else 0
            
            # Параметры
            r = 0.02  # risk-free rate
            sigma = 0.65  # assumed IV
            
            for strike, opt_type, oi, spot, dte in options:
                T = dte / 365.0
                
                # Рассчитываем Vanna
                vanna = self.calculate_vanna(spot, strike, T, r, sigma)
                
                # Умножаем на OI (с учётом знака для путов)
                multiplier = 1 if opt_type == 'Call' else -1
                vanna_exposure = vanna * oi * multiplier
                
                # Группируем
                if strike not in vanna_by_strike:
                    vanna_by_strike[strike] = 0
                
                vanna_by_strike[strike] += vanna_exposure
                total_vanna += vanna_exposure
            
            # Находим ключевые уровни
            sorted_strikes = sorted(vanna_by_strike.items(), key=lambda x: abs(x[1]), reverse=True)
            top_strikes = sorted_strikes[:5]
            
            result = {
                'asset': asset,
                'timestamp': datetime.now().isoformat(),
                'spot_price': round(spot_price, 2),
                'total_vanna': round(total_vanna, 2),
                'vanna_by_strike': {str(k): round(v, 2) for k, v in vanna_by_strike.items()},
                'top_vanna_strikes': [(round(k, 2), round(v, 2)) for k, v in top_strikes],
                'interpretation': self._interpret_vanna(total_vanna, spot_price, top_strikes)
            }
            
            # Сохраняем
            self._save_result(asset, result)
            
            logger.info(f"✅ {asset}: Total Vanna={total_vanna:.2f} ({result['interpretation']})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчёта Vanna для {asset}: {e}")
            return None
    
    def _interpret_vanna(self, total_vanna, spot, top_strikes):
        """Интерпретация Vanna"""
        if abs(total_vanna) < 100:
            return "NEUTRAL"
        
        # Положительная Vanna = рост IV увеличивает дельту (бычий)
        # Отрицательная Vanna = рост IV снижает дельту (медвежий)
        
        if total_vanna > 500:
            return "BULLISH_STRONG"
        elif total_vanna > 0:
            return "BULLISH"
        elif total_vanna < -500:
            return "BEARISH_STRONG"
        else:
            return "BEARISH"
    
    def _save_result(self, asset, result):
        """Сохранить результат"""
        try:
            filename = f"{asset}_vanna_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            logger.error(f"Ошибка сохранения Vanna: {e}")
    
    def calculate_all(self):
        """Рассчитать Vanna для всех активов"""
        assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'MNT']
        results = {}
        
        logger.info("=" * 60)
        logger.info("📊 VANNA CALCULATOR")
        logger.info("=" * 60)
        
        for asset in assets:
            result = self.calculate_asset_vanna(asset)
            if result:
                results[asset] = result
        
        logger.info("=" * 60)
        logger.info(f"✅ Обработано активов: {len(results)}")
        logger.info("=" * 60)
        
        return results


if __name__ == '__main__':
    calc = VannaCalculator()
    calc.calculate_all()
