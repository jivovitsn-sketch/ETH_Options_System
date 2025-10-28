#!/usr/bin/env python3
import numpy as np
from scipy.stats import norm
import pandas as pd

class RealOptionsModel:
    def __init__(self):
        self.r = 0.05  # Risk-free rate
    
    def black_scholes_call(self, S, K, T, r, sigma):
        """Black-Scholes для колла"""
        d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        
        call_price = S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
        delta = norm.cdf(d1)
        gamma = norm.pdf(d1) / (S*sigma*np.sqrt(T))
        theta = -(S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(d2))
        vega = S*norm.pdf(d1)*np.sqrt(T)
        
        return {
            'price': call_price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta/365,  # Daily theta
            'vega': vega/100     # Per 1% IV change
        }
    
    def black_scholes_put(self, S, K, T, r, sigma):
        """Black-Scholes для пута"""
        d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        
        put_price = K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
        gamma = norm.pdf(d1) / (S*sigma*np.sqrt(T))
        theta = -(S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(-d2))
        vega = S*norm.pdf(d1)*np.sqrt(T)
        
        return {
            'price': put_price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta/365,  # Daily theta
            'vega': vega/100     # Per 1% IV change
        }
    
    def bull_call_spread_pnl(self, spot_entry, spot_exit, days_passed, iv_entry, iv_exit):
        """Bull Call Spread с реальными греками"""
        
        # Страйки
        long_strike = spot_entry * 0.97   # 3% ITM
        short_strike = spot_entry * 1.08  # 8% OTM
        
        # Время до экспирации
        dte_entry = 45/365
        dte_exit = (45 - days_passed)/365
        
        # Входные опционы
        long_call_entry = self.black_scholes_call(spot_entry, long_strike, dte_entry, self.r, iv_entry)
        short_call_entry = self.black_scholes_call(spot_entry, short_strike, dte_entry, self.r, iv_entry)
        entry_cost = long_call_entry['price'] - short_call_entry['price']
        
        # Выходные опционы
        long_call_exit = self.black_scholes_call(spot_exit, long_strike, dte_exit, self.r, iv_exit)
        short_call_exit = self.black_scholes_call(spot_exit, short_strike, dte_exit, self.r, iv_exit)
        exit_value = long_call_exit['price'] - short_call_exit['price']
        
        pnl = exit_value - entry_cost
        
        return {
            'pnl': pnl,
            'entry_cost': entry_cost,
            'exit_value': exit_value,
            'theta_impact': (long_call_exit['theta'] - short_call_exit['theta']) * days_passed,
            'vega_impact': (long_call_exit['vega'] - short_call_exit['vega']) * (iv_exit - iv_entry) * 100
        }
    
    def long_straddle_pnl(self, spot_entry, spot_exit, days_passed, iv_entry, iv_exit):
        """Long Straddle с тетой и вегой"""
        
        strike = spot_entry  # ATM
        dte_entry = 45/365
        dte_exit = (45 - days_passed)/365
        
        # Входные опционы
        call_entry = self.black_scholes_call(spot_entry, strike, dte_entry, self.r, iv_entry)
        put_entry = self.black_scholes_put(spot_entry, strike, dte_entry, self.r, iv_entry)
        entry_cost = call_entry['price'] + put_entry['price']
        
        # Выходные опционы
        call_exit = self.black_scholes_call(spot_exit, strike, dte_exit, self.r, iv_exit)
        put_exit = self.black_scholes_put(spot_exit, strike, dte_exit, self.r, iv_exit)
        exit_value = call_exit['price'] + put_exit['price']
        
        pnl = exit_value - entry_cost
        
        return {
            'pnl': pnl,
            'entry_cost': entry_cost,
            'exit_value': exit_value,
            'theta_decay': (call_exit['theta'] + put_exit['theta']) * days_passed,
            'vega_impact': (call_exit['vega'] + put_exit['vega']) * (iv_exit - iv_entry) * 100
        }
    
    def run_real_backtest(self):
        """Бэктест с РЕАЛЬНОЙ опционной моделью"""
        
        print("=== REAL OPTIONS BACKTEST (Greeks + Time Decay) ===")
        
        spot_prices = [70000, 4000, 200, 2.6]  # BTC, ETH, SOL, XRP
        assets = ['BTC', 'ETH', 'SOL', 'XRP']
        
        results = []
        
        for i, asset in enumerate(assets):
            spot = spot_prices[i]
            print(f"\n{asset}: ${spot:,.2f}")
            
            # Различные сценарии
            scenarios = [
                {'move': -10, 'days': 7, 'iv_change': 5},   # Падение + рост IV
                {'move': -5, 'days': 14, 'iv_change': 0},   # Небольшое падение
                {'move': 0, 'days': 21, 'iv_change': -10},  # Боковик + падение IV
                {'move': 5, 'days': 14, 'iv_change': 0},    # Небольшой рост
                {'move': 10, 'days': 7, 'iv_change': 5},    # Рост + рост IV
                {'move': 15, 'days': 3, 'iv_change': 10}    # Сильный рост
            ]
            
            for scenario in scenarios:
                new_spot = spot * (1 + scenario['move']/100)
                iv_entry = 0.8  # 80% входная IV
                iv_exit = iv_entry + scenario['iv_change']/100
                
                # Bull Call Spread
                bcs = self.bull_call_spread_pnl(spot, new_spot, scenario['days'], iv_entry, iv_exit)
                
                # Long Straddle  
                ls = self.long_straddle_pnl(spot, new_spot, scenario['days'], iv_entry, iv_exit)
                
                results.append({
                    'asset': asset,
                    'strategy': 'Bull Call Spread',
                    'move_pct': scenario['move'],
                    'days': scenario['days'],
                    'iv_change': scenario['iv_change'],
                    'pnl': bcs['pnl'] * spot / 1000,  # Нормализуем
                    'theta_impact': bcs['theta_impact'] * spot / 1000,
                    'profitable': bcs['pnl'] > 0
                })
                
                results.append({
                    'asset': asset,
                    'strategy': 'Long Straddle',
                    'move_pct': scenario['move'],
                    'days': scenario['days'],
                    'iv_change': scenario['iv_change'],
                    'pnl': ls['pnl'] * spot / 1000,  # Нормализуем
                    'theta_impact': ls['theta_decay'] * spot / 1000,
                    'profitable': ls['pnl'] > 0
                })
        
        df = pd.DataFrame(results)
        
        # Анализ
        strategy_stats = df.groupby('strategy').agg({
            'profitable': 'mean',
            'pnl': 'mean',
            'theta_impact': 'mean'
        }).round(3)
        
        print(f"\n=== РЕАЛЬНЫЕ ОПЦИОННЫЕ РЕЗУЛЬТАТЫ ===")
        for strategy, stats in strategy_stats.iterrows():
            print(f"{strategy}:")
            print(f"  Win Rate: {stats['profitable']*100:.1f}%")
            print(f"  Avg P&L: ${stats['pnl']:,.0f}")
            print(f"  Theta Impact: ${stats['theta_impact']:,.0f}")
        
        df.to_csv('data/real_options_backtest.csv', index=False)
        print(f"\nРеальные опционные результаты: data/real_options_backtest.csv")

if __name__ == "__main__":
    model = RealOptionsModel()
    model.run_real_backtest()
