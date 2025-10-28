#!/usr/bin/env python3
import pandas as pd
import requests

class RealisticTradingParams:
    def __init__(self):
        self.trading_rules = {
            'Bull Call Spread': {
                'take_profit': 0.25,  # 25% от max profit
                'stop_loss': 0.50,    # 50% от премии
                'max_loss_ratio': 0.3, # 30% от ширины спреда
                'time_exit': 21       # дней до экспирации
            },
            'Bear Put Spread': {
                'take_profit': 0.25,
                'stop_loss': 0.50,
                'max_loss_ratio': 0.3,
                'time_exit': 21
            },
            'Long Straddle': {
                'take_profit': 1.0,    # 100% от премии
                'stop_loss': 0.50,     # 50% убыток
                'premium_pct': 0.04,   # 4% реалистичная премия
                'time_exit': 21
            },
            'Iron Condor': {
                'take_profit': 0.25,   # 25% от кредита
                'stop_loss': 2.0,      # 200% от кредита
                'profit_range': 0.06,  # ±6% для прибыли
                'time_exit': 21
            }
        }
    
    def calculate_realistic_pnl(self, strategy, entry_price, exit_price, dte=45):
        """Реалистичный расчет P&L с правилами выхода"""
        
        rules = self.trading_rules[strategy]
        move_pct = (exit_price - entry_price) / entry_price
        
        if strategy == "Bull Call Spread":
            # Реалистичные страйки
            long_strike = entry_price * 0.97   # 3% ITM
            short_strike = entry_price * 1.08  # 8% OTM
            spread_width = short_strike - long_strike
            
            # Премии
            net_debit = spread_width * rules['max_loss_ratio']
            max_profit = spread_width - net_debit
            
            # Расчет P&L
            if exit_price <= long_strike:
                pnl = -net_debit
            elif exit_price >= short_strike:
                pnl = max_profit
            else:
                pnl = (exit_price - long_strike) - net_debit
            
            # Применяем правила выхода
            if pnl >= max_profit * rules['take_profit']:
                return max_profit * rules['take_profit']  # Take profit
            elif pnl <= -net_debit * rules['stop_loss']:
                return -net_debit * rules['stop_loss']    # Stop loss
            
            return pnl
        
        elif strategy == "Long Straddle":
            premium = entry_price * rules['premium_pct']
            raw_profit = abs(exit_price - entry_price) - premium
            
            # Take profit rule
            if raw_profit >= premium * rules['take_profit']:
                return premium * rules['take_profit']
            elif raw_profit <= -premium * rules['stop_loss']:
                return -premium * rules['stop_loss']
            
            return max(raw_profit, -premium)
        
        elif strategy == "Iron Condor":
            # Кредит от продажи
            credit = entry_price * 0.02  # 2% кредит
            
            if abs(move_pct) <= rules['profit_range']:
                profit = credit * rules['take_profit']
                return profit
            else:
                loss = credit * rules['stop_loss']
                return -loss
        
        return 0
    
    def run_realistic_backtest(self):
        """Бэктест с реалистичными правилами"""
        
        print("=== REALISTIC TRADING RULES BACKTEST ===")
        
        # Получаем текущие цены Bybit
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
        prices = {}
        
        for symbol in symbols:
            try:
                url = "https://api.bybit.com/v5/market/tickers"
                response = requests.get(url, params={'category': 'spot', 'symbol': symbol})
                if response.status_code == 200:
                    data = response.json()
                    if data['retCode'] == 0:
                        asset = symbol.replace('USDT', '')
                        prices[asset] = float(data['result']['list'][0]['lastPrice'])
            except:
                continue
        
        results = []
        strategies = ['Bull Call Spread', 'Long Straddle', 'Iron Condor']
        moves = [-15, -10, -8, -5, -3, -1, 0, 1, 3, 5, 8, 10, 15]  # Более детальные движения
        
        for asset, price in prices.items():
            print(f"\n{asset}: ${price:,.2f}")
            
            for strategy in strategies:
                rules = self.trading_rules[strategy]
                print(f"  {strategy}:")
                print(f"    Take Profit: {rules['take_profit']*100}%")
                print(f"    Stop Loss: {rules['stop_loss']*100}%")
                
                wins = 0
                total = 0
                total_pnl = 0
                
                for move_pct in moves:
                    new_price = price * (1 + move_pct/100)
                    pnl = self.calculate_realistic_pnl(strategy, price, new_price)
                    
                    results.append({
                        'asset': asset,
                        'strategy': strategy,
                        'move_pct': move_pct,
                        'pnl': pnl,
                        'profitable': pnl > 0
                    })
                    
                    if pnl > 0:
                        wins += 1
                    total += 1
                    total_pnl += pnl
                
                win_rate = (wins / total) * 100
                avg_pnl = total_pnl / total
                print(f"    Win Rate: {win_rate:.1f}% | Avg P&L: ${avg_pnl:.0f}")
        
        # Сохраняем результаты
        df = pd.DataFrame(results)
        df.to_csv('data/realistic_rules_backtest.csv', index=False)
        
        print(f"\n=== ОБЩАЯ СТАТИСТИКА ===")
        overall = df.groupby('strategy').agg({
            'profitable': 'mean',
            'pnl': 'mean'
        }) * [100, 1]
        
        for strategy, stats in overall.iterrows():
            print(f"{strategy}: {stats['profitable']:.1f}% win rate, ${stats['pnl']:.0f} avg")

if __name__ == "__main__":
    backtest = RealisticTradingParams()
    backtest.run_realistic_backtest()
