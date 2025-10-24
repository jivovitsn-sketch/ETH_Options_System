#!/usr/bin/env python3
"""
SMART OPTIONS BACKTEST
- Выход по противоположному сигналу
- Расчет временной стоимости при выходе
- Не ждем экспирации
- Theta decay учтен
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import ast
import numpy as np
from itertools import product
from indicators.smart_money.order_blocks import OrderBlocks

class SmartOptionsBacktest:
    def __init__(self):
        self.ob = OrderBlocks()
        self.commission = 0.0003  # 0.03% per side × 4 legs = 0.12% total
        
        print("✅ Smart Options Backtest initialized")
        print("   - Exit on opposite signal")
        print("   - Time value captured")
        print("   - Commission: 0.12% total")
    
    def load_data(self, asset: str, currency: str):
        """Load spot + options"""
        # Spot
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / asset
        files = sorted(data_dir.glob("*.csv"))
        
        if not files:
            return None, None
        
        dfs = [pd.read_csv(f) for f in files[-100:]]
        df = pd.concat(dfs, ignore_index=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        df = df.resample('4h').agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }).dropna()
        df.reset_index(inplace=True)
        
        df = self.ob.find_order_blocks(df)
        
        # Options
        opts_dir = Path(__file__).parent.parent / 'data' / 'options_history' / currency
        opts_files = sorted(opts_dir.glob("*.csv"))
        
        if not opts_files:
            return df, None
        
        opts = pd.read_csv(opts_files[-1])
        
        def parse_greeks(g):
            if pd.isna(g): return {}
            try: return ast.literal_eval(g)
            except: return {}
        
        opts['greeks_dict'] = opts['greeks'].apply(parse_greeks)
        opts['delta'] = opts['greeks_dict'].apply(lambda x: x.get('delta', 0))
        opts['theta'] = opts['greeks_dict'].apply(lambda x: x.get('theta', 0))
        opts['vega'] = opts['greeks_dict'].apply(lambda x: x.get('vega', 0))
        opts['dte'] = (pd.to_datetime(opts['expiration'], unit='ms') - pd.Timestamp.now()).dt.days
        
        return df, opts
    
    def find_strategy(self, spot: float, opts: pd.DataFrame, strategy: str, dte_target: int):
        """Find option strategy"""
        valid = opts[(opts['dte'] >= dte_target-5) & (opts['dte'] <= dte_target+5)]
        
        if len(valid) < 2:
            return None
        
        if strategy == 'bull_call':
            calls = valid[valid['option_type'] == 'call']
            if len(calls) < 2: return None
            
            atm = calls.iloc[(calls['strike'] - spot).abs().argsort()[:1]]
            otm = calls.iloc[(calls['strike'] - spot*1.05).abs().argsort()[:1]]
            
            if len(atm) > 0 and len(otm) > 0:
                buy_cost = atm['mark_price'].iloc[0]
                sell_credit = otm['mark_price'].iloc[0]
                net_cost = buy_cost - sell_credit
                
                return {
                    'type': 'bull_call',
                    'entry_spot': spot,
                    'lower': atm['strike'].iloc[0],
                    'upper': otm['strike'].iloc[0],
                    'net_cost': net_cost,
                    'buy_price': buy_cost,
                    'sell_price': sell_credit,
                    'dte_entry': int(atm['dte'].iloc[0]),
                    'net_delta': atm['delta'].iloc[0] - otm['delta'].iloc[0],
                    'net_theta': atm['theta'].iloc[0] - otm['theta'].iloc[0],
                    'max_profit': (otm['strike'].iloc[0] - atm['strike'].iloc[0]) / spot
                }
        
        elif strategy == 'bear_put':
            puts = valid[valid['option_type'] == 'put']
            if len(puts) < 2: return None
            
            atm = puts.iloc[(puts['strike'] - spot).abs().argsort()[:1]]
            otm = puts.iloc[(puts['strike'] - spot*0.95).abs().argsort()[:1]]
            
            if len(atm) > 0 and len(otm) > 0:
                buy_cost = atm['mark_price'].iloc[0]
                sell_credit = otm['mark_price'].iloc[0]
                net_cost = buy_cost - sell_credit
                
                return {
                    'type': 'bear_put',
                    'entry_spot': spot,
                    'upper': atm['strike'].iloc[0],
                    'lower': otm['strike'].iloc[0],
                    'net_cost': net_cost,
                    'buy_price': buy_cost,
                    'sell_price': sell_credit,
                    'dte_entry': int(atm['dte'].iloc[0]),
                    'max_profit': (atm['strike'].iloc[0] - otm['strike'].iloc[0]) / spot
                }
        
        return None
    
    def calc_exit_value(self, strat: dict, exit_spot: float, periods_held: int):
        """
        Calculate exit value with time value
        
        Value = Intrinsic Value + Time Value
        Time Value decays with Theta
        """
        dte_remaining = strat['dte_entry'] - (periods_held / 6)  # 4h periods -> days
        
        if dte_remaining < 0:
            dte_remaining = 0
        
        if strat['type'] == 'bull_call':
            # Intrinsic value
            if exit_spot <= strat['lower']:
                intrinsic = 0
            elif exit_spot >= strat['upper']:
                intrinsic = strat['max_profit']
            else:
                intrinsic = (exit_spot - strat['lower']) / strat['entry_spot']
            
            # Time value (decays to 0 at expiration)
            time_value = strat['net_cost'] * (dte_remaining / strat['dte_entry'])
            
            # If in-the-money, time value is smaller
            if exit_spot > strat['lower']:
                time_value *= 0.5
            
            total_value = intrinsic + time_value
            pnl = total_value - strat['net_cost']
            
            return pnl
        
        elif strat['type'] == 'bear_put':
            # Intrinsic value
            if exit_spot >= strat['upper']:
                intrinsic = 0
            elif exit_spot <= strat['lower']:
                intrinsic = strat['max_profit']
            else:
                intrinsic = (strat['upper'] - exit_spot) / strat['entry_spot']
            
            # Time value
            time_value = strat['net_cost'] * (dte_remaining / strat['dte_entry'])
            
            if exit_spot < strat['upper']:
                time_value *= 0.5
            
            total_value = intrinsic + time_value
            pnl = total_value - strat['net_cost']
            
            return pnl
        
        return 0
    
    def test_combo(self, asset: str, currency: str, strategy: str, dte: int, take_profit: float):
        """Test one combination"""
        
        spot_df, opts_df = self.load_data(asset, currency)
        
        if spot_df is None or opts_df is None:
            return None
        
        capital = 10000
        position = None
        trades = []
        
        for i in range(100, len(spot_df)-5):
            price = spot_df.iloc[i]['close']
            
            # Check exit conditions
            if position:
                periods_held = i - position['idx']
                
                # Exit reasons:
                # 1. Opposite signal
                opposite_signal = False
                if strategy == 'bull_call' and spot_df.iloc[i]['bearish_ob']:
                    opposite_signal = True
                elif strategy == 'bear_put' and spot_df.iloc[i]['bullish_ob']:
                    opposite_signal = True
                
                # 2. Near expiration (90% of DTE)
                near_expiry = periods_held >= (dte / 4) * 0.9
                
                # 3. Take profit hit
                pnl_pct = self.calc_exit_value(position['strat'], price, periods_held)
                max_profit = position['strat']['max_profit'] - position['strat']['net_cost']
                tp_hit = pnl_pct >= max_profit * take_profit
                
                if opposite_signal or near_expiry or tp_hit:
                    # Calculate final P&L with time value
                    pnl = position['size'] * pnl_pct
                    
                    # Commission (4 legs)
                    comm = position['size'] * self.commission * 4
                    pnl -= comm
                    
                    capital += pnl
                    
                    exit_reason = 'opposite' if opposite_signal else ('expiry' if near_expiry else 'tp')
                    
                    trades.append({
                        'pnl': pnl,
                        'capital': capital,
                        'exit_reason': exit_reason,
                        'periods_held': periods_held
                    })
                    position = None
            
            # Open position
            if position is None:
                signal = False
                
                if strategy == 'bull_call' and spot_df.iloc[i]['bullish_ob']:
                    signal = True
                elif strategy == 'bear_put' and spot_df.iloc[i]['bearish_ob']:
                    signal = True
                
                if signal:
                    strat = self.find_strategy(price, opts_df, strategy, dte)
                    
                    if strat:
                        position = {
                            'idx': i,
                            'strat': strat,
                            'size': capital * 0.05
                        }
        
        if not trades:
            return None
        
        tdf = pd.DataFrame(trades)
        wins = len(tdf[tdf['pnl'] > 0])
        
        # Exit reason stats
        exit_reasons = tdf['exit_reason'].value_counts().to_dict()
        
        return {
            'asset': asset,
            'strategy': strategy,
            'dte': dte,
            'tp': take_profit,
            'trades': len(tdf),
            'wr': wins / len(tdf),
            'return': (tdf.iloc[-1]['capital'] - 10000) / 10000,
            'final': tdf.iloc[-1]['capital'],
            'avg_hold': tdf['periods_held'].mean(),
            'exits': exit_reasons
        }
    
    def run_matrix(self):
        print("\n" + "="*80)
        print("SMART OPTIONS BACKTEST - Exit on opposite signal + Time value")
        print("="*80)
        
        assets = [('BTCUSDT', 'BTC'), ('ETHUSDT', 'ETH')]
        strategies = ['bull_call', 'bear_put']
        dtes = [14, 30, 45, 60, 90]
        tps = [0.25, 0.50, 0.75, 1.00]
        
        results = []
        total = len(assets) * len(strategies) * len(dtes) * len(tps)
        current = 0
        
        for (asset, curr), strat, dte, tp in product(assets, strategies, dtes, tps):
            current += 1
            print(f"[{current}/{total}] {asset:10s} {strat:10s} {dte}DTE TP{int(tp*100)}%...", end=' ')
            
            r = self.test_combo(asset, curr, strat, dte, tp)
            
            if r:
                results.append(r)
                print(f"{r['trades']:2d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%, "
                      f"avg hold {r['avg_hold']:.1f} periods")
            else:
                print("No trades")
        
        results = sorted(results, key=lambda x: x['return'], reverse=True)
        
        print("\n" + "="*80)
        print("TOP 20 RESULTS")
        print("="*80)
        
        for i, r in enumerate(results[:20], 1):
            print(f"{i:2d}. {r['asset']:10s} {r['strategy']:10s} {r['dte']:2d}DTE TP{int(r['tp']*100):3d}%: "
                  f"{r['trades']:2d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%")
        
        import json
        with open('smart_options_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Saved to smart_options_results.json")

if __name__ == "__main__":
    bt = SmartOptionsBacktest()
    bt.run_matrix()
