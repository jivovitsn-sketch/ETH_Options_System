#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REAL DATA ANALYSIS - ML подход
Анализ реальных данных из БД
"""

import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
from collections import defaultdict

class RealDataAnalyzer:
    """Анализ реальных данных"""
    
    def __init__(self):
        self.db_path = './data/unlimited_oi.db'
    
    def analyze_volatility(self) -> Dict[str, Any]:
        """Анализ волатильности по активам"""
        print("\n" + "=" * 80)
        print("📊 АНАЛИЗ ВОЛАТИЛЬНОСТИ")
        print("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        
        # Получаем уникальные цены по активам
        query = '''
            SELECT asset, timestamp, spot_price
            FROM all_positions_tracking
            WHERE spot_price > 0
            GROUP BY asset, timestamp
            ORDER BY asset, timestamp
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        results = {}
        
        for asset in df['asset'].unique():
            asset_data = df[df['asset'] == asset].copy()
            
            if len(asset_data) < 2:
                continue
            
            # Сортируем по времени
            asset_data = asset_data.sort_values('timestamp')
            
            # Log returns
            asset_data['returns'] = np.log(asset_data['spot_price'] / asset_data['spot_price'].shift(1))
            
            # Убираем NaN
            returns = asset_data['returns'].dropna()
            
            if len(returns) < 2:
                continue
            
            # Статистика
            daily_vol = returns.std()
            annual_vol = daily_vol * np.sqrt(365)
            mean_return = returns.mean()
            
            # Временной период
            time_span = (asset_data['timestamp'].max() - asset_data['timestamp'].min())
            days = time_span / 86400
            
            results[asset] = {
                'daily_vol': daily_vol,
                'annual_vol': annual_vol,
                'mean_daily_return': mean_return,
                'n_datapoints': len(asset_data),
                'days_covered': days,
                'avg_price': asset_data['spot_price'].mean(),
                'min_price': asset_data['spot_price'].min(),
                'max_price': asset_data['spot_price'].max()
            }
            
            print(f"\n📊 {asset}:")
            print(f"  Период: {days:.1f} дней ({len(asset_data)} точек)")
            print(f"  Средняя цена: ${results[asset]['avg_price']:,.2f}")
            print(f"  Диапазон: ${results[asset]['min_price']:,.2f} - ${results[asset]['max_price']:,.2f}")
            print(f"  Daily Vol: {daily_vol*100:.2f}%")
            print(f"  Annual Vol: {annual_vol*100:.1f}%")
            print(f"  Mean Daily Return: {mean_return*100:.3f}%")
        
        return results
    
    def analyze_dte_volatility(self) -> Dict[str, Dict[int, Any]]:
        """Анализ волатильности по DTE (экспирациям)"""
        print("\n" + "=" * 80)
        print("📅 АНАЛИЗ ВОЛАТИЛЬНОСТИ ПО DTE")
        print("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT asset, dte, strike, option_type, open_interest, spot_price
            FROM all_positions_tracking
            WHERE open_interest > 0 AND dte IS NOT NULL
            ORDER BY asset, dte
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        results = defaultdict(lambda: defaultdict(list))
        
        for asset in df['asset'].unique():
            asset_data = df[df['asset'] == asset]
            
            # Группируем по DTE
            dte_groups = asset_data.groupby('dte')
            
            print(f"\n📊 {asset}:")
            
            for dte, group in dte_groups:
                if len(group) < 5:  # Минимум 5 контрактов
                    continue
                
                # Implied Vol через strike spread
                strikes = group['strike'].values
                spot = group['spot_price'].mean()
                
                # Монетарность
                moneyness = (strikes - spot) / spot
                
                # Средняя дистанция страйков от спота
                avg_distance = np.abs(moneyness).mean()
                
                # OI концентрация
                total_oi = group['open_interest'].sum()
                avg_oi = group['open_interest'].mean()
                
                results[asset][dte] = {
                    'n_contracts': len(group),
                    'total_oi': total_oi,
                    'avg_oi': avg_oi,
                    'avg_strike_distance': avg_distance,
                    'spot_price': spot
                }
                
                print(f"  DTE {dte:3d}: {len(group):4d} contracts | OI: {total_oi:10,.0f} | Avg distance: {avg_distance*100:5.1f}%")
        
        return dict(results)
    
    def analyze_liquidity(self) -> Dict[str, Any]:
        """Анализ ликвидности опционов"""
        print("\n" + "=" * 80)
        print("💧 АНАЛИЗ ЛИКВИДНОСТИ")
        print("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT asset, 
                   COUNT(*) as total_contracts,
                   SUM(open_interest) as total_oi,
                   AVG(open_interest) as avg_oi,
                   SUM(volume_24h) as total_volume,
                   AVG(volume_24h) as avg_volume
            FROM all_positions_tracking
            WHERE open_interest > 0
            GROUP BY asset
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        results = {}
        
        print("\n")
        for _, row in df.iterrows():
            asset = row['asset']
            
            # Классификация ликвидности
            if row['total_oi'] > 1000000:
                liquidity_class = 'VERY_HIGH'
            elif row['total_oi'] > 100000:
                liquidity_class = 'HIGH'
            elif row['total_oi'] > 10000:
                liquidity_class = 'MEDIUM'
            else:
                liquidity_class = 'LOW'
            
            results[asset] = {
                'total_contracts': int(row['total_contracts']),
                'total_oi': float(row['total_oi']),
                'avg_oi': float(row['avg_oi']),
                'total_volume': float(row['total_volume']),
                'avg_volume': float(row['avg_volume']),
                'liquidity_class': liquidity_class
            }
            
            print(f"📊 {asset:6s} | {liquidity_class:10s} | Contracts: {int(row['total_contracts']):5d} | Total OI: {row['total_oi']:12,.0f}")
        
        return results
    
    def generate_ml_configs(self, vol_data: Dict, liq_data: Dict) -> Dict[str, Dict]:
        """Генерация конфигураций на основе ML анализа"""
        print("\n" + "=" * 80)
        print("🤖 ML ГЕНЕРАЦИЯ КОНФИГУРАЦИЙ")
        print("=" * 80)
        
        configs = {}
        
        for asset in vol_data.keys():
            if asset not in liq_data:
                continue
            
            vol = vol_data[asset]
            liq = liq_data[asset]
            
            # ML ЛОГИКА:
            # Высокая вола → ниже min_confidence (больше сигналов)
            # Низкая ликвидность → выше min_data_sources
            # Высокая вола → шире страйки
            
            daily_vol = vol['daily_vol']
            liquidity = liq['liquidity_class']
            
            # Базовый конфиг
            config = {
                'asset': asset,
                'ml_generated': True
            }
            
            # MIN CONFIDENCE на основе волатильности
            if daily_vol < 0.02:  # < 2% daily vol
                config['min_confidence'] = 0.70
                config['strong_threshold'] = 0.85
            elif daily_vol < 0.04:  # 2-4%
                config['min_confidence'] = 0.65
                config['strong_threshold'] = 0.80
            elif daily_vol < 0.06:  # 4-6%
                config['min_confidence'] = 0.60
                config['strong_threshold'] = 0.75
            else:  # > 6%
                config['min_confidence'] = 0.55
                config['strong_threshold'] = 0.70
            
            # LIQUIDITY FILTERS
            if liquidity == 'VERY_HIGH':
                config['min_data_sources'] = 8
                config['require_futures_confirm'] = True
                config['require_options_confirm'] = True
            elif liquidity == 'HIGH':
                config['min_data_sources'] = 7
                config['require_futures_confirm'] = True
                config['require_options_confirm'] = True
            elif liquidity == 'MEDIUM':
                config['min_data_sources'] = 6
                config['require_futures_confirm'] = True
                config['require_options_confirm'] = False
            else:  # LOW
                config['min_data_sources'] = 5
                config['require_futures_confirm'] = False
                config['require_options_confirm'] = False
            
            # WEIGHTS на основе волатильности
            if daily_vol > 0.05:  # Высокая вола
                config['futures_weight'] = 0.30  # Меньше вес фьючерсам
                config['options_weight'] = 0.45  # Больше опционам
                config['timing_weight'] = 0.25
            else:  # Низкая вола
                config['futures_weight'] = 0.40
                config['options_weight'] = 0.35
                config['timing_weight'] = 0.25
            
            # STRIKE SELECTION на основе волатильности
            config['strike_otm_pct'] = min(0.05, daily_vol * 2)  # 2x daily vol
            config['max_premium_pct'] = min(0.15, daily_vol * 3)  # 3x daily vol
            
            # DTE PREFERENCE
            if daily_vol > 0.06:
                config['preferred_dte'] = [3, 7, 14]  # Короткие для высокой волы
            else:
                config['preferred_dte'] = [7, 14, 21]  # Длинные для низкой
            
            # STATS для справки
            config['stats'] = {
                'daily_vol': f"{daily_vol*100:.2f}%",
                'annual_vol': f"{vol['annual_vol']*100:.1f}%",
                'liquidity': liquidity,
                'total_oi': liq['total_oi'],
                'n_datapoints': vol['n_datapoints']
            }
            
            configs[asset] = config
            
            print(f"\n🤖 {asset}:")
            print(f"  Daily Vol: {daily_vol*100:.2f}% → min_confidence: {config['min_confidence']:.0%}")
            print(f"  Liquidity: {liquidity} → min_sources: {config['min_data_sources']}")
            print(f"  Weights: F{config['futures_weight']:.0%}/O{config['options_weight']:.0%}/T{config['timing_weight']:.0%}")
            print(f"  Strike OTM: {config['strike_otm_pct']*100:.1f}%")
            print(f"  Preferred DTE: {config['preferred_dte']}")
        
        return configs
    
    def run_full_analysis(self):
        """Полный анализ"""
        print("=" * 80)
        print("🔬 ПОЛНЫЙ ML АНАЛИЗ РЕАЛЬНЫХ ДАННЫХ")
        print("=" * 80)
        
        # 1. Волатильность
        vol_data = self.analyze_volatility()
        
        # 2. DTE анализ
        dte_data = self.analyze_dte_volatility()
        
        # 3. Ликвидность
        liq_data = self.analyze_liquidity()
        
        # 4. Генерация конфигов
        ml_configs = self.generate_ml_configs(vol_data, liq_data)
        
        # 5. Сохранение результатов
        import json
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'volatility_analysis': vol_data,
            'dte_analysis': {k: {int(dte): v for dte, v in dtes.items()} for k, dtes in dte_data.items()},
            'liquidity_analysis': liq_data,
            'ml_configs': ml_configs
        }
        
        with open('ml_analysis_results.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print("\n" + "=" * 80)
        print("✅ АНАЛИЗ ЗАВЕРШЁН")
        print("📄 Результаты сохранены в: ml_analysis_results.json")
        print("=" * 80)
        
        return output


if __name__ == '__main__':
    analyzer = RealDataAnalyzer()
    results = analyzer.run_full_analysis()
