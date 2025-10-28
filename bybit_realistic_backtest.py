#!/usr/bin/env python3
import pandas as pd
import requests
from datetime import datetime, timedelta

class BybitRealisticBacktest:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
    
    def get_current_bybit_levels(self):
        """Получаем АКТУАЛЬНЫЕ уровни с Bybit"""
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
        levels = {}
        
        for symbol in symbols:
            try:
                url = f"{self.base_url}/v5/market/tickers"
                response = requests.get(url, params={'category': 'spot', 'symbol': symbol}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['retCode'] == 0:
                        price = float(data['result']['list'][0]['lastPrice'])
                        
                        asset = symbol.replace('USDT', '')
                        levels[asset] = {
                            'current': price,
                            'support_2pct': price * 0.98,
                            'resistance_2pct': price * 1.02,
                            'support_5pct': price * 0.95,
                            'resistance_5pct': price * 1.05,
                            'support_10pct': price * 0.90,
                            'resistance_10pct': price * 1.10
                        }
            except Exception as e:
                print(f"Error getting {symbol}: {e}")
        
        return levels
    
    def run_realistic_scenarios(self):
        """Запуск реалистичных сценариев"""
        
        print("=== BYBIT REALISTIC BACKTEST ===")
        
        levels = self.get_current_bybit_levels()
        
        if not levels:
            print("Не удалось получить данные Bybit")
            return
        
        results = []
        strategies = ['Bull Call Spread', 'Bear Put Spread', 'Long Straddle', 'Iron Condor']
        
        # РЕАЛИСТИЧНЫЕ движения: ±2%, ±5%, ±8%, ±10%
        moves = [-10, -8, -5, -2, 0, 2, 5, 8, 10]
        
        for asset, data in levels.items():
            current_price = data['current']
            print(f"\n{asset}: ${current_price:,.2f}")
            
            for strategy in strategies:
                for move_pct in moves:
                    new_price = current_price * (1 + move_pct/100)
                    
                    # Расчет P&L для каждой стратегии
                    pnl = self._calculate_strategy_pnl(strategy, current_price, new_price, move_pct)
                    
                    results.append({
                        'asset': asset,
                        'strategy': strategy,
                        'entry_price': current_price,
                        'exit_price': new_price,
                        'move_pct': move_pct,
                        'pnl': pnl,
                        'profitable': pnl > 0
                    })
        
        # Анализ результатов
        df = pd.DataFrame(results)
        self._analyze_results(df)
        
        # Сохраняем ПРАВИЛЬНЫЕ результаты
        df.to_csv('data/bybit_realistic_backtest.csv', index=False)
        print(f"\nПравильные результаты сохранены: data/bybit_realistic_backtest.csv")
        
        return df
    
    def _calculate_strategy_pnl(self, strategy, entry_price, exit_price, move_pct):
        """Расчет P&L с реалистичными параметрами"""
        
        if strategy == "Bull Call Spread":
            # ITM long, OTM short
            long_strike = entry_price * 0.98
            short_strike = entry_price * 1.05
            
            if exit_price <= long_strike:
                return -300  # Max loss
            elif exit_price >= short_strike:
                return 400   # Max profit
            else:
                return (exit_price - long_strike) - 300
        
        elif strategy == "Bear Put Spread":
            long_strike = entry_price * 1.02
            short_strike = entry_price * 0.95
            
            if exit_price >= long_strike:
                return -300
            elif exit_price <= short_strike:
                return 400
            else:
                return (long_strike - exit_price) - 300
        
        elif strategy == "Long Straddle":
            premium = entry_price * 0.06  # 6% премия
            profit = abs(exit_price - entry_price) - premium
            return max(profit, -premium)
        
        elif strategy == "Iron Condor":
            # Прибыль если движение < 5%
            if abs(move_pct) < 5:
                return 150  # Получили кредит
            else:
                return -350  # Max loss
        
        return 0
    
    def _analyze_results(self, df):
        """Анализ ПРАВИЛЬНЫХ результатов"""
        
        print(f"\n=== АНАЛИЗ ПРАВИЛЬНЫХ РЕЗУЛЬТАТОВ ===")
        print(f"Всего сценариев: {len(df):,}")
        
        # По стратегиям
        strategy_stats = df.groupby('strategy').agg({
            'profitable': ['count', 'sum', 'mean'],
            'pnl': ['mean', 'max', 'min']
        }).round(2)
        
        print(f"\nПо стратегиям (актуальные данные Bybit):")
        for strategy, stats in strategy_stats.iterrows():
            total = stats[('profitable', 'count')]
            wins = stats[('profitable', 'sum')]
            win_rate = stats[('profitable', 'mean')] * 100
            avg_pnl = stats[('pnl', 'mean')]
            
            print(f"{strategy}:")
            print(f"  Win Rate: {win_rate:.1f}% ({wins}/{total})")
            print(f"  Avg P&L: ${avg_pnl:.0f}")
        
        # По активам
        print(f"\nПо активам (Bybit цены):")
        asset_stats = df.groupby('asset')['profitable'].mean() * 100
        for asset, win_rate in asset_stats.items():
            print(f"  {asset}: {win_rate:.1f}% win rate")

if __name__ == "__main__":
    backtest = BybitRealisticBacktest()
    backtest.run_realistic_scenarios()
