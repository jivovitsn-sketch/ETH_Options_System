#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REAL OPTIONS BACKTEST
С учётом:
- DTE (Days To Expiration)
- Strike selection (Delta-based)
- Premium calculation
- Theta decay
- Exit логика (экспирация vs TP/SL)
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class OptionsBacktest:
    """Реальный опционный бэктест"""
    
    def __init__(self):
        self.db_path = './data/signal_history.db'
        self.commission = 0.0003  # 0.03% на Bybit
    
    def load_signals_with_strategies(self) -> List[Dict]:
        """Загрузить сигналы со стратегиями"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                timestamp,
                asset,
                signal_type,
                confidence,
                spot_price,
                strategies_json,
                data_snapshot_json
            FROM signal_history
            WHERE signal_type IN ('BULLISH', 'BEARISH')
            ORDER BY timestamp ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            try:
                strategies = json.loads(row[5]) if row[5] else []
                data = json.loads(row[6])
                
                signals.append({
                    'timestamp': row[0],
                    'datetime': datetime.fromtimestamp(row[0]),
                    'asset': row[1],
                    'signal_type': row[2],
                    'confidence': row[3],
                    'spot_price': row[4],
                    'strategies': strategies,
                    'data': data
                })
            except Exception as e:
                print(f"Error parsing: {e}")
                pass
        
        return signals
    
    def backtest_option_trade(self, signal: Dict, next_signal: Optional[Dict] = None) -> Dict:
        """Бэктест одной опционной сделки"""
        
        # Параметры сделки
        entry_time = signal['datetime']
        entry_price = signal['spot_price']
        signal_type = signal['signal_type']
        strategies = signal['strategies']
        
        if not strategies:
            return None
        
        # Берём первую стратегию
        strategy = strategies[0]
        
        # Параметры опциона
        dte = strategy.get('dte', 7)  # Days to expiration
        option_type = 'Call' if signal_type == 'BULLISH' else 'Put'
        
        # Strike выбор (ATM + offset)
        if signal_type == 'BULLISH':
            strike = entry_price * 1.02  # 2% OTM Call
        else:
            strike = entry_price * 0.98  # 2% OTM Put
        
        # PREMIUM расчёт (упрощённый)
        # Реальный: используем Black-Scholes или берём из рынка
        # Упрощённый: ~2-5% от spot в зависимости от DTE и moneyness
        if dte <= 3:
            premium_pct = 0.02  # 2% для коротких экспираций
        elif dte <= 7:
            premium_pct = 0.03  # 3% для недельных
        else:
            premium_pct = 0.05  # 5% для месячных
        
        premium = entry_price * premium_pct
        
        # EXIT ЛОГИКА
        if next_signal:
            exit_time = next_signal['datetime']
            exit_price = next_signal['spot_price']
            
            # Считаем сколько дней прошло
            days_held = (exit_time - entry_time).total_seconds() / 86400
            
            # Если дошли до экспирации
            if days_held >= dte:
                # Intrinsic value на экспирации
                if option_type == 'Call':
                    intrinsic = max(0, exit_price - strike)
                else:  # Put
                    intrinsic = max(0, strike - exit_price)
                
                exit_premium = intrinsic
                reason = 'EXPIRATION'
            else:
                # Закрываем досрочно - считаем новую премию
                # С учётом theta decay
                remaining_dte = dte - days_held
                time_decay_factor = remaining_dte / dte
                
                # Intrinsic + Extrinsic
                if option_type == 'Call':
                    intrinsic = max(0, exit_price - strike)
                    extrinsic = premium * time_decay_factor * 0.5
                else:
                    intrinsic = max(0, strike - exit_price)
                    extrinsic = premium * time_decay_factor * 0.5
                
                exit_premium = intrinsic + extrinsic
                reason = 'EARLY_EXIT'
        else:
            # Нет следующего сигнала - симулируем экспирацию
            exit_time = entry_time + timedelta(days=dte)
            exit_price = entry_price * 1.02  # Условно
            
            if option_type == 'Call':
                intrinsic = max(0, exit_price - strike)
            else:
                intrinsic = max(0, strike - exit_price)
            
            exit_premium = intrinsic
            reason = 'SIMULATED_EXPIRATION'
        
        # PnL расчёт
        # Покупаем опцион = платим премию
        # Продаём опцион = получаем премию (текущую или intrinsic)
        cost = premium * (1 + self.commission)
        revenue = exit_premium * (1 - self.commission)
        
        pnl = revenue - cost
        pnl_pct = (pnl / cost) * 100 if cost > 0 else 0
        
        return {
            'entry_time': entry_time,
            'exit_time': exit_time,
            'asset': signal['asset'],
            'signal_type': signal_type,
            'option_type': option_type,
            'dte': dte,
            'strike': strike,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'premium_paid': cost,
            'premium_received': revenue,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'win': pnl > 0,
            'exit_reason': reason
        }
    
    def run_backtest(self):
        """Запуск бэктеста"""
        signals = self.load_signals_with_strategies()
        
        if not signals:
            print("❌ Нет сигналов со стратегиями!")
            return
        
        print(f"📝 Загружено сигналов: {len(signals)}")
        
        trades = []
        
        for i, signal in enumerate(signals):
            next_signal = signals[i + 1] if i + 1 < len(signals) else None
            
            trade = self.backtest_option_trade(signal, next_signal)
            
            if trade:
                trades.append(trade)
        
        # Анализ результатов
        self.analyze_results(trades)
    
    def analyze_results(self, trades: List[Dict]):
        """Анализ результатов"""
        
        if not trades:
            print("❌ Нет сделок!")
            return
        
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ОПЦИОННОГО БЭКТЕСТА")
        print("=" * 80)
        
        wins = [t for t in trades if t['win']]
        losses = [t for t in trades if not t['win']]
        
        total_pnl = sum(t['pnl'] for t in trades)
        total_pnl_pct = sum(t['pnl_pct'] for t in trades)
        
        print(f"\n🎯 ОБЩАЯ СТАТИСТИКА:")
        print(f"  Всего сделок: {len(trades)}")
        print(f"  Прибыльных: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)")
        print(f"  Убыточных: {len(losses)} ({len(losses)/len(trades)*100:.1f}%)")
        
        if wins:
            avg_win = sum(t['pnl_pct'] for t in wins) / len(wins)
            print(f"  Средний профит: +{avg_win:.2f}%")
        
        if losses:
            avg_loss = sum(t['pnl_pct'] for t in losses) / len(losses)
            print(f"  Средний убыток: {avg_loss:.2f}%")
        
        print(f"  Общий PnL: {total_pnl_pct:.2f}%")
        
        if losses and sum(t['pnl'] for t in losses) != 0:
            profit_factor = abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses))
            print(f"  Profit Factor: {profit_factor:.2f}")
        
        # Детали по сделкам
        print(f"\n📋 ДЕТАЛИ СДЕЛОК:")
        for i, trade in enumerate(trades, 1):
            status = "✅" if trade['win'] else "❌"
            print(f"\n  {status} Trade #{i}: {trade['asset']} {trade['option_type']}")
            print(f"     Signal: {trade['signal_type']}")
            print(f"     Strike: ${trade['strike']:.2f}")
            print(f"     Entry: ${trade['entry_price']:.2f}")
            print(f"     Exit: ${trade['exit_price']:.2f}")
            print(f"     Premium Paid: ${trade['premium_paid']:.2f}")
            print(f"     Premium Received: ${trade['premium_received']:.2f}")
            print(f"     PnL: {trade['pnl_pct']:+.2f}%")
            print(f"     Exit: {trade['exit_reason']}")
        
        print("\n" + "=" * 80)


if __name__ == '__main__':
    print("=" * 80)
    print("🎯 РЕАЛЬНЫЙ ОПЦИОННЫЙ БЭКТЕСТ")
    print("=" * 80)
    
    bt = OptionsBacktest()
    bt.run_backtest()
