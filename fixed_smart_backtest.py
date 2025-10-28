#!/usr/bin/env python3
import requests
import pandas as pd
import numpy as np

class SmartBacktest:
    def __init__(self):
        # Индивидуальные параметры по активам
        self.asset_params = {
            'BTC': {
                'vol_expectation': 0.08,  # 8% обычное движение за 2 недели
                'tp_optimal': 0.30,       # 30% от макс прибыли оптимально
                'sl_tight': 0.40,         # 40% от входа
                'move_scenarios': [-12, -8, -4, 0, 4, 8, 12]
            },
            'ETH': {
                'vol_expectation': 0.12,  # 12% обычное движение
                'tp_optimal': 0.35,
                'sl_tight': 0.45,
                'move_scenarios': [-15, -10, -5, 0, 5, 10, 15]
            },
            'SOL': {
                'vol_expectation': 0.20,  # 20% обычное движение
                'tp_optimal': 0.25,
                'sl_tight': 0.35,
                'move_scenarios': [-25, -15, -8, 0, 8, 15, 25]
            },
            'XRP': {
                'vol_expectation': 0.25,  # 25% обычное движение
                'tp_optimal': 0.20,
                'sl_tight': 0.30,
                'move_scenarios': [-30, -20, -10, 0, 10, 20, 30]
            }
        }
    
    def smart_exit_logic(self, current_pnl, entry_cost, max_profit, asset, days_held):
        """Умная логика выхода с учетом специфики актива"""
        
        params = self.asset_params[asset]
        
        # Динамический TP в зависимости от времени
        time_factor = max(0.5, 1 - (days_held / 45))  # Уменьшаем TP со временем
        dynamic_tp = params['tp_optimal'] * time_factor
        
        # Умный SL с учетом волатильности
        vol_adjusted_sl = params['sl_tight'] * (1 + params['vol_expectation'])
        
        tp_target = max_profit * dynamic_tp
        sl_target = -entry_cost * vol_adjusted_sl
        
        if current_pnl >= tp_target:
            return tp_target, "smart_tp"
        elif current_pnl <= sl_target:
            return sl_target, "smart_sl"
        else:
            return current_pnl, "hold"
    
    def test_asset_specific(self, asset):
        """Тестирование с учетом специфики актива"""
        
        print(f"Testing {asset} with optimized parameters...")
        
        # Тут будет логика получения реальных цен
        # И применения умных правил выхода
        
        params = self.asset_params[asset]
        results = []
        
        # Симуляция разных сценариев
        for move in params['move_scenarios']:
            for days in [7, 14, 21]:
                # Расчет P&L с умной логикой
                # (здесь будет реальная логика)
                
                # Пример результата
                results.append({
                    'asset': asset,
                    'move': move,
                    'days': days,
                    'tp_used': params['tp_optimal'],
                    'sl_used': params['sl_tight']
                })
        
        return results

if __name__ == "__main__":
    backtest = SmartBacktest()
    
    print("=== ASSET-SPECIFIC PARAMETERS ===")
    for asset, params in backtest.asset_params.items():
        print(f"{asset}:")
        print(f"  Expected vol: {params['vol_expectation']*100:.0f}%")
        print(f"  Optimal TP: {params['tp_optimal']*100:.0f}%")
        print(f"  Smart SL: {params['sl_tight']*100:.0f}%")
