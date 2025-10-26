#!/usr/bin/env python3
"""
ЖУРНАЛ СДЕЛОК с автоматическими метриками и дашбордом
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import LineChart, Reference

class TradingJournal:
    def __init__(self):
        self.journal_file = Path('data/Enhanced_Trading_Journal.xlsx')
        self.metrics_file = Path('data/trading_metrics.json')
        
        # Создаем структуру журнала
        self.init_journal()
        
    def init_journal(self):
        """Инициализация структуры журнала"""
        
        # Структура данных
        self.columns = {
            'trades': [
                'date', 'time', 'asset', 'signal', 'strategy', 
                'entry_price', 'exit_price', 'position_size', 
                'cost', 'profit_loss', 'roi_percent',
                'delta', 'theta', 'win_loss', 'confidence',
                'notes', 'candle_timeframe'
            ],
            'daily_summary': [
                'date', 'trades_count', 'wins', 'losses', 
                'win_rate', 'daily_pnl', 'cumulative_pnl',
                'best_trade', 'worst_trade', 'avg_trade'
            ],
            'monthly_metrics': [
                'month', 'total_trades', 'win_rate', 'profit_factor',
                'total_pnl', 'avg_monthly_return', 'max_drawdown',
                'sharpe_ratio', 'sortino_ratio', 'calmar_ratio'
            ]
        }
        
        print("📊 Trading Journal initialized")
        print(f"   File: {self.journal_file}")
        print(f"   Sheets: {list(self.columns.keys())}")
    
    def add_trade(self, trade_data):
        """Добавление новой сделки"""
        
        # Обрабатываем данные сделки
        trade_record = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'asset': trade_data.get('asset', 'ETHUSDT'),
            'signal': trade_data.get('signal', 'BUY'),
            'strategy': trade_data.get('strategy', '60_DTE_Bull_Call'),
            'entry_price': trade_data.get('entry', 0),
            'exit_price': trade_data.get('exit', 0),
            'position_size': trade_data.get('size', 89),
            'cost': trade_data.get('cost', 89),
            'profit_loss': self._calculate_pnl(trade_data),
            'roi_percent': self._calculate_roi(trade_data),
            'delta': trade_data.get('delta', 0.071),
            'theta': trade_data.get('theta', 0.05),
            'win_loss': 'WIN' if self._calculate_pnl(trade_data) > 0 else 'LOSS',
            'confidence': trade_data.get('confidence', 'MEDIUM'),
            'notes': trade_data.get('notes', ''),
            'candle_timeframe': '4H'
        }
        
        # Сохраняем в Excel
        self._save_to_excel(trade_record, 'trades')
        
        # Обновляем дневную сводку
        self._update_daily_summary()
        
        print(f"✅ Trade added: {trade_record['signal']} {trade_record['asset']} @ ${trade_record['entry_price']}")
        
        return trade_record
    
    def _calculate_pnl(self, trade_data):
        """Расчет P&L"""
        if trade_data.get('exit', 0) > 0:
            entry = trade_data.get('entry', 0)
            exit = trade_data.get('exit', 0)
            size = trade_data.get('size', 89)
            
            # Для опционных спредов
            if 'Bull_Call' in trade_data.get('strategy', ''):
                # Максимальная прибыль = $200 (из backtest)
                price_change = (exit - entry) / entry
                return min(price_change * size * 2.25, 200)  # Левередж эффект
        
        return 0  # Открытая позиция
    
    def _calculate_roi(self, trade_data):
        """Расчет ROI"""
        pnl = self._calculate_pnl(trade_data)
        cost = trade_data.get('cost', 89)
        return (pnl / cost * 100) if cost > 0 else 0
    
    def _save_to_excel(self, data, sheet_name):
        """Сохранение в Excel"""
        
        # Читаем существующие данные или создаем новый файл
        if self.journal_file.exists():
            try:
                existing_df = pd.read_excel(self.journal_file, sheet_name=sheet_name)
                df = pd.concat([existing_df, pd.DataFrame([data])], ignore_index=True)
            except:
                df = pd.DataFrame([data])
        else:
            df = pd.DataFrame([data])
        
        # Сохраняем с форматированием
        with pd.ExcelWriter(self.journal_file, engine='openpyxl', mode='a' if self.journal_file.exists() else 'w') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Форматирование
            worksheet = writer.sheets[sheet_name]
            
            # Заголовки
            for cell in worksheet[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    def _update_daily_summary(self):
        """Обновление дневной сводки"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Читаем сделки за сегодня
        try:
            trades_df = pd.read_excel(self.journal_file, sheet_name='trades')
            today_trades = trades_df[trades_df['date'] == today]
            
            if len(today_trades) > 0:
                summary = {
                    'date': today,
                    'trades_count': len(today_trades),
                    'wins': len(today_trades[today_trades['win_loss'] == 'WIN']),
                    'losses': len(today_trades[today_trades['win_loss'] == 'LOSS']),
                    'win_rate': len(today_trades[today_trades['win_loss'] == 'WIN']) / len(today_trades) * 100,
                    'daily_pnl': today_trades['profit_loss'].sum(),
                    'best_trade': today_trades['profit_loss'].max(),
                    'worst_trade': today_trades['profit_loss'].min(),
                    'avg_trade': today_trades['profit_loss'].mean()
                }
                
                # Кумулятивный P&L
                all_trades = pd.read_excel(self.journal_file, sheet_name='trades')
                summary['cumulative_pnl'] = all_trades['profit_loss'].sum()
                
                self._save_to_excel(summary, 'daily_summary')
                
        except Exception as e:
            print(f"Error updating daily summary: {e}")
    
    def generate_monthly_report(self):
        """Генерация месячного отчета"""
        
        try:
            trades_df = pd.read_excel(self.journal_file, sheet_name='trades')
            
            # Группируем по месяцам
            trades_df['date'] = pd.to_datetime(trades_df['date'])
            trades_df['month'] = trades_df['date'].dt.to_period('M')
            
            monthly_stats = []
            
            for month, group in trades_df.groupby('month'):
                wins = len(group[group['win_loss'] == 'WIN'])
                losses = len(group[group['win_loss'] == 'LOSS'])
                
                stats = {
                    'month': str(month),
                    'total_trades': len(group),
                    'win_rate': wins / len(group) * 100 if len(group) > 0 else 0,
                    'total_pnl': group['profit_loss'].sum(),
                    'avg_monthly_return': group['roi_percent'].mean(),
                    'max_drawdown': self._calculate_max_drawdown(group),
                    'profit_factor': self._calculate_profit_factor(group),
                    'sharpe_ratio': self._calculate_sharpe(group),
                    'sortino_ratio': self._calculate_sortino(group),
                    'calmar_ratio': self._calculate_calmar(group)
                }
                
                monthly_stats.append(stats)
            
            # Сохраняем месячную статистику
            monthly_df = pd.DataFrame(monthly_stats)
            
            with pd.ExcelWriter(self.journal_file, engine='openpyxl', mode='a') as writer:
                monthly_df.to_excel(writer, sheet_name='monthly_metrics', index=False)
            
            return monthly_df
            
        except Exception as e:
            print(f"Error generating monthly report: {e}")
            return pd.DataFrame()
    
    def _calculate_max_drawdown(self, trades):
        """Расчет максимальной просадки"""
        cumulative = trades['profit_loss'].cumsum()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        return drawdown.min()
    
    def _calculate_profit_factor(self, trades):
        """Profit Factor"""
        profits = trades[trades['profit_loss'] > 0]['profit_loss'].sum()
        losses = abs(trades[trades['profit_loss'] < 0]['profit_loss'].sum())
        return profits / losses if losses > 0 else float('inf')
    
    def _calculate_sharpe(self, trades):
        """Sharpe Ratio"""
        returns = trades['roi_percent'] / 100
        return returns.mean() / returns.std() if returns.std() > 0 else 0
    
    def _calculate_sortino(self, trades):
        """Sortino Ratio"""
        returns = trades['roi_percent'] / 100
        negative_returns = returns[returns < 0]
        downside_std = negative_returns.std() if len(negative_returns) > 0 else 0.001
        return returns.mean() / downside_std if downside_std > 0 else 0
    
    def _calculate_calmar(self, trades):
        """Calmar Ratio"""
        annual_return = trades['roi_percent'].mean() * 12  # Аннуализированная доходность
        max_dd = abs(self._calculate_max_drawdown(trades))
        return annual_return / max_dd if max_dd > 0 else 0

# Тест журнала
if __name__ == "__main__":
    journal = TradingJournal()
    
    # Тестовая сделка
    test_trade = {
        'asset': 'ETHUSDT',
        'signal': 'BUY',
        'strategy': '60_DTE_Bull_Call',
        'entry': 3900,
        'exit': 4100,  # Закрытая сделка
        'size': 89,
        'cost': 89,
        'delta': 0.071,
        'theta': 0.05,
        'confidence': 'HIGH'
    }
    
    journal.add_trade(test_trade)
    print("✅ Test trade added to journal")
