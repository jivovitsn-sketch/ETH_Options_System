#!/usr/bin/env python3
"""
ГЕНЕРАТОР ДАШБОРДА МЕТРИК для Telegram
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import io
import base64

class TradingDashboard:
    def __init__(self):
        self.journal_file = Path('data/Enhanced_Trading_Journal.xlsx')
        self.output_dir = Path('data/dashboard_images')
        self.output_dir.mkdir(exist_ok=True)
        
        # Настройки стилей
        plt.style.use('dark_background')
        self.colors = {
            'profit': '#00ff88',
            'loss': '#ff4444', 
            'neutral': '#888888',
            'accent': '#00ccff'
        }
    
    def generate_monthly_dashboard(self):
        """Генерация месячного дашборда"""
        
        try:
            # Читаем данные
            trades_df = pd.read_excel(self.journal_file, sheet_name='trades')
            daily_df = pd.read_excel(self.journal_file, sheet_name='daily_summary')
            
            # Создаем фигуру с субплотами
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('📊 ETH OPTIONS TRADING DASHBOARD', fontsize=20, fontweight='bold', color='white')
            
            # 1. График P&L по времени
            self._plot_cumulative_pnl(trades_df, ax1)
            
            # 2. Win Rate статистика
            self._plot_win_rate_stats(trades_df, ax2)
            
            # 3. Распределение прибыли/убытков
            self._plot_pnl_distribution(trades_df, ax3)
            
            # 4. Ключевые метрики
            self._plot_key_metrics(trades_df, ax4)
            
            plt.tight_layout()
            
            # Сохраняем
            output_file = self.output_dir / f'dashboard_{datetime.now().strftime("%Y%m")}.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='black')
            plt.close()
            
            print(f"✅ Dashboard saved: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Dashboard generation error: {e}")
            return None
    
    def _plot_cumulative_pnl(self, df, ax):
        """График кумулятивной прибыли"""
        
        if len(df) == 0:
            ax.text(0.5, 0.5, 'No data yet', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('📈 Cumulative P&L')
            return
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df['cumulative_pnl'] = df['profit_loss'].cumsum()
        
        # Линия P&L
        ax.plot(df['date'], df['cumulative_pnl'], color=self.colors['accent'], linewidth=3, label='Total P&L')
        
        # Заливка прибыли/убытка
        ax.fill_between(df['date'], 0, df['cumulative_pnl'], 
                       where=(df['cumulative_pnl'] >= 0), color=self.colors['profit'], alpha=0.3)
        ax.fill_between(df['date'], 0, df['cumulative_pnl'], 
                       where=(df['cumulative_pnl'] < 0), color=self.colors['loss'], alpha=0.3)
        
        # Форматирование
        ax.set_title('📈 Cumulative P&L', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='white', linestyle='--', alpha=0.5)
        
        # Добавляем значение
        last_pnl = df['cumulative_pnl'].iloc[-1]
        color = self.colors['profit'] if last_pnl >= 0 else self.colors['loss']
        ax.text(0.02, 0.98, f'${last_pnl:.2f}', transform=ax.transAxes, 
                fontsize=16, fontweight='bold', color=color, va='top')
    
    def _plot_win_rate_stats(self, df, ax):
        """Статистика винрейта"""
        
        if len(df) == 0:
            ax.text(0.5, 0.5, 'No data yet', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('🎯 Win Rate')
            return
        
        wins = len(df[df['win_loss'] == 'WIN'])
        losses = len(df[df['win_loss'] == 'LOSS'])
        total = wins + losses
        
        if total == 0:
            return
        
        # Pie chart винрейта
        sizes = [wins, losses]
        colors = [self.colors['profit'], self.colors['loss']]
        labels = [f'Wins\n{wins}\n({wins/total*100:.1f}%)', f'Losses\n{losses}\n({losses/total*100:.1f}%)']
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='', startangle=90, textprops={'fontsize': 12})
        ax.set_title('🎯 Win Rate Distribution', fontsize=14, fontweight='bold')
        
        # Добавляем общий винрейт
        win_rate = wins / total * 100
        ax.text(0, -1.3, f'Overall: {win_rate:.1f}%', ha='center', va='center', 
                fontsize=16, fontweight='bold', color=self.colors['accent'])
    
    def _plot_pnl_distribution(self, df, ax):
        """Распределение прибыли/убытков"""
        
        if len(df) == 0:
            ax.text(0.5, 0.5, 'No data yet', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('💰 P&L Distribution')
            return
        
        profits = df[df['profit_loss'] > 0]['profit_loss']
        losses = df[df['profit_loss'] < 0]['profit_loss']
        
        # Гистограммы
        if len(profits) > 0:
            ax.hist(profits, bins=10, color=self.colors['profit'], alpha=0.7, label=f'Profits ({len(profits)})')
        
        if len(losses) > 0:
            ax.hist(losses, bins=10, color=self.colors['loss'], alpha=0.7, label=f'Losses ({len(losses)})')
        
        ax.set_title('💰 P&L Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('P&L ($)')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.axvline(x=0, color='white', linestyle='--', alpha=0.5)
    
    def _plot_key_metrics(self, df, ax):
        """Ключевые метрики"""
        
        # Скрываем оси
        ax.axis('off')
        
        if len(df) == 0:
            ax.text(0.5, 0.5, 'No data yet', ha='center', va='center', transform=ax.transAxes)
            return
        
        # Рассчитываем метрики
        total_trades = len(df)
        wins = len(df[df['win_loss'] == 'WIN'])
        win_rate = wins / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = df['profit_loss'].sum()
        avg_trade = df['profit_loss'].mean()
        best_trade = df['profit_loss'].max()
        worst_trade = df['profit_loss'].min()
        
        profit_trades = df[df['profit_loss'] > 0]['profit_loss']
        loss_trades = df[df['profit_loss'] < 0]['profit_loss']
        
        profit_factor = profit_trades.sum() / abs(loss_trades.sum()) if len(loss_trades) > 0 else float('inf')
        
        # Текст метрик
        metrics_text = f"""
