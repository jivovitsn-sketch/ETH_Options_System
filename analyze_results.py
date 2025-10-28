import pandas as pd

df = pd.read_csv('data/real_options_backtest.csv')

print('=== ИТОГОВЫЙ АНАЛИЗ ОПЦИОННОГО БЭКТЕСТА ===')
print(f'Всего сценариев: {len(df)}')

print('\nBull Call Spread результаты:')
bcs = df[df['strategy'] == 'Bull Call Spread']
for _, row in bcs.iterrows():
    print(f'{row["asset"]} {row["move_pct"]}% {row["days"]}d: P&L ${row["pnl"]:,.0f}')

print('\nLong Straddle + theta decay:')
ls = df[df['strategy'] == 'Long Straddle']
avg_theta_per_day = ls['theta_impact'].mean() / ls['days'].mean()
print(f'Средние theta потери за день: ${avg_theta_per_day:,.0f}')

print('\n=== РЕАЛЬНЫЕ РАЗМЕРЫ ПОЗИЦИЙ ===')
capital = 50000
position_pct = 0.03
position_size = capital * position_pct

print(f'Капитал: ${capital:,}')
print(f'Размер позиции (3%): ${position_size:,}')

# Bull Call Spread
bcs_cost = 500  # Типичная стоимость
bcs_contracts = position_size / bcs_cost
print(f'Bull Call Spread: {bcs_contracts:.0f} контрактов')

# Long Straddle BTC
straddle_cost = 70000 * 0.06  # 6% от BTC
straddle_contracts = position_size / straddle_cost
print(f'Long Straddle BTC: {straddle_contracts:.1f} контрактов')
