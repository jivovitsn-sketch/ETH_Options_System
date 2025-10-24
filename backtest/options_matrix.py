#!/usr/bin/env python3
"""OPTIONS MATRIX - все комбинации"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import ast
from itertools import product
from indicators.smart_money.order_blocks import OrderBlocks
from indicators.smart_money.fair_value_gaps import FairValueGaps

class OptionsMatrix:
    def __init__(self):
        self.ob = OrderBlocks()
        self.fvg = FairValueGaps()
        
        # Load spot
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
        files = sorted(data_dir.glob("*.csv"))[-60:]
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.resample('4h').agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }).dropna()
        df.reset_index(inplace=True)
        
        # Add indicators
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        df = self.ob.find_order_blocks(df)
        df = self.fvg.find_fvg(df)
        
        self.spot_df = df
        
        # Load options
        options_dir = Path(__file__).parent.parent / 'data' / 'options_history' / 'BTC'
        latest = sorted(options_dir.glob("*.csv"))[-1]
        opts = pd.read_csv(latest)
        
        def parse_greeks(g):
            if pd.isna(g): return {}
            try: return ast.literal_eval(g)
            except: return {}
        
        opts['greeks_dict'] = opts['greeks'].apply(parse_greeks)
        opts['delta'] = opts['greeks_dict'].apply(lambda x: x.get('delta', 0))
        opts['dte'] = (pd.to_datetime(opts['expiration'], unit='ms') - pd.Timestamp.now()).dt.days
        
        self.options_df = opts
        
        print(f"✅ Loaded {len(self.spot_df)} candles, {len(self.options_df)} options")
    
    def get_signal(self, i, indicator):
        """Get trading signal"""
        row = self.spot_df.iloc[i]
        
        if indicator == 'ob_bullish':
            return 'LONG' if row['bullish_ob'] else None
        elif indicator == 'ob_bearish':
            return 'SHORT' if row['bearish_ob'] else None
        elif indicator == 'fvg_bullish':
            return 'LONG' if row['fvg_bullish'] else None
        elif indicator == 'fvg_bearish':
            return 'SHORT' if row['fvg_bearish'] else None
        elif indicator == 'sma':
            if pd.notna(row['sma20']) and pd.notna(row['sma50']):
                if row['close'] > row['sma20'] > row['sma50']:
                    return 'LONG'
                elif row['close'] < row['sma20'] < row['sma50']:
                    return 'SHORT'
        
        return None
    
    def find_option_strategy(self, spot, signal, strategy_type, dte):
        """Find option strategy"""
        opts = self.options_df
        valid = opts[(opts['dte'] >= dte-3) & (opts['dte'] <= dte+3)]
        
        if strategy_type == 'bull_call' and signal == 'LONG':
            calls = valid[valid['option_type'] == 'call']
            if len(calls) < 2: return None
            
            atm = calls.iloc[(calls['strike'] - spot).abs().argsort()[:1]]
            otm = calls.iloc[(calls['strike'] - spot*1.05).abs().argsort()[:1]]
            
            if len(atm) > 0 and len(otm) > 0:
                cost = atm['mark_price'].iloc[0] - otm['mark_price'].iloc[0]
                return {'type': 'bull_call', 'entry': spot, 
                       'lower': atm['strike'].iloc[0], 'upper': otm['strike'].iloc[0], 
                       'cost': cost}
        
        elif strategy_type == 'bear_put' and signal == 'SHORT':
            puts = valid[valid['option_type'] == 'put']
            if len(puts) < 2: return None
            
            atm = puts.iloc[(puts['strike'] - spot).abs().argsort()[:1]]
            otm = puts.iloc[(puts['strike'] - spot*0.95).abs().argsort()[:1]]
            
            if len(atm) > 0 and len(otm) > 0:
                cost = atm['mark_price'].iloc[0] - otm['mark_price'].iloc[0]
                return {'type': 'bear_put', 'entry': spot,
                       'upper': atm['strike'].iloc[0], 'lower': otm['strike'].iloc[0],
                       'cost': cost}
        
        return None
    
    def calc_pnl(self, strat, exit_spot):
        """Calculate P&L"""
        if strat['type'] == 'bull_call':
            if exit_spot <= strat['lower']:
                value = 0
            elif exit_spot >= strat['upper']:
                value = (strat['upper'] - strat['lower']) / strat['entry']
            else:
                value = (exit_spot - strat['lower']) / strat['entry']
            return value - strat['cost']
        
        elif strat['type'] == 'bear_put':
            if exit_spot >= strat['upper']:
                value = 0
            elif exit_spot <= strat['lower']:
                value = (strat['upper'] - strat['lower']) / strat['entry']
            else:
                value = (strat['upper'] - exit_spot) / strat['entry']
            return value - strat['cost']
        
        return 0
    
    def test_combo(self, indicator, strategy, dte):
        """Test one combination"""
        capital = 10000
        position = None
        trades = []
        
        for i in range(100, len(self.spot_df)-18):
            price = self.spot_df.iloc[i]['close']
            
            # Close
            if position and (i - position['idx']) >= 18:
                pnl_pct = self.calc_pnl(position['strat'], price)
                pnl = position['size'] * pnl_pct
                capital += pnl
                trades.append({'pnl': pnl, 'capital': capital})
                position = None
            
            # Open
            if position is None:
                signal = self.get_signal(i, indicator)
                if signal:
                    strat = self.find_option_strategy(price, signal, strategy, dte)
                    if strat:
                        position = {'idx': i, 'strat': strat, 'size': capital * 0.05}
        
        if not trades:
            return None
        
        tdf = pd.DataFrame(trades)
        wins = len(tdf[tdf['pnl'] > 0])
        return {
            'indicator': indicator,
            'strategy': strategy,
            'dte': dte,
            'trades': len(tdf),
            'wr': wins / len(tdf),
            'return': (tdf.iloc[-1]['capital'] - 10000) / 10000,
            'final': tdf.iloc[-1]['capital']
        }
    
    def run_matrix(self):
        print("\n" + "="*80)
        print("OPTIONS MATRIX TEST")
        print("="*80)
        
        indicators = ['ob_bullish', 'ob_bearish', 'fvg_bullish', 'fvg_bearish', 'sma']
        strategies = ['bull_call', 'bear_put']
        dtes = [7, 14, 30]
        
        results = []
        
        for ind, strat, dte in product(indicators, strategies, dtes):
            r = self.test_combo(ind, strat, dte)
            if r:
                results.append(r)
                print(f"✓ {ind:15s} + {strat:10s} + {dte}DTE: {r['trades']:2d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%")
        
        results = sorted(results, key=lambda x: x['return'], reverse=True)
        
        print("\n" + "="*80)
        print("TOP 5 COMBINATIONS")
        print("="*80)
        for r in results[:5]:
            print(f"{r['indicator']:15s} + {r['strategy']:10s} ({r['dte']:2d}DTE): "
                  f"{r['trades']:2d} trades, {r['wr']*100:5.1f}% WR, {r['return']*100:+6.1f}%")

if __name__ == "__main__":
    matrix = OptionsMatrix()
    matrix.run_matrix()
