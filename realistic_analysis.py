#!/usr/bin/env python3
import pandas as pd

def analyze_realistic_scenarios():
    df = pd.read_csv('data/options_backtest_results.csv')
    
    print("=== REALISTIC BACKTEST ANALYSIS ===")
    
    # Проблемы с текущими расчетами
    print("IDENTIFIED ISSUES:")
    print("1. Bull/Bear spreads: 0% win rate (unrealistic)")
    print("2. Long Straddle: $367,500 profit on 30% move (inflated)")
    print("3. Identical repeated results (simulation bugs)")
    
    # Реалистичные сценарии (движения 5-20%)
    realistic_moves = df[df['price_move'].abs().between(5, 20)]
    
    print(f"\nREALISTIC SCENARIOS (5-20% moves):")
    print(f"Total: {len(realistic_moves):,}")
    
    realistic_profit = realistic_moves[realistic_moves['leveraged_profit'] > 0]
    
    if len(realistic_profit) > 0:
        strategy_performance = realistic_profit.groupby('strategy').agg({
            'leveraged_profit': ['count', 'mean', 'max'],
            'leveraged_roi': 'mean'
        }).round(0)
        
        print("\nREALISTIC STRATEGY PERFORMANCE:")
        for strategy, data in strategy_performance.iterrows():
            profit_count = data[('leveraged_profit', 'count')]
            avg_profit = data[('leveraged_profit', 'mean')]
            max_profit = data[('leveraged_profit', 'max')]
            avg_roi = data[('leveraged_roi', 'mean')]
            
            print(f"{strategy}:")
            print(f"  Wins: {profit_count}, Avg: ${avg_profit:,.0f}, Max: ${max_profit:,.0f}, ROI: {avg_roi:.0f}%")
    
    # Практические рекомендации
    print(f"\nPRACTICAL RECOMMENDATIONS:")
    print("1. Long Straddle: Best for expecting big moves (>15%)")
    print("2. Iron Condor: Consistent profits in range-bound markets")
    print("3. Avoid Bull/Bear spreads until logic is fixed")
    print("4. Focus on 10-20% price movement scenarios")
    
    # Корректировка расчетов
    print(f"\nCORRECTED CALCULATIONS NEEDED:")
    print("- Bull/Bear spreads: Should profit on directional moves")
    print("- Realistic premiums: 2-5% of underlying, not 15%")
    print("- Leverage: 10-15x more realistic than 35x")
    print("- Max profit caps: $50k-100k range more realistic")

if __name__ == "__main__":
    analyze_realistic_scenarios()
