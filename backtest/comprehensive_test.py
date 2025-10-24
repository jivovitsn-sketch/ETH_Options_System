#!/usr/bin/env python3
"""
COMPREHENSIVE BACKTEST - FIXED
Тестируем все индикаторы + опционные стратегии
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime

from indicators.smart_money.fair_value_gaps import FairValueGaps
from indicators.smart_money.order_blocks import OrderBlocks
from indicators.smart_money.liquidity_zones import LiquidityZones
from indicators.gann.gann_angles import GannAngles
from strategies.options.spreads import OptionsSpreads

class ComprehensiveBacktest:
    """
    Полный бэктест всех индикаторов
    """
    
    def __init__(self):
        self.fvg = FairValueGaps()
        self.ob = OrderBlocks()
        self.liq = LiquidityZones()
        self.gann = GannAngles()
        self.options = OptionsSpreads()
        
        print("✅ Comprehensive Backtest initialized")
    
    def load_data(self, days: int = 60):
        """Загрузить данные"""
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'BTCUSDT'
        files = sorted(data_dir.glob("*.csv"))[-days:]
        
        dfs = []
        for file in files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        df = pd.concat(dfs, ignore_index=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Resample to 4H
        df.set_index('timestamp', inplace=True)
        resampled = df.resample('4h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        resampled.reset_index(inplace=True)
        
        print(f"✅ Loaded {len(resampled)} candles (4H)")
        return resampled
    
    def test_sma_baseline(self, df: pd.DataFrame):
        """Test SMA (baseline)"""
        df = df.copy()
        
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        trades = []
        position = None
        capital = 10000
        
        for i in range(100, len(df) - 18):
            current_price = df.iloc[i]['close']
            sma20 = df.iloc[i]['sma20']
            sma50 = df.iloc[i]['sma50']
            
            # Close position
            if position and (i - position['entry_idx']) >= 18:
                exit_price = current_price
                
                # Calculate option P&L with entry_price
                pnl_dollars = self.options.calculate_pnl(
                    position['option_strategy'],
                    position['entry_price'],
                    exit_price
                )
                
                capital += pnl_dollars
                
                trades.append({
                    'pnl': pnl_dollars,
                    'capital': capital,
                    'strategy': position['option_type']
                })
                
                position = None
            
            # Open position
            if position is None and pd.notna(sma20) and pd.notna(sma50):
                signal = None
                
                if current_price > sma20 > sma50:
                    signal = 'BULLISH'
                elif current_price < sma20 < sma50:
                    signal = 'BEARISH'
                
                if signal:
                    risk = capital * 0.05
                    
                    # Create option strategy
                    if signal == 'BULLISH':
                        option_strategy = self.options.bull_call_spread(
                            current_price,
                            1.00,  # ATM
                            1.10,  # 10% OTM
                            risk
                        )
                        option_type = 'bull_call_spread'
                    else:
                        option_strategy = self.options.bear_put_spread(
                            current_price,
                            0.90,  # 10% OTM
                            1.00,  # ATM
                            risk
                        )
                        option_type = 'bear_put_spread'
                    
                    position = {
                        'entry_idx': i,
                        'entry_price': current_price,
                        'option_strategy': option_strategy,
                        'option_type': option_type
                    }
        
        return self._calculate_metrics(trades, 'SMA Baseline')
    
    def test_fvg_only(self, df: pd.DataFrame):
        """Test FVG только"""
        df_with_fvg = self.fvg.find_fvg(df)
        
        trades = []
        position = None
        capital = 10000
        
        for i in range(100, len(df_with_fvg) - 18):
            current_price = df_with_fvg.iloc[i]['close']
            
            # Close position
            if position and (i - position['entry_idx']) >= 18:
                exit_price = current_price
                pnl_dollars = self.options.calculate_pnl(
                    position['option_strategy'],
                    position['entry_price'],
                    exit_price
                )
                capital += pnl_dollars
                trades.append({'pnl': pnl_dollars, 'capital': capital})
                position = None
            
            # Open position
            if position is None:
                signal = None
                
                if df_with_fvg.iloc[i]['fvg_bullish']:
                    signal = 'BULLISH'
                elif df_with_fvg.iloc[i]['fvg_bearish']:
                    signal = 'BEARISH'
                
                if signal:
                    risk = capital * 0.05
                    
                    if signal == 'BULLISH':
                        option_strategy = self.options.bull_call_spread(
                            current_price, 1.0, 1.10, risk
                        )
                    else:
                        option_strategy = self.options.bear_put_spread(
                            current_price, 0.90, 1.0, risk
                        )
                    
                    position = {
                        'entry_idx': i,
                        'entry_price': current_price,
                        'option_strategy': option_strategy
                    }
        
        return self._calculate_metrics(trades, 'FVG Only')
    
    def test_order_blocks_only(self, df: pd.DataFrame):
        """Test Order Blocks только"""
        df_with_ob = self.ob.find_order_blocks(df)
        
        trades = []
        position = None
        capital = 10000
        
        for i in range(100, len(df_with_ob) - 18):
            current_price = df_with_ob.iloc[i]['close']
            
            # Close
            if position and (i - position['entry_idx']) >= 18:
                exit_price = current_price
                pnl_dollars = self.options.calculate_pnl(
                    position['option_strategy'],
                    position['entry_price'],
                    exit_price
                )
                capital += pnl_dollars
                trades.append({'pnl': pnl_dollars, 'capital': capital})
                position = None
            
            # Open
            if position is None:
                signal = None
                
                if df_with_ob.iloc[i]['bullish_ob']:
                    signal = 'BULLISH'
                elif df_with_ob.iloc[i]['bearish_ob']:
                    signal = 'BEARISH'
                
                if signal:
                    risk = capital * 0.05
                    
                    if signal == 'BULLISH':
                        option_strategy = self.options.bull_call_spread(
                            current_price, 1.0, 1.10, risk
                        )
                    else:
                        option_strategy = self.options.bear_put_spread(
                            current_price, 0.90, 1.0, risk
                        )
                    
                    position = {
                        'entry_idx': i,
                        'entry_price': current_price,
                        'option_strategy': option_strategy
                    }
        
        return self._calculate_metrics(trades, 'Order Blocks Only')
    
    def test_sma_plus_fvg(self, df: pd.DataFrame):
        """Test SMA + FVG комбо"""
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        df_with_fvg = self.fvg.find_fvg(df)
        
        trades = []
        position = None
        capital = 10000
        
        for i in range(100, len(df_with_fvg) - 18):
            current_price = df_with_fvg.iloc[i]['close']
            sma20 = df_with_fvg.iloc[i]['sma20']
            sma50 = df_with_fvg.iloc[i]['sma50']
            
            # Close
            if position and (i - position['entry_idx']) >= 18:
                exit_price = current_price
                pnl_dollars = self.options.calculate_pnl(
                    position['option_strategy'],
                    position['entry_price'],
                    exit_price
                )
                capital += pnl_dollars
                trades.append({'pnl': pnl_dollars, 'capital': capital})
                position = None
            
            # Open: нужно согласие SMA и FVG
            if position is None and pd.notna(sma20) and pd.notna(sma50):
                sma_signal = None
                fvg_signal = None
                
                # SMA
                if current_price > sma20 > sma50:
                    sma_signal = 'BULLISH'
                elif current_price < sma20 < sma50:
                    sma_signal = 'BEARISH'
                
                # FVG
                if df_with_fvg.iloc[i]['fvg_bullish']:
                    fvg_signal = 'BULLISH'
                elif df_with_fvg.iloc[i]['fvg_bearish']:
                    fvg_signal = 'BEARISH'
                
                # Согласие обоих
                if sma_signal and sma_signal == fvg_signal:
                    risk = capital * 0.05
                    
                    if sma_signal == 'BULLISH':
                        option_strategy = self.options.bull_call_spread(
                            current_price, 1.0, 1.10, risk
                        )
                    else:
                        option_strategy = self.options.bear_put_spread(
                            current_price, 0.90, 1.0, risk
                        )
                    
                    position = {
                        'entry_idx': i,
                        'entry_price': current_price,
                        'option_strategy': option_strategy
                    }
        
        return self._calculate_metrics(trades, 'SMA + FVG')
    
    def _calculate_metrics(self, trades: list, strategy_name: str) -> dict:
        """Рассчитать метрики"""
        if not trades:
            return {
                'name': strategy_name,
                'trades': 0,
                'win_rate': 0,
                'return': 0,
                'final_capital': 10000
            }
        
        trades_df = pd.DataFrame(trades)
        
        total_trades = len(trades_df)
        winning = len(trades_df[trades_df['pnl'] > 0])
        win_rate = winning / total_trades if total_trades > 0 else 0
        
        final_capital = trades_df.iloc[-1]['capital']
        total_return = (final_capital - 10000) / 10000
        
        return {
            'name': strategy_name,
            'trades': total_trades,
            'win_rate': win_rate,
            'return': total_return,
            'final_capital': final_capital
        }
    
    def run_all_tests(self):
        """Запустить все тесты"""
        print("\n╔════════════════════════════════════════════════╗")
        print("║   COMPREHENSIVE BACKTEST - ALL INDICATORS     ║")
        print("╚════════════════════════════════════════════════╝")
        
        df = self.load_data(days=60)
        
        results = []
        
        print("\n🔍 Testing strategies...")
        
        # Test each strategy
        results.append(self.test_sma_baseline(df.copy()))
        results.append(self.test_fvg_only(df.copy()))
        results.append(self.test_order_blocks_only(df.copy()))
        results.append(self.test_sma_plus_fvg(df.copy()))
        
        # Print results
        print(f"\n{'='*80}")
        print(f"📊 RESULTS (Options Spreads - 4H timeframe, 3-day hold)")
        print(f"{'='*80}")
        print(f"{'Strategy':<25} {'Trades':>8} {'Win Rate':>10} {'Return':>12} {'Final $':>12}")
        print(f"{'-'*80}")
        
        for r in results:
            print(f"{r['name']:<25} {r['trades']:>8d} {r['win_rate']*100:>9.1f}% "
                  f"{r['return']*100:>11.1f}% ${r['final_capital']:>10,.0f}")
        
        print(f"{'='*80}")
        
        # Best strategy
        if results:
            best = max(results, key=lambda x: x['return'])
            print(f"\n🏆 BEST: {best['name']} with {best['return']*100:.1f}% return")
            
            if best['win_rate'] > 0.55:
                print(f"✅ Win Rate > 55% - GOOD!")
            else:
                print(f"⚠️  Win Rate < 55% - needs improvement")

if __name__ == "__main__":
    backtest = ComprehensiveBacktest()
    backtest.run_all_tests()
