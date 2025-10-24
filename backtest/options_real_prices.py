#!/usr/bin/env python3
"""
REAL OPTIONS BACKTEST - используем РЕАЛЬНЫЕ цены с API
NO формул, только данные
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import ast
from indicators.smart_money.order_blocks import OrderBlocks

def analyze_real_options():
    """Анализ РЕАЛЬНЫХ опционов с API"""
    
    print("\n" + "="*80)
    print("REAL OPTIONS DATA ANALYSIS")
    print("="*80)
    
    # Load BTC options
    btc_opts = pd.read_csv('data/options_history/BTC/20251024_231900.csv')
    eth_opts = sorted(Path('data/options_history/ETH').glob('*.csv'))[-1]
    eth_opts = pd.read_csv(eth_opts)
    
    def parse_greeks(g):
        if pd.isna(g): return {}
        try: return ast.literal_eval(g)
        except: return {}
    
    for name, opts in [('BTC', btc_opts), ('ETH', eth_opts)]:
        opts['greeks_dict'] = opts['greeks'].apply(parse_greeks)
        opts['delta'] = opts['greeks_dict'].apply(lambda x: x.get('delta', 0))
        opts['theta'] = opts['greeks_dict'].apply(lambda x: x.get('theta', 0))
        opts['dte'] = (pd.to_datetime(opts['expiration'], unit='ms') - pd.Timestamp.now()).dt.days
        
        spot = opts['underlying_price'].iloc[0]
        
        print(f"\n{name} OPTIONS (Spot: ${spot:,.2f})")
        print("-" * 80)
        
        # Find ATM bull call spread
        calls_14 = opts[(opts['option_type'] == 'call') & (opts['dte'] >= 10) & (opts['dte'] <= 20)]
        calls_30 = opts[(opts['option_type'] == 'call') & (opts['dte'] >= 25) & (opts['dte'] <= 35)]
        calls_60 = opts[(opts['option_type'] == 'call') & (opts['dte'] >= 55) & (opts['dte'] <= 65)]
        
        for dte_name, calls in [('14 DTE', calls_14), ('30 DTE', calls_30), ('60 DTE', calls_60)]:
            if len(calls) < 2:
                continue
            
            # ATM
            atm = calls.iloc[(calls['strike'] - spot).abs().argsort()[:1]]
            # 5% OTM
            otm = calls.iloc[(calls['strike'] - spot*1.05).abs().argsort()[:1]]
            
            if len(atm) == 0 or len(otm) == 0:
                continue
            
            buy_price = atm['mark_price'].iloc[0]  # BTC
            sell_price = otm['mark_price'].iloc[0]  # BTC
            net_cost_btc = buy_price - sell_price
            net_cost_usd = net_cost_btc * spot
            
            # Greeks
            net_delta = atm['delta'].iloc[0] - otm['delta'].iloc[0]
            net_theta = atm['theta'].iloc[0] - otm['theta'].iloc[0]
            
            # Max profit
            max_profit_btc = (otm['strike'].iloc[0] - atm['strike'].iloc[0]) / spot
            max_profit_usd = max_profit_btc * spot
            
            # ROI
            roi = (max_profit_btc / net_cost_btc - 1) * 100
            
            print(f"\n{dte_name}:")
            print(f"  Buy ATM ${atm['strike'].iloc[0]:,.0f}:  {buy_price:.6f} BTC = ${buy_price*spot:,.2f}")
            print(f"  Sell OTM ${otm['strike'].iloc[0]:,.0f}: {sell_price:.6f} BTC = ${sell_price*spot:,.2f}")
            print(f"  Net Cost:  {net_cost_btc:.6f} BTC = ${net_cost_usd:,.2f}")
            print(f"  Max Profit: {max_profit_btc:.6f} BTC = ${max_profit_usd:,.2f}")
            print(f"  ROI if max: {roi:+.1f}%")
            print(f"  Delta: {net_delta:.4f}")
            print(f"  Theta: {net_theta:.4f} (per day)")
            print(f"  With $10k: {10000/net_cost_usd:.2f} contracts = ${10000/net_cost_usd*spot:,.0f} notional")

def backtest_with_real_data():
    """Backtest с РЕАЛЬНЫМИ ценами опционов"""
    
    print("\n" + "="*80)
    print("BACKTEST: SPOT vs OPTIONS (REAL DATA)")
    print("="*80)
    
    # Load ETH spot
    ob = OrderBlocks()
    
    data_dir = Path('data/raw/ETHUSDT')
    files = sorted(data_dir.glob("*.csv"))[-100:]
    
    dfs = [pd.read_csv(f) for f in files]
    spot_df = pd.concat(dfs, ignore_index=True)
    spot_df['timestamp'] = pd.to_datetime(spot_df['timestamp'])
    spot_df.set_index('timestamp', inplace=True)
    
    spot_df = spot_df.resample('4h').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    spot_df.reset_index(inplace=True)
    
    spot_df = ob.find_order_blocks(spot_df)
    
    # Load ETH options (60 DTE)
    eth_opts = sorted(Path('data/options_history/ETH').glob('*.csv'))[-1]
    opts = pd.read_csv(eth_opts)
    
    def parse_greeks(g):
        if pd.isna(g): return {}
        try: return ast.literal_eval(g)
        except: return {}
    
    opts['greeks_dict'] = opts['greeks'].apply(parse_greeks)
    opts['delta'] = opts['greeks_dict'].apply(lambda x: x.get('delta', 0))
    opts['theta'] = opts['greeks_dict'].apply(lambda x: x.get('theta', 0))
    opts['dte'] = (pd.to_datetime(opts['expiration'], unit='ms') - pd.Timestamp.now()).dt.days
    
    initial_spot = opts['underlying_price'].iloc[0]
    
    # Find 60 DTE bull call spread
    calls = opts[(opts['option_type'] == 'call') & (opts['dte'] >= 55) & (opts['dte'] <= 65)]
    
    atm = calls.iloc[(calls['strike'] - initial_spot).abs().argsort()[:1]]
    otm = calls.iloc[(calls['strike'] - initial_spot*1.05).abs().argsort()[:1]]
    
    net_cost_btc = atm['mark_price'].iloc[0] - otm['mark_price'].iloc[0]
    net_cost_usd = net_cost_btc * initial_spot
    net_delta = atm['delta'].iloc[0] - otm['delta'].iloc[0]
    net_theta = atm['theta'].iloc[0] - otm['theta'].iloc[0]
    lower_strike = atm['strike'].iloc[0]
    upper_strike = otm['strike'].iloc[0]
    
    print(f"\nUsing ETH 60 DTE Bull Call Spread:")
    print(f"  Cost: ${net_cost_usd:,.2f}")
    print(f"  Delta: {net_delta:.4f}")
    print(f"  Theta: {net_theta:.2f}/day")
    
    # SPOT backtest
    spot_capital = 10000
    spot_pos = None
    spot_trades = []
    
    # OPTIONS backtest
    opts_capital = 10000
    opts_pos = None
    opts_trades = []
    
    for i in range(100, len(spot_df)-5):
        price = spot_df.iloc[i]['close']
        
        # === SPOT ===
        if spot_pos and (i - spot_pos['idx']) >= 18:
            pnl_pct = (price - spot_pos['entry']) / spot_pos['entry']
            pnl = spot_pos['size'] * pnl_pct
            spot_capital += pnl
            spot_trades.append({'pnl': pnl, 'capital': spot_capital})
            spot_pos = None
        
        if spot_pos is None and spot_df.iloc[i]['bullish_ob']:
            spot_pos = {'idx': i, 'entry': price, 'size': spot_capital * 0.05}
        
        # === OPTIONS ===
        if opts_pos:
            periods = i - opts_pos['idx']
            days_passed = periods / 6  # 4h periods -> days
            
            # Exit on opposite signal
            if spot_df.iloc[i]['bearish_ob'] or periods >= 13:
                # Profit from price change (using Delta)
                price_change = price - opts_pos['entry']
                price_change_pct = price_change / opts_pos['entry']
                
                # Option value change = Delta × price change %
                option_value_change = net_delta * price_change_pct
                
                # Subtract Theta decay
                theta_loss = net_theta * days_passed / initial_spot
                
                # Total P&L in BTC
                pnl_btc = option_value_change - theta_loss
                
                # Convert to USD
                contracts = opts_pos['size'] / net_cost_usd
                pnl_usd = pnl_btc * contracts * price
                
                opts_capital += pnl_usd
                opts_trades.append({'pnl': pnl_usd, 'capital': opts_capital})
                opts_pos = None
        
        if opts_pos is None and spot_df.iloc[i]['bullish_ob']:
            opts_pos = {'idx': i, 'entry': price, 'size': opts_capital * 0.05}
    
    # Results
    print(f"\n" + "="*80)
    print("RESULTS (100 days)")
    print("="*80)
    
    if spot_trades:
        spot_df_t = pd.DataFrame(spot_trades)
        spot_wins = len(spot_df_t[spot_df_t['pnl'] > 0])
        spot_return = (spot_df_t.iloc[-1]['capital'] - 10000) / 10000
        
        print(f"\nSPOT:")
        print(f"  Trades: {len(spot_trades)}")
        print(f"  Win Rate: {spot_wins/len(spot_trades)*100:.1f}%")
        print(f"  Return: {spot_return*100:+.1f}%")
        print(f"  Final: ${spot_df_t.iloc[-1]['capital']:,.0f}")
    
    if opts_trades:
        opts_df_t = pd.DataFrame(opts_trades)
        opts_wins = len(opts_df_t[opts_df_t['pnl'] > 0])
        opts_return = (opts_df_t.iloc[-1]['capital'] - 10000) / 10000
        
        print(f"\nOPTIONS (60 DTE Bull Call):")
        print(f"  Trades: {len(opts_trades)}")
        print(f"  Win Rate: {opts_wins/len(opts_trades)*100:.1f}%")
        print(f"  Return: {opts_return*100:+.1f}%")
        print(f"  Final: ${opts_df_t.iloc[-1]['capital']:,.0f}")
    
    print("="*80)

if __name__ == "__main__":
    analyze_real_options()
    backtest_with_real_data()
