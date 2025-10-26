#!/usr/bin/env python3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class OptionsBacktester:
    def __init__(self):
        self.strategies = {
            1: "Bull Call Spread",
            2: "Bear Put Spread", 
            3: "Long Straddle",
            4: "Short Straddle",
            5: "Iron Condor",
            6: "Butterfly Spread",
            7: "Collar",
            8: "Protective Put",
            9: "Covered Call",
            10: "Jade Lizard",
            11: "Big Lizard",
            12: "Short Strangle"
        }
        
        # Леверидж опционов vs спот
        self.leverage_multiplier = 35  # 35 контрактов вместо 1 BTC
        
        # Take Profit варианты (% от максимальной прибыли)
        self.take_profit_levels = [
            25, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250, 300
        ]
        
        # Варианты выходов
        self.exit_strategies = [
            "50% profit target",
            "75% profit target", 
            "100% profit target",
            "DTE-based (21 days)",
            "DTE-based (14 days)",
            "DTE-based (7 days)",
            "Theta decay (-50%)",
            "Delta neutral",
            "Volatility expansion",
            "Time decay optimization",
            "Rolling strategy",
            "Partial profit taking"
        ]
    
    def calculate_strategy_parameters(self, strategy_id, spot_price, iv=0.25, dte=45):
        """Расчет параметров для каждой стратегии"""
        
        if strategy_id == 1:  # Bull Call Spread
            long_strike = round(spot_price / 50) * 50
            short_strike = long_strike + 200
            cost = 0.05 * spot_price / 1000  # ETH units
            max_profit = 200 - (cost * 1000)
            max_loss = cost * 1000
            breakeven = long_strike + (cost * 1000)
            
        elif strategy_id == 2:  # Bear Put Spread
            long_strike = round(spot_price / 50) * 50
            short_strike = long_strike - 200
            cost = 0.05 * spot_price / 1000
            max_profit = 200 - (cost * 1000)
            max_loss = cost * 1000
            breakeven = long_strike - (cost * 1000)
            
        elif strategy_id == 3:  # Long Straddle
            strike = round(spot_price / 50) * 50
            cost = 0.15 * spot_price / 1000  # Дороже из-за покупки волатильности
            max_profit = float('inf')  # Теоретически неограничен
            max_loss = cost * 1000
            breakeven = f"{strike - cost*1000}/{strike + cost*1000}"
            
        elif strategy_id == 4:  # Short Straddle
            strike = round(spot_price / 50) * 50
            cost = -0.15 * spot_price / 1000  # Получаем премию
            max_profit = abs(cost * 1000)
            max_loss = float('inf')  # Теоретически неограничен
            breakeven = f"{strike - abs(cost)*1000}/{strike + abs(cost)*1000}"
            
        elif strategy_id == 5:  # Iron Condor
            otm_put = round(spot_price * 0.9 / 50) * 50
            itm_put = otm_put + 100
            itm_call = round(spot_price * 1.1 / 50) * 50  
            otm_call = itm_call + 100
            cost = 0.02 * spot_price / 1000  # Небольшой дебит
            max_profit = 100 - (cost * 1000)
            max_loss = cost * 1000
            breakeven = f"{itm_put + cost*1000}/{itm_call - cost*1000}"
            
        else:
            # Базовые расчеты для остальных стратегий
            cost = 0.08 * spot_price / 1000
            max_profit = 150
            max_loss = cost * 1000
            breakeven = spot_price
        
        return {
            'cost': cost,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven': breakeven,
            'leverage': self.leverage_multiplier
        }
    
    def simulate_trade_outcomes(self, strategy_id, spot_price, price_moves):
        """Симуляция результатов торговли"""
        params = self.calculate_strategy_parameters(strategy_id, spot_price)
        
        results = []
        
        for move in price_moves:
            new_price = spot_price * (1 + move/100)
            
            # Симуляция P&L для каждого варианта выхода
            for tp_level in self.take_profit_levels:
                for exit_strategy in self.exit_strategies[:10]:  # Первые 10
                    
                    # Расчет прибыли/убытка
                    if strategy_id in [1, 2]:  # Спреды
                        if move > 0 and strategy_id == 1:  # Bull Call при росте
                            profit = min(params['max_profit'] * tp_level/100, params['max_profit'])
                        elif move < 0 and strategy_id == 2:  # Bear Put при падении
                            profit = min(params['max_profit'] * tp_level/100, params['max_profit'])
                        else:
                            profit = -params['max_loss'] * min(abs(move)/10, 1)
                    
                    elif strategy_id == 3:  # Long Straddle
                        profit = max(abs(move) * spot_price/100 - params['max_loss'], -params['max_loss'])
                        profit = min(profit * tp_level/100, profit)
                    
                    else:  # Остальные стратегии
                        base_profit = move * spot_price / 100 * 0.1  # 10% от движения
                        profit = base_profit * tp_level/100
                    
                    # Учитываем леверидж
                    leveraged_profit = profit * params['leverage']
                    
                    results.append({
                        'strategy': self.strategies[strategy_id],
                        'price_move': move,
                        'new_price': new_price,
                        'take_profit': tp_level,
                        'exit_strategy': exit_strategy,
                        'profit_usd': profit,
                        'leveraged_profit': leveraged_profit,
                        'roi_percent': (profit / params['max_loss']) * 100 if params['max_loss'] > 0 else 0,
                        'leveraged_roi': (leveraged_profit / (params['max_loss'] * params['leverage'])) * 100
                    })
        
        return results
    
    def run_comprehensive_backtest(self, spot_price=70000):
        """Запуск полного бэктеста"""
        print(f"=== OPTIONS STRATEGIES BACKTEST ===")
        print(f"Spot Price: ${spot_price:,}")
        print(f"Leverage Multiplier: {self.leverage_multiplier}x")
        print(f"Strategies: {len(self.strategies)}")
        print(f"Take Profit Levels: {len(self.take_profit_levels)}")
        print(f"Exit Strategies: {len(self.exit_strategies)}")
        
        # Различные сценарии движения цены
        price_scenarios = [-20, -15, -10, -5, -2, 0, 2, 5, 10, 15, 20, 25, 30]
        
        all_results = []
        
        for strategy_id in self.strategies.keys():
            print(f"\nTesting {self.strategies[strategy_id]}...")
            
            results = self.simulate_trade_outcomes(strategy_id, spot_price, price_scenarios)
            all_results.extend(results)
        
        # Создаем DataFrame для анализа
        df = pd.DataFrame(all_results)
        
        return df
    
    def analyze_best_setups(self, df):
        """Анализ лучших настроек"""
        print(f"\n=== BACKTEST ANALYSIS ===")
        
        # Топ 10 по ROI
        top_roi = df.nlargest(10, 'leveraged_roi')
        print(f"\nTOP 10 SETUPS BY LEVERAGED ROI:")
        for i, row in top_roi.iterrows():
            print(f"{row['strategy']} | Move: {row['price_move']}% | TP: {row['take_profit']}% | ROI: {row['leveraged_roi']:.1f}%")
        
        # Топ 10 по абсолютной прибыли
        top_profit = df.nlargest(10, 'leveraged_profit')
        print(f"\nTOP 10 BY ABSOLUTE PROFIT:")
        for i, row in top_profit.iterrows():
            print(f"{row['strategy']} | Move: {row['price_move']}% | Profit: ${row['leveraged_profit']:,.0f}")
        
        # Статистика по стратегиям
        strategy_stats = df.groupby('strategy').agg({
            'leveraged_roi': ['mean', 'max', 'min', 'std'],
            'leveraged_profit': ['mean', 'max', 'min']
        }).round(1)
        
        print(f"\nSTRATEGY STATISTICS:")
        print(strategy_stats)
        
        return top_roi, top_profit, strategy_stats

