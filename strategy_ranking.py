#!/usr/bin/env python3
import pandas as pd

def rank_strategies():
    df = pd.read_csv('data/fixed_backtest_results.csv')
    
    print("=== FINAL STRATEGY RANKING ===")
    
    # Расчет метрик эффективности
    strategy_metrics = df.groupby('strategy').agg({
        'leveraged_pnl': [
            lambda x: (x > 0).mean() * 100,  # Win Rate
            'mean',  # Average PnL
            'std',   # Volatility
            lambda x: x.mean() / x.std() if x.std() > 0 else 0  # Sharpe-like ratio
        ]
    }).round(2)
    
    strategy_metrics.columns = ['Win_Rate', 'Avg_PnL', 'Volatility', 'Risk_Ratio']
    
    # Добавляем оценку риск/доходность
    strategy_metrics['Score'] = (
        strategy_metrics['Win_Rate'] * 0.3 +  # 30% weight
        (strategy_metrics['Avg_PnL'] / 1000) * 0.4 +  # 40% weight 
        strategy_metrics['Risk_Ratio'] * 30  # 30% weight
    ).round(1)
    
    # Сортируем по общему счету
    ranking = strategy_metrics.sort_values('Score', ascending=False)
    
    print("RANKING (по общему счету):")
    for i, (strategy, data) in enumerate(ranking.iterrows(), 1):
        print(f"{i}. {strategy}")
        print(f"   Score: {data['Score']}")
        print(f"   Win Rate: {data['Win_Rate']:.1f}%")
        print(f"   Avg PnL: ${data['Avg_PnL']:,.0f}")
        print(f"   Risk Ratio: {data['Risk_Ratio']:.2f}")
        print()
    
    # Рекомендации по рынку
    print("РЕКОМЕНДАЦИИ ПО РЫНОЧНЫМ УСЛОВИЯМ:")
    print("📈 Сильный тренд вверх: Bull Call Spread")
    print("📉 Сильный тренд вниз: Bear Put Spread") 
    print("📊 Высокая волатильность: Long Straddle")
    print("📏 Боковой рынок: Iron Condor")
    print("🎯 Точное попадание: Butterfly Spread")

if __name__ == "__main__":
    rank_strategies()
