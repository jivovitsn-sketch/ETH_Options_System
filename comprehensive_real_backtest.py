#!/usr/bin/env python3
import requests
import pandas as pd
import time
from datetime import datetime
import numpy as np

class ComprehensiveRealBacktest:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.assets = {
            'BTC': {'symbol': 'BTCUSDT', 'exp': '14NOV25'},
            'ETH': {'symbol': 'ETHUSDT', 'exp': '14NOV25'},
            'SOL': {'symbol': 'SOLUSDT', 'exp': '14NOV25'},
            'XRP': {'symbol': 'XRPUSDT', 'exp': '14NOV25'}
        }
        
        # Правила торговли
        self.trading_rules = {
            'take_profit_levels': [0.25, 0.50, 0.75, 1.0],  # 25%, 50%, 75%, 100% от макс прибыли
            'stop_loss_levels': [0.25, 0.50, 0.75],         # 25%, 50%, 75% от входа
            'time_exits': [7, 14, 21, 30],                   # Дней до принудительного закрытия
            'scenarios': [
                {'move': -15, 'days': 7, 'iv_change': 5},
                {'move': -10, 'days': 14, 'iv_change': 0},
                {'move': -5, 'days': 21, 'iv_change': -5},
                {'move': 0, 'days': 30, 'iv_change': -10},
                {'move': 5, 'days': 21, 'iv_change': -5},
                {'move': 10, 'days': 14, 'iv_change': 0},
                {'move': 15, 'days': 7, 'iv_change': 5}
            ]
        }
    
    def get_spot_price(self, symbol):
        """Получаем спот цену"""
        try:
            response = requests.get(f"{self.base_url}/v5/market/tickers",
                                  params={'category': 'spot', 'symbol': symbol})
            if response.status_code == 200:
                data = response.json()
                return float(data['result']['list'][0]['lastPrice'])
        except:
            pass
        return None
    
    def get_option_price(self, symbol):
        """Получаем цену опциона"""
        try:
            response = requests.get(f"{self.base_url}/v5/market/tickers",
                                  params={'category': 'option', 'symbol': symbol})
            if response.status_code == 200:
                data = response.json()
                if data['retCode'] == 0 and data['result']['list']:
                    option_data = data['result']['list'][0]
                    return {
                        'bid': float(option_data['bid1Price']),
                        'ask': float(option_data['ask1Price']),
                        'last': float(option_data['lastPrice']),
                        'volume': float(option_data['volume24h']) if option_data['volume24h'] else 0,
                        'oi': float(option_data['openInterest']) if option_data['openInterest'] else 0
                    }
        except Exception as e:
            print(f"Error getting {symbol}: {e}")
        return None
    
    def get_atm_strikes(self, asset, spot_price):
        """Определяем ATM страйки для актива"""
        if asset == 'BTC':
            base_strike = round(spot_price / 1000) * 1000
            strikes = [base_strike - 2000, base_strike - 1000, base_strike, 
                      base_strike + 1000, base_strike + 2000]
        elif asset == 'ETH':
            base_strike = round(spot_price / 100) * 100
            strikes = [base_strike - 200, base_strike - 100, base_strike,
                      base_strike + 100, base_strike + 200]
        elif asset == 'SOL':
            base_strike = round(spot_price / 10) * 10
            strikes = [base_strike - 20, base_strike - 10, base_strike,
                      base_strike + 10, base_strike + 20]
        else:  # XRP
            base_strike = round(spot_price * 2) / 2  # Округляем до 0.5
            strikes = [base_strike - 1, base_strike - 0.5, base_strike,
                      base_strike + 0.5, base_strike + 1]
        
        return strikes
    
    def test_bull_call_spread(self, asset, spot_price, strikes, exp):
        """Тестируем Bull Call Spread с реальными ценами"""
        results = []
        
        for i in range(len(strikes)-1):
            long_strike = strikes[i]
            short_strike = strikes[i+1]
            
            # Получаем реальные цены опционов
            long_symbol = f"{asset}-{exp}-{int(long_strike)}-C-USDT"
            short_symbol = f"{asset}-{exp}-{int(short_strike)}-C-USDT"
            
            long_option = self.get_option_price(long_symbol)
            short_option = self.get_option_price(short_symbol)
            
            if not long_option or not short_option:
                continue
            
            # Входная стоимость (покупаем по ask, продаем по bid)
            entry_cost = long_option['ask'] - short_option['bid']
            
            if entry_cost <= 0:
                continue
            
            # Максимальная прибыль
            max_profit = (short_strike - long_strike) - entry_cost
            
            # Тестируем различные правила выхода
            for tp_level in self.trading_rules['take_profit_levels']:
                for sl_level in self.trading_rules['stop_loss_levels']:
                    for scenario in self.trading_rules['scenarios']:
                        
                        # Симулируем движение цены
                        new_spot = spot_price * (1 + scenario['move']/100)
                        
                        # Расчет P&L
                        if new_spot <= long_strike:
                            pnl = -entry_cost
                        elif new_spot >= short_strike:
                            pnl = max_profit
                        else:
                            pnl = (new_spot - long_strike) - entry_cost
                        
                        # Применяем правила выхода
                        tp_target = max_profit * tp_level
                        sl_target = -entry_cost * sl_level
                        
                        final_pnl = pnl
                        exit_reason = "expiry"
                        
                        if pnl >= tp_target:
                            final_pnl = tp_target
                            exit_reason = "take_profit"
                        elif pnl <= sl_target:
                            final_pnl = sl_target
                            exit_reason = "stop_loss"
                        
                        results.append({
                            'asset': asset,
                            'strategy': 'Bull Call Spread',
                            'long_strike': long_strike,
                            'short_strike': short_strike,
                            'entry_cost': entry_cost,
                            'max_profit': max_profit,
                            'spot_move': scenario['move'],
                            'days_held': scenario['days'],
                            'tp_level': tp_level,
                            'sl_level': sl_level,
                            'final_pnl': final_pnl,
                            'roi': (final_pnl / entry_cost) * 100,
                            'exit_reason': exit_reason,
                            'profitable': final_pnl > 0,
                            'volume': long_option['volume'] + short_option['volume'],
                            'total_oi': long_option['oi'] + short_option['oi']
                        })
            
            time.sleep(0.1)  # Не спамим API
        
        return results
    
    def test_long_straddle(self, asset, spot_price, strikes, exp):
        """Тестируем Long Straddle с реальными ценами"""
        results = []
        
        # Используем ATM страйк
        atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
        
        call_symbol = f"{asset}-{exp}-{int(atm_strike)}-C-USDT"
        put_symbol = f"{asset}-{exp}-{int(atm_strike)}-P-USDT"
        
        call_option = self.get_option_price(call_symbol)
        put_option = self.get_option_price(put_symbol)
        
        if not call_option or not put_option:
            return results
        
        # Входная стоимость (покупаем оба по ask)
        entry_cost = call_option['ask'] + put_option['ask']
        
        for tp_level in self.trading_rules['take_profit_levels']:
            for sl_level in self.trading_rules['stop_loss_levels']:
                for scenario in self.trading_rules['scenarios']:
                    
                    new_spot = spot_price * (1 + scenario['move']/100)
                    
                    # P&L = |движение| - премия
                    movement = abs(new_spot - atm_strike)
                    pnl = movement - entry_cost
                    
                    # Правила выхода для стрэддла
                    tp_target = entry_cost * tp_level  # TP как % от премии
                    sl_target = -entry_cost * sl_level
                    
                    final_pnl = pnl
                    exit_reason = "expiry"
                    
                    if pnl >= tp_target:
                        final_pnl = tp_target
                        exit_reason = "take_profit"
                    elif pnl <= sl_target:
                        final_pnl = sl_target
                        exit_reason = "stop_loss"
                    
                    results.append({
                        'asset': asset,
                        'strategy': 'Long Straddle',
                        'strike': atm_strike,
                        'entry_cost': entry_cost,
                        'spot_move': scenario['move'],
                        'days_held': scenario['days'],
                        'tp_level': tp_level,
                        'sl_level': sl_level,
                        'final_pnl': final_pnl,
                        'roi': (final_pnl / entry_cost) * 100,
                        'exit_reason': exit_reason,
                        'profitable': final_pnl > 0,
                        'volume': call_option['volume'] + put_option['volume'],
                        'total_oi': call_option['oi'] + put_option['oi']
                    })
        
        return results
    
    def run_comprehensive_backtest(self):
        """Запуск полного бэктеста"""
        
        print("=== COMPREHENSIVE REAL BYBIT BACKTEST ===")
        print(f"Start: {datetime.now().strftime('%H:%M:%S')}")
        
        all_results = []
        
        for asset_name, asset_config in self.assets.items():
            print(f"\nTesting {asset_name}...")
            
            # Получаем спот цену
            spot_price = self.get_spot_price(asset_config['symbol'])
            if not spot_price:
                print(f"  No spot price for {asset_name}")
                continue
            
            print(f"  Spot: ${spot_price:,.2f}")
            
            # Определяем ATM страйки
            strikes = self.get_atm_strikes(asset_name, spot_price)
            
            # Тестируем Bull Call Spreads
            print(f"  Testing Bull Call Spreads...")
            bcs_results = self.test_bull_call_spread(asset_name, spot_price, strikes, asset_config['exp'])
            all_results.extend(bcs_results)
            
            # Тестируем Long Straddles
            print(f"  Testing Long Straddles...")
            ls_results = self.test_long_straddle(asset_name, spot_price, strikes, asset_config['exp'])
            all_results.extend(ls_results)
            
            print(f"  {asset_name} completed: {len(bcs_results + ls_results)} scenarios")
        
        # Сохраняем результаты
        df = pd.DataFrame(all_results)
        df.to_csv('data/comprehensive_real_backtest.csv', index=False)
        
        # Анализ результатов
        self.analyze_results(df)
        
        print(f"\nBacktest completed: {len(all_results)} total scenarios")
        print(f"Results saved: data/comprehensive_real_backtest.csv")
        
        return df
    
    def analyze_results(self, df):
        """Анализ результатов бэктеста"""
        
        print(f"\n=== COMPREHENSIVE ANALYSIS ===")
        
        # Общая статистика
        total_scenarios = len(df)
        profitable = len(df[df['profitable'] == True])
        
        print(f"Total scenarios: {total_scenarios:,}")
        print(f"Profitable: {profitable:,} ({profitable/total_scenarios*100:.1f}%)")
        
        # По стратегиям
        print(f"\nBY STRATEGY:")
        strategy_stats = df.groupby('strategy').agg({
            'profitable': ['count', 'sum', 'mean'],
            'roi': 'mean',
            'final_pnl': 'mean'
        }).round(2)
        
        for strategy in df['strategy'].unique():
            data = strategy_stats.loc[strategy]
            total = data[('profitable', 'count')]
            wins = data[('profitable', 'sum')]
            win_rate = data[('profitable', 'mean')] * 100
            avg_roi = data[('roi', 'mean')]
            avg_pnl = data[('final_pnl', 'mean')]
            
            print(f"  {strategy}: {win_rate:.1f}% win rate ({wins}/{total})")
            print(f"    Avg ROI: {avg_roi:.1f}%, Avg P&L: ${avg_pnl:.0f}")
        
        # По активам
        print(f"\nBY ASSET:")
        for asset in df['asset'].unique():
            asset_data = df[df['asset'] == asset]
            win_rate = asset_data['profitable'].mean() * 100
            avg_roi = asset_data['roi'].mean()
            print(f"  {asset}: {win_rate:.1f}% win rate, {avg_roi:.1f}% avg ROI")
        
        # Лучшие настройки
        print(f"\nBEST SETTINGS:")
        best_combo = df.groupby(['strategy', 'tp_level', 'sl_level']).agg({
            'profitable': 'mean',
            'roi': 'mean',
            'final_pnl': 'mean'
        }).round(2)
        
        best_combo = best_combo.sort_values('profitable', ascending=False)
        
        print("Top 5 combinations by win rate:")
        for i, (index, data) in enumerate(best_combo.head(5).iterrows()):
            strategy, tp, sl = index
            print(f"  {i+1}. {strategy} | TP:{tp*100:.0f}% | SL:{sl*100:.0f}%")
            print(f"     Win Rate: {data['profitable']*100:.1f}%, ROI: {data['roi']:.1f}%")

if __name__ == "__main__":
    backtest = ComprehensiveRealBacktest()
    backtest.run_comprehensive_backtest()