def create_trading_plan(best_setups):
    """Создание торгового плана"""
    
    plan = f"""
# TRADING PLAN - OPTIONS STRATEGIES

## BEST PERFORMING SETUPS

### High ROI Strategies:
"""
    
    for i, row in best_setups.head(5).iterrows():
        plan += f"""
**{row['strategy']}**
- Price Move: {row['price_move']}%
- Take Profit: {row['take_profit']}%
- Expected ROI: {row['leveraged_roi']:.1f}%
- Target Profit: ${row['leveraged_profit']:,.0f}
"""
    
    plan += f"""
## RISK MANAGEMENT

### Position Sizing:
- Max 2% of capital per trade
- Leverage: 35x (options vs spot)
- Max 3 concurrent positions

### Exit Rules:
1. Take 50% profit at 25% max profit
2. Close at 21 DTE if unprofitable  
3. Stop loss at 2x initial debit
4. Roll positions if delta neutral

### Market Conditions:
- High IV: Sell premium (Short Straddle, Iron Condor)
- Low IV: Buy premium (Long Straddle, Spreads)
- Trending: Directional spreads
- Ranging: Neutral strategies
"""
    
    return plan

if __name__ == "__main__":
    backtest = OptionsBacktester()
    
    # Запускаем бэктест для BTC
    results_df = backtest.run_comprehensive_backtest(70000)
    
    # Анализируем результаты
    top_roi, top_profit, stats = backtest.analyze_best_setups(results_df)
    
    # Создаем торговый план
    trading_plan = create_trading_plan(top_roi)
    
    # Сохраняем результаты
    results_df.to_csv('data/options_backtest_results.csv', index=False)
    
    with open('data/TRADING_PLAN.md', 'w') as f:
        f.write(trading_plan)
    
    print(f"\n✅ Backtest complete!")
    print(f"📊 Results saved: data/options_backtest_results.csv")
    print(f"📋 Trading plan: data/TRADING_PLAN.md") 
    print(f"📈 Total scenarios tested: {len(results_df)}")
