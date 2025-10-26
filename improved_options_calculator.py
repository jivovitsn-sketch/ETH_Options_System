#!/usr/bin/env python3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ImprovedOptionsCalculator:
    def __init__(self):
        self.strategies = {
            1: "Bull Call Spread",
            2: "Bear Put Spread", 
            3: "Iron Condor",
            4: "Long Straddle",
            5: "Butterfly Spread"
        }
    
    def calculate_max_pain_level(self, spot_price):
        """Примерный расчет уровня Max Pain"""
        # Max Pain обычно находится около текущей цены ±3-5%
        return round(spot_price * 0.98 / 50) * 50
    
    def select_optimal_strikes(self, strategy_id, spot_price, dte=45, iv=0.25):
        """Улучшенный выбор страйков с учетом Max Pain и DTE"""
        
        max_pain = self.calculate_max_pain_level(spot_price)
        
        if strategy_id == 1:  # Bull Call Spread
            # Для 45 DTE: ITM long, OTM short с широким спредом
            if dte > 30:
                long_strike = round(spot_price * 0.95 / 25) * 25  # 5% ITM
                short_strike = round(spot_price * 1.15 / 25) * 25  # 15% OTM
            else:
                long_strike = round(spot_price * 0.98 / 25) * 25  # 2% ITM  
                short_strike = round(spot_price * 1.08 / 25) * 25  # 8% OTM
            
            # Расчет премий (более реалистичный)
            long_premium = self._calculate_premium(spot_price, long_strike, dte, 'call', iv)
            short_premium = self._calculate_premium(spot_price, short_strike, dte, 'call', iv)
            
            net_debit = long_premium - short_premium
            max_profit = (short_strike - long_strike) - net_debit
            max_loss = net_debit
            breakeven = long_strike + net_debit
            
        elif strategy_id == 2:  # Bear Put Spread
            if dte > 30:
                long_strike = round(spot_price * 1.05 / 25) * 25  # 5% ITM
                short_strike = round(spot_price * 0.85 / 25) * 25  # 15% OTM
            else:
                long_strike = round(spot_price * 1.02 / 25) * 25  # 2% ITM
                short_strike = round(spot_price * 0.92 / 25) * 25  # 8% OTM
            
            long_premium = self._calculate_premium(spot_price, long_strike, dte, 'put', iv)
            short_premium = self._calculate_premium(spot_price, short_strike, dte, 'put', iv)
            
            net_debit = long_premium - short_premium
            max_profit = (long_strike - short_strike) - net_debit
            max_loss = net_debit
            breakeven = long_strike - net_debit
            
        elif strategy_id == 3:  # Iron Condor
            # Симметричные страйки вокруг Max Pain
            put_long = round(max_pain * 0.85 / 25) * 25
            put_short = round(max_pain * 0.92 / 25) * 25
            call_short = round(max_pain * 1.08 / 25) * 25
            call_long = round(max_pain * 1.15 / 25) * 25
            
            # Получаем кредит от продажи
            put_credit = self._calculate_premium(spot_price, put_short, dte, 'put', iv) - \
                        self._calculate_premium(spot_price, put_long, dte, 'put', iv)
            call_credit = self._calculate_premium(spot_price, call_short, dte, 'call', iv) - \
                         self._calculate_premium(spot_price, call_long, dte, 'call', iv)
            
            net_credit = put_credit + call_credit
            max_profit = net_credit
            max_loss = min(call_short - call_long, put_short - put_long) - net_credit
            breakeven = f"{put_short + net_credit}/{call_short - net_credit}"
            
        elif strategy_id == 4:  # Long Straddle
            strike = round(spot_price / 25) * 25
            
            call_premium = self._calculate_premium(spot_price, strike, dte, 'call', iv)
            put_premium = self._calculate_premium(spot_price, strike, dte, 'put', iv)
            
            net_debit = call_premium + put_premium
            max_profit = float('inf')  # Теоретически неограничен
            max_loss = net_debit
            breakeven = f"{strike - net_debit}/{strike + net_debit}"
            
        elif strategy_id == 5:  # Butterfly Spread
            center_strike = round(max_pain / 25) * 25
            lower_strike = center_strike - 100
            upper_strike = center_strike + 100
            
            # Buy 1 lower, Sell 2 center, Buy 1 upper
            lower_premium = self._calculate_premium(spot_price, lower_strike, dte, 'call', iv)
            center_premium = self._calculate_premium(spot_price, center_strike, dte, 'call', iv)
            upper_premium = self._calculate_premium(spot_price, upper_strike, dte, 'call', iv)
            
            net_debit = lower_premium - 2*center_premium + upper_premium
            max_profit = (center_strike - lower_strike) - net_debit
            max_loss = net_debit
            breakeven = f"{lower_strike + net_debit}/{upper_strike - net_debit}"
        
        return {
            'long_strike': locals().get('long_strike', strike if 'strike' in locals() else center_strike),
            'short_strike': locals().get('short_strike', 0),
            'net_cost': locals().get('net_debit', locals().get('net_credit', 0)),
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven': breakeven,
            'max_pain_level': max_pain
        }
    
    def _calculate_premium(self, spot, strike, dte, option_type, iv):
        """Упрощенная модель расчета премии"""
        
        # Внутренняя стоимость
        if option_type == 'call':
            intrinsic = max(0, spot - strike)
        else:
            intrinsic = max(0, strike - spot)
        
        # Временная стоимость (упрощенно)
        time_value = (dte / 365) * iv * spot * 0.1
        
        # Корректировка по монетности
        moneyness = abs(spot - strike) / spot
        if moneyness > 0.1:  # OTM опционы дешевле
            time_value *= (1 - moneyness)
        
        total_premium = intrinsic + time_value
        
        # Реалистичные пределы
        return max(total_premium, spot * 0.005)  # Минимум 0.5% от спота
    
    def backtest_improved_strategies(self, spot_price=70000):
        """Улучшенный бэктест с правильными страйками"""
        
        print(f"=== IMPROVED OPTIONS BACKTEST ===")
        print(f"Spot: ${spot_price:,}")
        
        results = []
        price_moves = [-20, -15, -10, -5, 0, 5, 10, 15, 20]
        dte_options = [60, 45, 30, 21]
        
        for strategy_id in [1, 2, 3, 4, 5]:
            strategy_name = self.strategies[strategy_id]
            print(f"\nTesting {strategy_name}...")
            
            for dte in dte_options:
                strikes = self.select_optimal_strikes(strategy_id, spot_price, dte)
                
                for move in price_moves:
                    new_price = spot_price * (1 + move/100)
                    
                    # Расчет P&L на экспирации
                    pnl = self._calculate_expiry_pnl(strategy_id, strikes, spot_price, new_price)
                    
                    results.append({
                        'strategy': strategy_name,
                        'dte': dte,
                        'price_move': move,
                        'new_price': new_price,
                        'pnl': pnl,
                        'max_profit': strikes['max_profit'],
                        'max_loss': strikes['max_loss'],
                        'max_pain': strikes['max_pain_level']
                    })
        
        df = pd.DataFrame(results)
        return df
    
    def _calculate_expiry_pnl(self, strategy_id, strikes, entry_price, exit_price):
        """Расчет P&L на экспирации"""
        
        if strategy_id == 1:  # Bull Call Spread
            long_strike = strikes['long_strike']
            short_strike = strikes['short_strike']
            
            if exit_price <= long_strike:
                return -strikes['max_loss']
            elif exit_price >= short_strike:
                return strikes['max_profit']
            else:
                return (exit_price - long_strike) - strikes['max_loss']
        
        elif strategy_id == 2:  # Bear Put Spread
            long_strike = strikes['long_strike']
            short_strike = strikes['short_strike']
            
            if exit_price >= long_strike:
                return -strikes['max_loss']
            elif exit_price <= short_strike:
                return strikes['max_profit']
            else:
                return (long_strike - exit_price) - strikes['max_loss']
        
        elif strategy_id == 3:  # Iron Condor
            # Упрощенный расчет для Iron Condor
            if abs(exit_price - entry_price) / entry_price < 0.05:  # В коридоре
                return strikes['max_profit']
            else:
                return -strikes['max_loss']
        
        elif strategy_id == 4:  # Long Straddle
            strike = strikes['long_strike']
            profit = abs(exit_price - strike) - strikes['max_loss']
            return max(profit, -strikes['max_loss'])
        
        elif strategy_id == 5:  # Butterfly
            center = strikes['long_strike']
            if abs(exit_price - center) < 50:  # Близко к центру
                return strikes['max_profit']
            else:
                return -strikes['max_loss']

