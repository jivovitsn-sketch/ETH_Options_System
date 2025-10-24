#!/usr/bin/env python3
"""
ULTIMATE BACKTEST
ВСЕ 8 стратегий + ВСЕ индикаторы на ОДНИХ данных
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from itertools import product

from indicators.smart_money.fair_value_gaps import FairValueGaps
from indicators.smart_money.order_blocks import OrderBlocks
from strategies.options.all_spreads import AllOptionStrategies

class UltimateBacktest:
    """
    Матрица:
    - 8 опционных стратегий
    - 4 индикатора (SMA, FVG, OB, SMA+FVG)
    - 60 дней данных
    
    = 32 комбинации
    """
    
    def __init__(self):
        self.fvg = FairValueGaps()
        self.ob = OrderBlocks()
        self.options = AllOptionStrategies()
        print("✅ Ultimate Backtest initialized")
    
    def load_data(self):
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
        files = sorted(data_dir.glob("*.csv"))[-60:]
        
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        resampled = df.resample('4h').agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }).dropna()
        resampled.reset_index(inplace=True)
        
        print(f"✅ Loaded {len(resampled)} candles (4H)")
        return resampled
    
    def get_signal(self, df, i, indicator):
        """Получить сигнал от индикатора"""
        
        if indicator == 'sma':
            sma20 = df.iloc[i]['sma20']
            sma50 = df.iloc[i]['sma50']
            price = df.iloc[i]['close']
            
            if pd.notna(sma20) and pd.notna(sma50):
                if price > sma20 > sma50:
                    return 'BULLISH'
                elif price < sma20 < sma50:
                    return 'BEARISH'
            return 'NEUTRAL'
        
        elif indicator == 'fvg':
            if df.iloc[i]['fvg_bullish']:
                return 'BULLISH'
            elif df.iloc[i]['fvg_bearish']:
                return 'BEARISH'
            return 'NEUTRAL'
        
        elif indicator == 'ob':
            if df.iloc[i]['bullish_ob']:
                return 'BULLISH'
            elif df.iloc[i]['bearish_ob']:
                return 'BEARISH'
            return 'NEUTRAL'
        
        elif indicator == 'sma_fvg':
            sma_sig = self.get_signal(df, i, 'sma')
            fvg_sig = self.get_signal(df, i, 'fvg')
            
            if sma_sig == fvg_sig and sma_sig != 'NEUTRAL':
                return sma_sig
            return 'NEUTRAL'
        
        return 'NEUTRAL'
    
    def select_strategy(self, signal, strategy_type, price, risk):
        """Выбрать стратегию по сигналу"""
        
        if strategy_type == 'bull_call':
            if signal == 'BULLISH':
                return self.options.bull_call_spread(price, risk)
        
        elif strategy_type == 'bear_put':
            if signal == 'BEARISH':
                return self.options.bear_put_spread(price, risk)
        
        elif strategy_type == 'iron_condor':
            if signal == 'NEUTRAL':
                return self.options.iron_condor(price, risk)
        
        elif strategy_type == 'butterfly':
            if signal == 'NEUTRAL':
                return self.options.butterfly_spread(price, risk)
        
        elif strategy_type == 'straddle':
            # Ставка на волатильность - открываем всегда
            return self.options.straddle(price, risk)
        
        elif strategy_type == 'strangle':
            return self.options.strangle(price, risk)
        
        elif strategy_type == 'calendar':
            if signal == 'NEUTRAL':
                return self.options.calendar_spread(price, risk)
        
        elif strategy_type == 'lottery':
            if signal == 'BULLISH':
                return self.options.lottery_call(price, risk)
            elif signal == 'BEARISH':
                return self.options.lottery_put(price, risk)
        
        return None
    
    def backtest_combo(self, df, indicator, strategy_type):
        """Бэктест одной комбинации"""
        
        # Prepare indicators
        df = df.copy()
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        df = self.fvg.find_fvg(df)
        df = self.ob.find_order_blocks(df)
        
        trades = []
        position = None
        capital = 10000
        
        for i in range(100, len(df) - 18):
            price = df.iloc[i]['close']
            
            # Close position
            if position and (i - position['entry_idx']) >= 18:
                exit_price = price
                pnl = self.options.calculate_pnl(
                    position['strategy'],
                    exit_price
                )
                capital += pnl
                trades.append({'pnl': pnl, 'capital': capital})
                position = None
            
            # Open position
            if position is None:
                signal = self.get_signal(df, i, indicator)
                risk = capital * 0.05
                
                strategy = self.select_strategy(signal, strategy_type, price, risk)
                
                if strategy:
                    position = {
                        'entry_idx': i,
                        'strategy': strategy
                    }
        
        # Metrics
        if not trades:
            return None
        
        tdf = pd.DataFrame(trades)
        wins = len(tdf[tdf['pnl'] > 0])
        wr = wins / len(tdf)
        final = tdf.iloc[-1]['capital']
        ret = (final - 10000) / 10000
        
        return {
            'indicator': indicator,
            'strategy': strategy_type,
            'trades': len(tdf),
            'win_rate': wr,
            'return': ret,
            'final': final
        }
    
    def run_full_matrix(self):
        """Полная матрица бэктестов"""
        
        print("\n╔════════════════════════════════════════════════╗")
        print("║   ULTIMATE BACKTEST - FULL MATRIX             ║")
        print("╚════════════════════════════════════════════════╝")
        
        df = self.load_data()
        
        indicators = ['sma', 'fvg', 'ob', 'sma_fvg']
        strategies = ['bull_call', 'bear_put', 'iron_condor', 'butterfly', 
                     'straddle', 'strangle', 'calendar', 'lottery']
        
        results = []
        total_combos = len(indicators) * len(strategies)
        
        print(f"\n🔍 Testing {total_combos} combinations...")
        
        for ind, strat in product(indicators, strategies):
            result = self.backtest_combo(df, ind, strat)
            if result:
                results.append(result)
        
        # Sort by return
        results = sorted(results, key=lambda x: x['return'], reverse=True)
        
        # Print top 10
        print(f"\n{'='*90}")
        print(f"📊 TOP 10 COMBINATIONS")
        print(f"{'='*90}")
        print(f"{'Indicator':<12} {'Strategy':<15} {'Trades':>8} {'WR':>8} {'Return':>10} {'Final':>12}")
        print(f"{'-'*90}")
        
        for r in results[:10]:
            print(f"{r['indicator']:<12} {r['strategy']:<15} {r['trades']:>8d} "
                  f"{r['win_rate']*100:>7.1f}% {r['return']*100:>9.1f}% ${r['final']:>10,.0f}")
        
        print(f"{'='*90}")
        
        if results:
            best = results[0]
            print(f"\n🏆 BEST: {best['indicator']} + {best['strategy']}")
            print(f"   Return: {best['return']*100:.1f}%")
            print(f"   Win Rate: {best['win_rate']*100:.1f}%")
            print(f"   Trades: {best['trades']}")

if __name__ == "__main__":
    bt = UltimateBacktest()
    bt.run_full_matrix()
