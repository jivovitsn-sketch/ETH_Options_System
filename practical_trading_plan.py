#!/usr/bin/env python3
import pandas as pd

def create_practical_plan():
    df = pd.read_csv('data/options_backtest_results.csv')
    
    # Находим реалистичные прибыльные стратегии
    realistic = df[
        (df['leveraged_profit'] > 0) & 
        (df['leveraged_profit'] < 100000) &  # Исключаем нереалистично высокие прибыли
        (df['leveraged_roi'] < 200)  # Исключаем нереалистичные ROI
    ]
    
    if len(realistic) > 0:
        # Топ стратегии
        top_strategies = realistic.groupby('strategy').agg({
            'leveraged_profit': 'mean',
            'leveraged_roi': 'mean',
            'price_move': 'count'
        }).sort_values('leveraged_profit', ascending=False)
        
        plan = """
# ПРАКТИЧЕСКИЙ ПЛАН ТОРГОВЛИ ОПЦИОНАМИ

## РЕКОМЕНДУЕМЫЕ СТРАТЕГИИ

"""
        
        for strategy, data in top_strategies.head(5).iterrows():
            best_setup = realistic[realistic['strategy'] == strategy].nlargest(1, 'leveraged_profit').iloc[0]
            
            plan += f"""
### {strategy}
- Средняя прибыль: ${data['leveraged_profit']:,.0f}
- Средний ROI: {data['leveraged_roi']:.1f}%
- Лучший сетап: {best_setup['price_move']}% движение, {best_setup['take_profit']}% TP
- Прибыль лучшего: ${best_setup['leveraged_profit']:,.0f}
"""
        
        plan += """
## ПРАВИЛА РИСК-МЕНЕДЖМЕНТА

### Размер позиции:
- Максимум 2% капитала на сделку
- Не более 3 одновременных позиций
- Стоп-лосс на уровне 50% от premium

### Выход из сделок:
- Take Profit: 50% от максимальной прибыли
- Time Stop: закрытие за 21 день до экспирации
- Delta hedge при сильном движении против

### Выбор стратегии по рынку:
- Trending market: Bull/Bear spreads
- Range market: Iron Condors, Butterflies
- High IV: Sell premium (Short Straddle)
- Low IV: Buy premium (Long Straddle)
"""
        
        with open('data/PRACTICAL_TRADING_PLAN.md', 'w') as f:
            f.write(plan)
        
        print("Практический план создан: data/PRACTICAL_TRADING_PLAN.md")
    
    else:
        print("Недостаточно реалистичных данных для плана")

if __name__ == "__main__":
    create_practical_plan()
