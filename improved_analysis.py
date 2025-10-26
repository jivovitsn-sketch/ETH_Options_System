#!/usr/bin/env python3
import pandas as pd
import numpy as np

def analyze_backtest_results():
    df = pd.read_csv('data/options_backtest_results.csv')
    
    print("=== DETAILED BACKTEST ANALYSIS ===")
    print(f"Total scenarios: {len(df):,}")
    
    # Фильтруем только прибыльные сделки
    profitable = df[df['leveraged_profit'] > 0]
    print(f"Profitable scenarios: {len(profitable):,} ({len(profitable)/len(df)*100:.1f}%)")
    
    # Топ стратегии по винрейту
    winrate = df.groupby('strategy').apply(lambda x: (x['leveraged_profit'] > 0).mean() * 100).sort_values(ascending=False)
    print(f"\nWIN RATES BY STRATEGY:")
    for strategy, rate in winrate.items():
        print(f"{strategy}: {rate:.1f}%")
    
    # Средняя прибыль по стратегиям (только profitable)
    if len(profitable) > 0:
        avg_profit = profitable.groupby('strategy')['leveraged_profit'].mean().sort_values(ascending=False)
        print(f"\nAVERAGE PROFIT (profitable trades only):")
        for strategy, profit in avg_profit.head(5).items():
            print(f"{strategy}: ${profit:,.0f}")
    
    # Лучшие комбинации параметров
    print(f"\nBEST PARAMETER COMBINATIONS:")
    best_combos = df.nlargest(10, 'leveraged_profit')[['strategy', 'price_move', 'take_profit', 'leveraged_profit', 'leveraged_roi']]
    for i, row in best_combos.iterrows():
        print(f"{row['strategy']} | Move: {row['price_move']}% | TP: {row['take_profit']}% | Profit: ${row['leveraged_profit']:,.0f} | ROI: {row['leveraged_roi']:.1f}%")
    
    # Анализ по движениям цены
    price_analysis = df.groupby('price_move').agg({
        'leveraged_profit': ['mean', 'count'],
        'leveraged_roi': 'mean'
    }).round(2)
    
    print(f"\nPERFORMANCE BY PRICE MOVEMENT:")
    print(price_analysis)

if __name__ == "__main__":
    analyze_backtest_results()