def analyze_improved_results(df):
    """Анализ улучшенных результатов"""
    print(f"\n=== IMPROVED ANALYSIS ===")
    
    # Общая статистика
    profitable = df[df['pnl'] > 0]
    print(f"Total scenarios: {len(df):,}")
    print(f"Profitable: {len(profitable):,} ({len(profitable)/len(df)*100:.1f}%)")
    
    # По стратегиям
    strategy_stats = df.groupby('strategy').agg({
        'pnl': ['count', lambda x: (x > 0).mean() * 100, 'mean', 'max'],
    }).round(1)
    
    strategy_stats.columns = ['Total', 'Win_Rate_%', 'Avg_PnL', 'Max_PnL']
    
    print(f"\nSTRATEGY PERFORMANCE:")
    print(strategy_stats)
    
    # Лучшие настройки
    best_setups = df.nlargest(10, 'pnl')[['strategy', 'dte', 'price_move', 'pnl']]
    print(f"\nBEST SETUPS:")
    for _, row in best_setups.iterrows():
        print(f"{row['strategy']} | {row['dte']}DTE | {row['price_move']}% move | ${row['pnl']:,.0f}")

if __name__ == "__main__":
    calc = ImprovedOptionsCalculator()
    results_df = calc.backtest_improved_strategies(70000)
    analyze_improved_results(results_df)
    
    # Сохраняем результаты
    results_df.to_csv('data/improved_backtest_results.csv', index=False)
    print(f"\nResults saved: data/improved_backtest_results.csv")
