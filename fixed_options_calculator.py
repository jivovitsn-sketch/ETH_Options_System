#!/usr/bin/env python3
import pandas as pd
import numpy as np

class FixedOptionsCalculator:
    def __init__(self):
        self.strategies = {
            1: "Bull Call Spread",
            2: "Bear Put Spread",
            3: "Iron Condor", 
            4: "Long Straddle",
            5: "Butterfly Spread"
        }
        # РЕАЛИСТИЧНЫЙ ЛЕВЕРИДЖ 10-15x
        self.leverage = 12
    
    def calculate_max_pain(self, spot_price):
        return round(spot_price * 0.98 / 50) * 50
    
    def calculate_strikes(self, strategy_id, spot_price, dte=45):
        """Исправленный расчет страйков"""
        
        if strategy_id == 1:  # Bull Call Spread
            if dte > 30:
                long_strike = round(spot_price * 0.95 / 25) * 25
                short_strike = round(spot_price * 1.15 / 25) * 25
            else:
                long_strike = round(spot_price * 0.98 / 25) * 25
                short_strike = round(spot_price * 1.08 / 25) * 25
            
            net_debit = (short_strike - long_strike) * 0.3  # 30% от ширины
            max_profit = (short_strike - long_strike) - net_debit
            max_loss = net_debit
            
        elif strategy_id == 2:  # Bear Put Spread
            if dte > 30:
                long_strike = round(spot_price * 1.05 / 25) * 25
                short_strike = round(spot_price * 0.85 / 25) * 25
            else:
                long_strike = round(spot_price * 1.02 / 25) * 25
                short_strike = round(spot_price * 0.92 / 25) * 25
            
            net_debit = (long_strike - short_strike) * 0.3
            max_profit = (long_strike - short_strike) - net_debit
            max_loss = net_debit
            
        elif strategy_id == 3:  # Iron Condor
            center = self.calculate_max_pain(spot_price)
            put_long = round(center * 0.85 / 25) * 25
            put_short = round(center * 0.92 / 25) * 25
            call_short = round(center * 1.08 / 25) * 25
            call_long = round(center * 1.15 / 25) * 25
            
            long_strike = put_long
            short_strike = call_long
            net_debit = 100  # Фиксированный дебит
            max_profit = 300
            max_loss = net_debit
            
        elif strategy_id == 4:  # Long Straddle
            long_strike = round(spot_price / 25) * 25
            short_strike = long_strike
            net_debit = spot_price * 0.08  # 8% от цены спота
            max_profit = 999999  # Неограничен
            max_loss = net_debit
            
        elif strategy_id == 5:  # Butterfly
            center = round(spot_price / 25) * 25
            long_strike = center - 100
            short_strike = center + 100
            net_debit = 200
            max_profit = 300
            max_loss = net_debit
        
        return {
            'long_strike': long_strike,
            'short_strike': short_strike, 
            'net_debit': net_debit,
            'max_profit': max_profit,
            'max_loss': max_loss
        }
    
    def calculate_pnl(self, strategy_id, strikes, entry_price, exit_price):
        """Расчет P&L на экспирации"""
        
        if strategy_id == 1:  # Bull Call Spread
            if exit_price <= strikes['long_strike']:
                return -strikes['max_loss']
            elif exit_price >= strikes['short_strike']:
                return strikes['max_profit']
            else:
                return (exit_price - strikes['long_strike']) - strikes['max_loss']
        
        elif strategy_id == 2:  # Bear Put Spread
            if exit_price >= strikes['long_strike']:
                return -strikes['max_loss']
            elif exit_price <= strikes['short_strike']:
                return strikes['max_profit']
            else:
                return (strikes['long_strike'] - exit_price) - strikes['max_loss']
        
        elif strategy_id == 3:  # Iron Condor
            move_percent = abs(exit_price - entry_price) / entry_price
            if move_percent < 0.08:  # В коридоре ±8%
                return strikes['max_profit']
            else:
                return -strikes['max_loss']
        
        elif strategy_id == 4:  # Long Straddle
            move_amount = abs(exit_price - strikes['long_strike'])
            profit = move_amount - strikes['max_loss']
            return max(profit, -strikes['max_loss'])
        
        elif strategy_id == 5:  # Butterfly
            center = strikes['long_strike'] + 100
            distance = abs(exit_price - center)
            if distance < 50:
                return strikes['max_profit']
            else:
                return -strikes['max_loss']
    
    def run_backtest(self, spot_price=70000):
        """Запуск исправленного бэктеста"""
        
        print(f"=== FIXED OPTIONS BACKTEST ===")
        print(f"Spot: ${spot_price:,}")
        print(f"Leverage: {self.leverage}x (realistic)")
        
        results = []
        price_moves = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25]
        dte_list = [60, 45, 30, 21]
        
        for strategy_id in self.strategies.keys():
            strategy_name = self.strategies[strategy_id]
            print(f"Testing {strategy_name}...")
            
            for dte in dte_list:
                strikes = self.calculate_strikes(strategy_id, spot_price, dte)
                
                for move in price_moves:
                    new_price = spot_price * (1 + move/100)
                    
                    base_pnl = self.calculate_pnl(strategy_id, strikes, spot_price, new_price)
                    leveraged_pnl = base_pnl * self.leverage
                    
                    results.append({
                        'strategy': strategy_name,
                        'dte': dte,
                        'price_move': move,
                        'new_price': new_price,
                        'base_pnl': base_pnl,
                        'leveraged_pnl': leveraged_pnl,
                        'max_profit': strikes['max_profit'] * self.leverage,
                        'max_loss': strikes['max_loss'] * self.leverage,
                        'long_strike': strikes['long_strike'],
                        'short_strike': strikes['short_strike']
                    })
        
        df = pd.DataFrame(results)
        return df

