#!/usr/bin/env python3
import requests
import pandas as pd

class CorrectOptionsBacktest:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        
        # ПРАВИЛЬНЫЕ опционные параметры
        self.asset_configs = {
            'BTC': {
                'symbol': 'BTCUSDT',
                'exp': '14NOV25',
                'exit_rules': [
                    {'type': 'take_profit_pct', 'value': 25},  # 25% от макс прибыли
                    {'type': 'take_profit_pct', 'value': 50},  # 50% от макс прибыли
                    {'type': 'take_profit_dollars', 'value': 200},  # $200 прибыль
                    {'type': 'hold_to_expiry', 'value': None}   # Держать до конца
                ],
                'move_scenarios': [-12, -8, -5, -2, 0, 2, 5, 8, 12],
                'time_scenarios': [3, 7, 14, 21]  # Дней до продажи
            },
            'ETH': {
                'symbol': 'ETHUSDT',
                'exp': '14NOV25', 
                'exit_rules': [
                    {'type': 'take_profit_pct', 'value': 30},
                    {'type': 'take_profit_pct', 'value': 60},
                    {'type': 'take_profit_dollars', 'value': 100},
                    {'type': 'hold_to_expiry', 'value': None}
                ],
                'move_scenarios': [-15, -10, -6, -3, 0, 3, 6, 10, 15],
                'time_scenarios': [3, 7, 14, 21]
            }
        }
    
    def calculate_option_pnl_at_time(self, strategy, entry_data, new_spot, days_passed):
        """Расчет P&L опциона в определенное время (не на экспирации)"""
        
        if strategy == "Bull Call Spread":
            long_strike = entry_data['long_strike']
            short_strike = entry_data['short_strike']
            entry_cost = entry_data['entry_cost']
            
            # Приблизительная стоимость спреда в зависимости от спота и времени
            # (упрощенная модель без Black-Scholes)
            
            if new_spot <= long_strike:
                # Полностью OTM
                current_value = entry_cost * 0.1  # Остаточная стоимость
            elif new_spot >= short_strike:
                # Полностью ITM
                max_profit = short_strike - long_strike - entry_cost
                time_decay = 1 - (days_passed / 45)  # Линейное убывание времени
                current_value = entry_cost + max_profit * (0.7 + 0.3 * time_decay)
            else:
                # Между страйками
                intrinsic = new_spot - long_strike
                time_value = (45 - days_passed) / 45 * entry_cost * 0.3
                current_value = intrinsic + time_value
            
            pnl = current_value - entry_cost
            return pnl
        
        elif strategy == "Long Straddle":
            strike = entry_data['strike']
            entry_cost = entry_data['entry_cost']
            
            # Стрэддл зависит от расстояния от страйка
            movement = abs(new_spot - strike)
            time_decay = (45 - days_passed) / 45
            
            # Упрощенная модель: движение минус временной распад
            current_value = movement + entry_cost * time_decay * 0.5
            pnl = current_value - entry_cost
            
            return pnl
    
    def apply_exit_rule(self, current_pnl, max_profit, entry_cost, exit_rule):
        """Применяем правило выхода"""
        
        if exit_rule['type'] == 'take_profit_pct':
            target = max_profit * (exit_rule['value'] / 100)
            if current_pnl >= target:
                return target, f"TP_{exit_rule['value']}%"
        
        elif exit_rule['type'] == 'take_profit_dollars':
            if current_pnl >= exit_rule['value']:
                return exit_rule['value'], f"TP_${exit_rule['value']}"
        
        elif exit_rule['type'] == 'hold_to_expiry':
            # На экспирации
            return current_pnl, "expiry"
        
        # Если правило не сработало - держим
        return None, "hold"
    
    def test_asset_correct(self, asset, config):
        """Правильный тест опционов без стоп-лоссов"""
        
        spot_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                   params={'category': 'spot', 'symbol': config['symbol']})
        spot_price = float(spot_response.json()['result']['list'][0]['lastPrice'])
        
        print(f"Testing {asset}: ${spot_price:,.2f}")
        
        results = []
        
        # Тестируем Bull Call Spread
        base_strike = round(spot_price / 1000) * 1000 if asset == 'BTC' else round(spot_price / 100) * 100
        long_strike = base_strike
        short_strike = base_strike + (1000 if asset == 'BTC' else 100)
        
        # Получаем реальные цены
        long_symbol = f"{asset}-{config['exp']}-{int(long_strike)}-C-USDT"
        short_symbol = f"{asset}-{config['exp']}-{int(short_strike)}-C-USDT"
        
        try:
            long_response = requests.get(f"{self.base_url}/v5/market/tickers",
                                       params={'category': 'option', 'symbol': long_symbol})
            short_response = requests.get(f"{self.base_url}/v5/market/tickers", 
                                        params={'category': 'option', 'symbol': short_symbol})
            
            long_data = long_response.json()['result']['list'][0]
            short_data = short_response.json()['result']['list'][0]
            
            entry_cost = float(long_data['ask1Price']) - float(short_data['bid1Price'])
            max_profit = (short_strike - long_strike) - entry_cost
            
            if entry_cost <= 0:
                return results
            
            entry_data = {
                'long_strike': long_strike,
                'short_strike': short_strike,
                'entry_cost': entry_cost
            }
            
            # Тестируем сценарии
            for move_pct in config['move_scenarios']:
                for days in config['time_scenarios']:
                    for exit_rule in config['exit_rules']:
                        
                        new_spot = spot_price * (1 + move_pct/100)
                        
                        if exit_rule['type'] == 'hold_to_expiry':
                            # P&L на экспирации
                            if new_spot <= long_strike:
                                final_pnl = -entry_cost
                            elif new_spot >= short_strike:
                                final_pnl = max_profit
                            else:
                                final_pnl = (new_spot - long_strike) - entry_cost
                            exit_reason = "expiry"
                        else:
                            # P&L в промежуточное время
                            current_pnl = self.calculate_option_pnl_at_time(
                                "Bull Call Spread", entry_data, new_spot, days
                            )
                            
                            final_pnl, exit_reason = self.apply_exit_rule(
                                current_pnl, max_profit, entry_cost, exit_rule
                            )
                            
                            if final_pnl is None:
                                final_pnl = current_pnl
                                exit_reason = "hold"
                        
                        results.append({
                            'asset': asset,
                            'strategy': 'Bull Call Spread',
                            'entry_cost': entry_cost,
                            'max_profit': max_profit,
                            'move_pct': move_pct,
                            'days': days,
                            'exit_rule': exit_rule['type'],
                            'exit_value': exit_rule['value'],
                            'final_pnl': final_pnl,
                            'exit_reason': exit_reason,
                            'roi': (final_pnl / entry_cost) * 100,
                            'profitable': final_pnl > 0
                        })
            
        except Exception as e:
            print(f"Error testing {asset}: {e}")
        
        return results
    
    def run_correct_backtest(self):
        """Запуск правильного опционного бэктеста"""
        
        print("=== CORRECT OPTIONS BACKTEST (No Stop Losses) ===")
        
        all_results = []
        
        for asset, config in self.asset_configs.items():
            asset_results = self.test_asset_correct(asset, config)
            all_results.extend(asset_results)
            print(f"{asset}: {len(asset_results)} scenarios")
        
        if all_results:
            df = pd.DataFrame(all_results)
            df.to_csv('data/correct_options_backtest.csv', index=False)
            
            # Анализ
            print(f"\n=== CORRECT ANALYSIS ===")
            print(f"Overall win rate: {df['profitable'].mean()*100:.1f}%")
            
            # Лучшие правила выхода
            exit_performance = df.groupby(['exit_rule', 'exit_value']).agg({
                'profitable': 'mean',
                'roi': 'mean'
            }).round(2)
            
            print(f"\nBest exit rules:")
            for (rule, value), data in exit_performance.sort_values('profitable', ascending=False).head(5).iterrows():
                print(f"{rule} {value}: {data['profitable']*100:.1f}% win rate, {data['roi']:.1f}% ROI")

if __name__ == "__main__":
    backtest = CorrectOptionsBacktest()
    backtest.run_correct_backtest()
