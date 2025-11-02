#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIXED OPTIONS BACKTEST
Исправлена логика: exit только для того же актива
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class OptionsBacktestFixed:
    """Исправленный опционный бэктест"""
    
    def __init__(self):
        self.db_path = './data/signal_history.db'
        self.commission = 0.0003
    
    def load_signals(self) -> Dict[str, List[Dict]]:
        """Загрузить сигналы, сгруппированные по активам"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                timestamp,
                asset,
                signal_type,
                confidence,
                spot_price,
                data_snapshot_json
            FROM signal_history
            WHERE signal_type IN ('BULLISH', 'BEARISH')
            ORDER BY timestamp ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Группируем по активам
        by_asset = {}
        
        for row in rows:
            try:
                asset = row[1]
                
                if asset not in by_asset:
                    by_asset[asset] = []
                
                by_asset[asset].append({
                    'timestamp': row[0],
                    'datetime': datetime.fromtimestamp(row[0]),
                    'asset': asset,
                    'signal_type': row[2],
                    'confidence': row[3],
                    'spot_price': row[4]
                })
            except:
                pass
        
        return by_asset
    
    def backtest_option(self, entry_signal: Dict, exit_signal: Optional[Dict], dte: int = 7) -> Dict:
        """Бэктест одного опциона"""
        
        entry_time = entry_signal['datetime']
        entry_price = entry_signal['spot_price']
        signal_type = entry_signal['signal_type']
        
        # Страйк выбор
        if signal_type == 'BULLISH':
            strike = entry_price * 1.02  # 2% OTM Call
            option_type = 'Call'
        else:
            strike = entry_price * 0.98  # 2% OTM Put
            option_type = 'Put'
        
        # Премия (упрощённая формула)
        if dte <= 3:
            premium_pct = 0.02
        elif dte <= 7:
            premium_pct = 0.03
        else:
            premium_pct = 0.05
        
        premium = entry_price * premium_pct
        cost = premium * (1 + self.commission)
        
        # EXIT
        if exit_signal:
            exit_time = exit_signal['datetime']
            exit_price = exit_signal['spot_price']
            
            days_held = (exit_time - entry_time).total_seconds() / 86400
            
            # До экспирации?
            if days_held >= dte:
                # Экспирация
                if option_type == 'Call':
                    intrinsic = max(0, exit_price - strike)
                else:
                    intrinsic = max(0, strike - exit_price)
                
                revenue = intrinsic * (1 - self.commission)
                reason = 'EXPIRATION'
            else:
                # Досрочный выход
                remaining_dte = max(0, dte - days_held)
                time_factor = remaining_dte / dte
                
                if option_type == 'Call':
                    intrinsic = max(0, exit_price - strike)
                else:
                    intrinsic = max(0, strike - exit_price)
                
                # Extrinsic value (theta decay)
                extrinsic = premium * time_factor * 0.3
                
                revenue = (intrinsic + extrinsic) * (1 - self.commission)
                reason = 'EARLY_EXIT'
        else:
            # Нет exit сигнала - держим до экспирации
            exit_time = entry_time + timedelta(days=dte)
            
            # Симулируем цену (можем взять из futures data)
            # Пока берём +2% от entry
            exit_price = entry_price * 1.02 if signal_type == 'BULLISH' else entry_price * 0.98
            
            if option_type == 'Call':
                intrinsic = max(0, exit_price - strike)
            else:
                intrinsic = max(0, strike - exit_price)
            
            revenue = intrinsic * (1 - self.commission)
            reason = 'NO_EXIT_SIGNAL'
        
        # PnL
        pnl = revenue - cost
        pnl_pct = (pnl / cost) * 100 if cost > 0 else -100
        
        return {
            'entry_time': entry_time,
            'exit_time': exit_time,
            'asset': entry_signal['asset'],
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
        """Запуск исправленного бэктеста"""
        by_asset = self.load_signals()
        
        if not by_asset:
            print("❌ Нет сигналов!")
            return
        
        print(f"📝 Активов: {len(by_asset)}")
        for asset, signals in by_asset.items():
            print(f"  {asset}: {len(signals)} сигналов")
        
        all_trades = []
        
        # Бэктест по каждому активу отдельно
        for asset, signals in by_asset.items():
            print(f"\n{'='*60}")
            print(f"📊 {asset}")
            print('='*60)
            
            for i, signal in enumerate(signals):
                # Exit = следующий сигнал ЭТОГО ЖЕ актива
                exit_signal = signals[i + 1] if i + 1 < len(signals) else None
                
                trade = self.backtest_option(signal, exit_signal, dte=7)
                all_trades.append(trade)
                
                status = "✅" if trade['win'] else "❌"
                print(f"  {status} {trade['option_type']}: {trade['pnl_pct']:+.1f}% | {trade['exit_reason']}")
        
        # Анализ
        self.analyze(all_trades)
    
    def analyze(self, trades: List[Dict]):
        """Анализ результатов"""
        
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ (ИСПРАВЛЕННЫЕ)")
        print("=" * 80)
        
        wins = [t for t in trades if t['win']]
        losses = [t for t in trades if not t['win']]
        
        print(f"\n🎯 СТАТИСТИКА:")
        print(f"  Всего сделок: {len(trades)}")
        print(f"  Прибыльных: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)")
        print(f"  Убыточных: {len(losses)} ({len(losses)/len(trades)*100:.1f}%)")
        
        if wins:
            avg_win = sum(t['pnl_pct'] for t in wins) / len(wins)
            print(f"  Средний профит: +{avg_win:.2f}%")
        
        if losses:
            avg_loss = sum(t['pnl_pct'] for t in losses) / len(losses)
            print(f"  Средний убыток: {avg_loss:.2f}%")
        
        total_pnl = sum(t['pnl_pct'] for t in trades)
        print(f"  Общий PnL: {total_pnl:.2f}%")
        
        if wins and losses and sum(t['pnl'] for t in losses) != 0:
            pf = abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses))
            print(f"  Profit Factor: {pf:.2f}")
        
        # По активам
        by_asset = {}
        for t in trades:
            asset = t['asset']
            if asset not in by_asset:
                by_asset[asset] = []
            by_asset[asset].append(t)
        
        print(f"\n📊 ПО АКТИВАМ:")
        for asset, asset_trades in by_asset.items():
            asset_wins = [t for t in asset_trades if t['win']]
            asset_pnl = sum(t['pnl_pct'] for t in asset_trades)
            wr = len(asset_wins) / len(asset_trades) * 100 if asset_trades else 0
            
            print(f"  {asset}: {len(asset_trades)} сделок | WR {wr:.0f}% | PnL {asset_pnl:+.1f}%")
        
        print("\n" + "=" * 80)


if __name__ == '__main__':
    print("=" * 80)
    print("🎯 ИСПРАВЛЕННЫЙ ОПЦИОННЫЙ БЭКТЕСТ")
    print("=" * 80)
    
    bt = OptionsBacktestFixed()
    bt.run_backtest()