def analyze_fixed_results(df):
    """Анализ исправленных результатов"""
    
    print(f"\n=== FIXED ANALYSIS ===")
    print(f"Total scenarios: {len(df):,}")
    
    profitable = df[df['leveraged_pnl'] > 0]
    print(f"Profitable: {len(profitable):,} ({len(profitable)/len(df)*100:.1f}%)")
    
    # Статистика по стратегиям
    strategy_stats = df.groupby('strategy').agg({
        'leveraged_pnl': [
            lambda x: (x > 0).mean() * 100,  # Win rate
            'mean',  # Average PnL
            'max',   # Max profit
            'min'    # Max loss
        ]
    }).round(1)
    
    strategy_stats.columns = ['Win_Rate_%', 'Avg_PnL', 'Max_Profit', 'Max_Loss']
    
    print(f"\nSTRATEGY PERFORMANCE:")
    for strategy, data in strategy_stats.iterrows():
        print(f"{strategy}:")
        print(f"  Win Rate: {data['Win_Rate_%']:.1f}%")
        print(f"  Avg PnL: ${data['Avg_PnL']:,.0f}")
        print(f"  Max Profit: ${data['Max_Profit']:,.0f}")
        print(f"  Max Loss: ${data['Max_Loss']:,.0f}")
        print()
    
    # Лучшие настройки
    best_setups = df.nlargest(10, 'leveraged_pnl')
    print(f"BEST SETUPS:")
    for _, row in best_setups.iterrows():
        print(f"{row['strategy']} | {row['dte']}DTE | {row['price_move']}% | ${row['leveraged_pnl']:,.0f}")

if __name__ == "__main__":
    calc = FixedOptionsCalculator()
    results_df = calc.run_backtest(70000)
    analyze_fixed_results(results_df)
    
    # Сохраняем
    results_df.to_csv('data/fixed_backtest_results.csv', index=False)
    print(f"\nFixed results saved: data/fixed_backtest_results.csv")
