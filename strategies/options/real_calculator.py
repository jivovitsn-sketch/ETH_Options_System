#!/usr/bin/env python3
"""REAL OPTIONS CALCULATOR"""
import pandas as pd
from pathlib import Path
import ast

class RealOptionsCalculator:
    def __init__(self):
        self.load_latest_data()
        print("✅ Real Options Calculator initialized")
    
    def load_latest_data(self):
        options_dir = Path(__file__).parent.parent.parent / 'data' / 'options' / 'BTC'
        latest = sorted(options_dir.glob("*.csv"))[-1]
        self.df = pd.read_csv(latest)
        
        # Parse greeks properly
        def parse_greeks(g):
            if pd.isna(g):
                return {}
            try:
                return ast.literal_eval(g)
            except:
                return {}
        
        self.df['greeks_dict'] = self.df['greeks'].apply(parse_greeks)
        self.df['delta'] = self.df['greeks_dict'].apply(lambda x: x.get('delta', 0))
        self.df['theta'] = self.df['greeks_dict'].apply(lambda x: x.get('theta', 0))
        self.df['vega'] = self.df['greeks_dict'].apply(lambda x: x.get('vega', 0))
        self.df['gamma'] = self.df['greeks_dict'].apply(lambda x: x.get('gamma', 0))
        
        self.df['dte'] = (pd.to_datetime(self.df['expiration'], unit='ms') - pd.Timestamp.now()).dt.days
        
        self.spot = self.df['underlying_price'].iloc[0]
        print(f"   Spot: ${self.spot:,.2f}")
    
    def bull_call_spread(self):
        """Bull Call Spread - ATM to 10% OTM"""
        calls = self.df[self.df['option_type'] == 'call']
        
        # ATM
        atm = calls.iloc[(calls['strike'] - self.spot).abs().argsort()[:1]]
        # 10% OTM
        otm_target = self.spot * 1.05
        otm = calls.iloc[(calls['strike'] - otm_target).abs().argsort()[:1]]
        
        if len(atm) > 0 and len(otm) > 0:
            cost = atm['mark_price'].iloc[0] - otm['mark_price'].iloc[0]
            spread = otm['strike'].iloc[0] - atm['strike'].iloc[0]
            max_profit = spread / self.spot - cost
            
            return {
                'name': 'Bull Call Spread',
                'lower': atm['strike'].iloc[0],
                'upper': otm['strike'].iloc[0],
                'cost_btc': cost,
                'max_profit_pct': max_profit * 100,
                'dte': int(atm['dte'].iloc[0]),
                'delta': atm['delta'].iloc[0] - otm['delta'].iloc[0],
                'theta': atm['theta'].iloc[0] - otm['theta'].iloc[0]
            }
        return None
    
    def bear_put_spread(self):
        """Bear Put Spread - ATM to 10% OTM"""
        puts = self.df[self.df['option_type'] == 'put']
        
        # ATM
        atm = puts.iloc[(puts['strike'] - self.spot).abs().argsort()[:1]]
        # 10% OTM
        otm_target = self.spot * 0.95
        otm = puts.iloc[(puts['strike'] - otm_target).abs().argsort()[:1]]
        
        if len(atm) > 0 and len(otm) > 0:
            cost = atm['mark_price'].iloc[0] - otm['mark_price'].iloc[0]
            spread = atm['strike'].iloc[0] - otm['strike'].iloc[0]
            max_profit = spread / self.spot - cost
            
            return {
                'name': 'Bear Put Spread',
                'upper': atm['strike'].iloc[0],
                'lower': otm['strike'].iloc[0],
                'cost_btc': cost,
                'max_profit_pct': max_profit * 100,
                'dte': int(atm['dte'].iloc[0]),
                'delta': atm['delta'].iloc[0] - otm['delta'].iloc[0],
                'theta': atm['theta'].iloc[0] - otm['theta'].iloc[0]
            }
        return None
    
    def iron_condor(self):
        """Iron Condor - sell call spread + sell put spread"""
        calls = self.df[self.df['option_type'] == 'call']
        puts = self.df[self.df['option_type'] == 'put']
        
        # Sell call at +5%, buy call at +10%
        sell_call = calls.iloc[(calls['strike'] - self.spot*1.05).abs().argsort()[:1]]
        buy_call = calls.iloc[(calls['strike'] - self.spot*1.10).abs().argsort()[:1]]
        
        # Sell put at -5%, buy put at -10%
        sell_put = puts.iloc[(puts['strike'] - self.spot*0.95).abs().argsort()[:1]]
        buy_put = puts.iloc[(puts['strike'] - self.spot*0.90).abs().argsort()[:1]]
        
        if all(len(x) > 0 for x in [sell_call, buy_call, sell_put, buy_put]):
            credit = (sell_call['mark_price'].iloc[0] - buy_call['mark_price'].iloc[0] +
                     sell_put['mark_price'].iloc[0] - buy_put['mark_price'].iloc[0])
            
            return {
                'name': 'Iron Condor',
                'call_strikes': f"{sell_call['strike'].iloc[0]:.0f}/{buy_call['strike'].iloc[0]:.0f}",
                'put_strikes': f"{buy_put['strike'].iloc[0]:.0f}/{sell_put['strike'].iloc[0]:.0f}",
                'credit_btc': credit,
                'max_profit_pct': credit / 0.01 * 100,  # per 0.01 BTC
                'dte': int(sell_call['dte'].iloc[0])
            }
        return None
    
    def straddle(self):
        """Long Straddle - buy ATM call + ATM put"""
        calls = self.df[self.df['option_type'] == 'call']
        puts = self.df[self.df['option_type'] == 'put']
        
        atm_call = calls.iloc[(calls['strike'] - self.spot).abs().argsort()[:1]]
        atm_put = puts.iloc[(puts['strike'] - self.spot).abs().argsort()[:1]]
        
        if len(atm_call) > 0 and len(atm_put) > 0:
            cost = atm_call['mark_price'].iloc[0] + atm_put['mark_price'].iloc[0]
            
            return {
                'name': 'Long Straddle',
                'strike': atm_call['strike'].iloc[0],
                'cost_btc': cost,
                'breakeven_up': atm_call['strike'].iloc[0] + cost * self.spot,
                'breakeven_down': atm_put['strike'].iloc[0] - cost * self.spot,
                'dte': int(atm_call['dte'].iloc[0]),
                'iv': atm_call['mark_iv'].iloc[0]
            }
        return None
    
    def show_all(self):
        print("\n" + "="*80)
        print("ALL STRATEGIES WITH REAL DATA")
        print("="*80)
        
        strategies = [
            self.bull_call_spread(),
            self.bear_put_spread(),
            self.iron_condor(),
            self.straddle()
        ]
        
        for s in strategies:
            if s:
                print(f"\n{s['name']}:")
                for k, v in s.items():
                    if k != 'name':
                        print(f"  {k}: {v}")

if __name__ == "__main__":
    calc = RealOptionsCalculator()
    calc.show_all()