📊 KEY METRICS

🎯 Total Trades: {total_trades}
📈 Win Rate: {win_rate:.1f}%
💰 Total P&L: ${total_pnl:.2f}
📊 Avg Trade: ${avg_trade:.2f}

🏆 Best Trade: ${best_trade:.2f}
📉 Worst Trade: ${worst_trade:.2f}
⚖️ Profit Factor: {profit_factor:.2f}

🔥 Strategy: 60 DTE Bull Calls
⏰ Timeframe: 4H
🎲 Based on Order Blocks
        """
        
        # Цвет для общего P&L
        pnl_color = self.colors['profit'] if total_pnl >= 0 else self.colors['loss']
        
        ax.text(0.1, 0.9, metrics_text, transform=ax.transAxes, fontsize=12, 
                va='top', ha='left', color='white', fontfamily='monospace')
        
        # Выделяем P&L
        ax.text(0.6, 0.5, f'${total_pnl:.2f}', transform=ax.transAxes, 
                fontsize=32, fontweight='bold', color=pnl_color, ha='center', va='center')
    
    def create_fomo_summary(self, df):
        """Создание FOMO-сводки для Telegram"""
        
        if len(df) == 0:
            return "📊 No trading data available yet. Start trading to see results!"
        
        # Основные метрики
        total_trades = len(df)
        wins = len(df[df['win_loss'] == 'WIN'])
        win_rate = wins / total_trades * 100
        total_pnl = df['profit_loss'].sum()
        
        # Последний месяц
        last_month = df[pd.to_datetime(df['date']) >= datetime.now() - timedelta(days=30)]
        monthly_pnl = last_month['profit_loss'].sum() if len(last_month) > 0 else 0
        
        # Эмоджи по результатам
        trend_emoji = "🚀" if total_pnl > 0 else "📉" if total_pnl < 0 else "⚖️"
        
        # FOMO текст (но честный)
        fomo_text = f"""
{trend_emoji} ETH OPTIONS RESULTS

📊 Performance:
- Total Trades: {total_trades}
- Win Rate: {win_rate:.1f}%
- Total P&L: ${total_pnl:.2f}

📅 Last 30 Days: ${monthly_pnl:.2f}

⚡ Strategy: 60 DTE Bull Call Spreads
🎯 Based on Order Blocks signals

⚠️ RISK WARNING:
- Past performance ≠ future results
- Options trading involves high risk
- Only trade with money you can lose
- This is for educational purposes

💡 Paper trading recommended first
        """
        
        return fomo_text.strip()

# Тест дашборда
if __name__ == "__main__":
    dashboard = TradingDashboard()
    
    # Генерируем дашборд
    image_file = dashboard.generate_monthly_dashboard()
    
    if image_file:
        print(f"✅ Dashboard created: {image_file}")
    else:
        print("❌ Dashboard creation failed")
