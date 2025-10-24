#!/usr/bin/env python3
"""REAL OPTIONS BACKTEST with indicators"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import ast
from indicators.smart_money.order_blocks import OrderBlocks

class RealOptionsBacktest:
    def __init__(self):
        self.ob = OrderBlocks()
        print("✅ Real Options Backtest initialized")
    
    def load_spot_data(self, days=60):
        """Load spot price data"""
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
        files = sorted(data_dir.glob("*.csv"))[-days:]
        
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # 4H timeframe
        df = df.resample('4h').agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }).dropna()
        df.reset_index(inplace=True)
        
        return df
    
    def load_options_data(self):
        """Load latest options snapshot"""
        options_dir = Path(__file__).parent.parent / 'data' / 'options_history' / 'BTC'
        latest = sorted(options_dir.glob("*.csv"))[-1]
        df = pd.read_csv(latest)
        
        # Parse greeks
        def parse_greeks(g):
            if pd.isna(g):
                return {}
            try:
                return ast.literal_eval(g)
            except:
                return {}
        
        df['greeks_dict'] = df['greeks'].apply(parse_greeks)
        df['delta'] = df['greeks_dict'].apply(lambda x: x.get('delta', 0))
        df['theta'] = df['greeks_dict'].apply(lambda x: x.get('theta', 0))
        
        df['dte'] = (pd.to_datetime(df['expiration'], unit='ms') - pd.Timestamp.now()).dt.days
        
        return df
    
    def find_strategy(self, spot, dte_target=14):
        """Find best bull call spread for given spot and DTE"""
        opts = self.options_df
        
        # Filter by DTE
        valid = opts[(opts['dte'] >= dte_target-3) & (opts['dte'] <= dte_target+3)]
        calls = valid[valid['option_type'] == 'call']
        
        if len(calls) < 2:
            return None
        
        # ATM call
        atm = calls.iloc[(calls['strike'] - spot).abs().argsort()[:1]]
        # 5% OTM call
        otm_target = spot * 1.05
        otm = calls.iloc[(calls['strike'] - otm_target).abs().argsort()[:1]]
        
        if len(atm) > 0 and len(otm) > 0:
            cost = atm['mark_price'].iloc[0] - otm['mark_price'].iloc[0]
            
            return {
                'type': 'bull_call_spread',
                'entry_spot': spot,
                'lower_strike': atm['strike'].iloc[0],
                'upper_strike': otm['strike'].iloc[0],
                'cost_btc': cost,
                'dte': int(atm['dte'].iloc[0]),
                'net_delta': atm['delta'].iloc[0] - otm['delta'].iloc[0],
                'net_theta': atm['theta'].iloc[0] - otm['theta'].iloc[0]
            }
        
        return None
    
    def calculate_pnl(self, strategy, exit_spot):
        """Calculate P&L using real option pricing"""
        entry = strategy['entry_spot']
        lower = strategy['lower_strike']
        upper = strategy['upper_strike']
        cost = strategy['cost_btc']
        
        # Simplified: intrinsic value at expiration
        if exit_spot <= lower:
            value = 0
        elif exit_spot >= upper:
            value = (upper - lower) / entry
        else:
            value = (exit_spot - lower) / entry
        
        pnl_pct = value - cost
        
        return pnl_pct
    
    def run(self):
        print("\n" + "="*70)
        print("REAL OPTIONS BACKTEST")
        print("="*70)
        
        # Load data
        spot_df = self.load_spot_data(60)
        self.options_df = self.load_options_data()
        
        print(f"\nSpot data: {len(spot_df)} candles")
        print(f"Options: {len(self.options_df)} instruments")
        
        # Add Order Blocks
        spot_df = self.ob.find_order_blocks(spot_df)
        
        # Backtest
        capital = 10000
        position = None
        trades = []
        
        for i in range(100, len(spot_df)-18):
            price = spot_df.iloc[i]['close']
            
            # Close position after 18 periods (3 days)
            if position and (i - position['idx']) >= 18:
                exit_price = price
                pnl_pct = self.calculate_pnl(position['strategy'], exit_price)
                pnl_dollars = position['size'] * pnl_pct
                
                capital += pnl_dollars
                trades.append({
                    'pnl': pnl_dollars,
                    'capital': capital,
                    'entry': position['strategy']['entry_spot'],
                    'exit': exit_price
                })
                position = None
            
            # Open position on bullish Order Block
            if position is None and spot_df.iloc[i]['bullish_ob']:
                strategy = self.find_strategy(price, 14)
                
                if strategy:
                    position = {
                        'idx': i,
                        'strategy': strategy,
                        'size': capital * 0.05
                    }
        
        # Results
        if not trades:
            print("\n❌ No trades")
            return
        
        tdf = pd.DataFrame(trades)
        wins = len(tdf[tdf['pnl'] > 0])
        wr = wins / len(tdf)
        final = tdf.iloc[-1]['capital']
        ret = (final - 10000) / 10000
        
        print("\n" + "="*70)
        print("RESULTS: Order Blocks + Bull Call Spreads (Real Options)")
        print("="*70)
        print(f"Period:        60 days")
        print(f"Timeframe:     4H")
        print(f"Strategy:      Bull Call Spread (14 DTE)")
        print(f"")
        print(f"Total Trades:  {len(tdf)}")
        print(f"Win Rate:      {wr*100:.1f}%")
        print(f"Total Return:  {ret*100:.1f}%")
        print(f"Final Capital: ${final:,.0f}")
        print("="*70)
        
        tdf.to_csv('real_options_trades.csv', index=False)
        print(f"\n💾 Saved to real_options_trades.csv")

if __name__ == "__main__":
    bt = RealOptionsBacktest()
    bt.run()
