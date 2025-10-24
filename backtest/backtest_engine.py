#!/usr/bin/env python3
"""
BACKTEST ENGINE V20.2
Полноценный бэктест с Ensemble + Options
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import yaml

from ml.ensemble_combiner import EnsembleCombiner

class BacktestEngine:
    """
    Бэктестинг системы с опционными конструкциями
    """
    
    def __init__(self):
        # Load configs
        config_path = Path(__file__).parent.parent / 'configs' / 'strategies.yaml'
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        # Ensemble
        self.ensemble = EnsembleCombiner()
        
        # Load ML models
        model_path = Path(__file__).parent.parent / 'ml_agent_models_multi.pkl'
        if model_path.exists():
            self.ensemble.load_ml_models(str(model_path))
            print("✅ ML models loaded")
        else:
            print("⚠️  No ML models found")
        
        # Trading params
        self.initial_capital = 10000
        self.position_size_pct = 0.05  # 5% per trade
        
        # Results
        self.trades = []
        self.equity_curve = []
        
        print("✅ Backtest Engine initialized")
    
    def load_data(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """Загрузить исторические данные"""
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / symbol
        
        if not data_dir.exists():
            print(f"⚠️  No data for {symbol}")
            return pd.DataFrame()
        
        files = sorted(data_dir.glob("*.csv"))[-days:]
        
        if not files:
            print(f"⚠️  No CSV files for {symbol}")
            return pd.DataFrame()
        
        dfs = []
        for file in files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        price_df = pd.concat(dfs, ignore_index=True)
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        price_df = price_df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"✅ Loaded {len(price_df)} candles for {symbol}")
        return price_df
    
    def calculate_option_pnl(self, construction: str, entry_price: float, 
                            exit_price: float, direction: str) -> float:
        """
        Симуляция P&L опционной конструкции
        
        Упрощённая модель:
        - Bull Call Spread: прибыль если цена выросла
        - Bear Put Spread: прибыль если цена упала
        - Max profit = 100% (достиг TP3)
        - Max loss = -50% (достиг SL)
        """
        
        price_change = (exit_price - entry_price) / entry_price
        
        if construction == 'bull_call_spread':
            if price_change > 0.02:  # TP3: +2%
                return 1.0  # +100% profit
            elif price_change > 0.01:  # TP2: +1%
                return 0.5  # +50%
            elif price_change > 0.005:  # TP1: +0.5%
                return 0.25  # +25%
            elif price_change < -0.01:  # SL: -1%
                return -0.5  # -50% loss
            else:
                return price_change * 20  # Scaled P&L
        
        elif construction == 'bear_put_spread':
            if price_change < -0.02:  # TP3
                return 1.0
            elif price_change < -0.01:  # TP2
                return 0.5
            elif price_change < -0.005:  # TP1
                return 0.25
            elif price_change > 0.01:  # SL
                return -0.5
            else:
                return -price_change * 20
        
        else:
            return 0.0
    
    def run_backtest(self, symbol: str = 'BTCUSDT', days: int = 60):
        """
        Запустить бэктест
        """
        
        print(f"\n{'='*70}")
        print(f"🚀 BACKTEST: {symbol} | {days} days")
        print(f"{'='*70}")
        
        # Load data
        df = self.load_data(symbol, days)
        
        if df.empty:
            print("❌ No data for backtest")
            return
        
        # Resample to hourly
        df.set_index('timestamp', inplace=True)
        hourly = df.resample('1H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        hourly.reset_index(inplace=True)
        
        print(f"📊 Hourly candles: {len(hourly)}")
        
        # Trading vars
        capital = self.initial_capital
        position = None
        
        # Loop through time
        for i in range(100, len(hourly) - 24):  # Need 100 for features, 24 for outcome
            
            current_time = hourly.iloc[i]['timestamp']
            current_price = hourly.iloc[i]['close']
            
            # Get window for prediction
            window = hourly.iloc[i-100:i].copy()
            
            # Context
            context = {
                'trend': 'NEUTRAL',
                'astro_direction_str': 'NEUTRAL',
                'oi_pcr': 1.0,
                'iv': 0.5
            }
            
            # Get ensemble prediction
            try:
                prediction = self.ensemble.predict(window, context)
                signal = prediction['prediction']
                confidence = prediction['confidence']
            except Exception as e:
                signal = 'NEUTRAL'
                confidence = 0.5
            
            # Close existing position if holding for 24h
            if position and (i - position['entry_idx']) >= 24:
                exit_price = current_price
                pnl_pct = self.calculate_option_pnl(
                    position['construction'],
                    position['entry_price'],
                    exit_price,
                    position['direction']
                )
                
                pnl_dollars = position['size'] * pnl_pct
                capital += pnl_dollars
                
                self.trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': current_time,
                    'direction': position['direction'],
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'pnl_pct': pnl_pct,
                    'pnl_dollars': pnl_dollars,
                    'capital': capital
                })
                
                position = None
            
            # Open new position if signal
            if position is None and signal != 'NEUTRAL' and confidence > 0.50:
                
                construction = 'bull_call_spread' if signal == 'BULLISH' else 'bear_put_spread'
                position_size = capital * self.position_size_pct
                
                position = {
                    'entry_idx': i,
                    'entry_time': current_time,
                    'entry_price': current_price,
                    'direction': signal,
                    'construction': construction,
                    'size': position_size,
                    'confidence': confidence
                }
            
            # Record equity
            self.equity_curve.append({
                'timestamp': current_time,
                'capital': capital
            })
        
        # Close final position if exists
        if position:
            exit_price = hourly.iloc[-1]['close']
            pnl_pct = self.calculate_option_pnl(
                position['construction'],
                position['entry_price'],
                exit_price,
                position['direction']
            )
            pnl_dollars = position['size'] * pnl_pct
            capital += pnl_dollars
            
            self.trades.append({
                'entry_time': position['entry_time'],
                'exit_time': hourly.iloc[-1]['timestamp'],
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'pnl_pct': pnl_pct,
                'pnl_dollars': pnl_dollars,
                'capital': capital
            })
        
        # Calculate metrics
        self.calculate_metrics()
    
    def calculate_metrics(self):
        """Расчёт метрик"""
        
        if not self.trades:
            print("\n❌ No trades executed")
            return
        
        trades_df = pd.DataFrame(self.trades)
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl_dollars'] > 0])
        losing_trades = len(trades_df[trades_df['pnl_dollars'] < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl_dollars'].sum()
        final_capital = trades_df.iloc[-1]['capital']
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        avg_win = trades_df[trades_df['pnl_dollars'] > 0]['pnl_dollars'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl_dollars'] < 0]['pnl_dollars'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 else 0
        
        # Sharpe Ratio (simplified)
        returns = trades_df['pnl_pct'].values
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 else 0
        
        # Print results
        print(f"\n{'='*70}")
        print(f"📊 BACKTEST RESULTS")
        print(f"{'='*70}")
        print(f"Initial Capital:    ${self.initial_capital:,.2f}")
        print(f"Final Capital:      ${final_capital:,.2f}")
        print(f"Total P&L:          ${total_pnl:,.2f}")
        print(f"Total Return:       {total_return*100:.2f}%")
        print(f"\nTotal Trades:       {total_trades}")
        print(f"Winning Trades:     {winning_trades}")
        print(f"Losing Trades:      {losing_trades}")
        print(f"Win Rate:           {win_rate*100:.2f}%")
        print(f"\nAvg Win:            ${avg_win:.2f}")
        print(f"Avg Loss:           ${avg_loss:.2f}")
        print(f"Profit Factor:      {profit_factor:.2f}")
        print(f"Sharpe Ratio:       {sharpe:.2f}")
        print(f"{'='*70}")
        
        # Save results
        trades_df.to_csv('backtest_trades.csv', index=False)
        print(f"\n💾 Trades saved to backtest_trades.csv")


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════╗")
    print("║       BACKTEST ENGINE V20.2                   ║")
    print("╚════════════════════════════════════════════════╝")
    
    engine = BacktestEngine()
    
    # Run backtest
    engine.run_backtest(symbol='BTCUSDT', days=60)
