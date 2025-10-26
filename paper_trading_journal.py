#!/usr/bin/env python3
import pandas as pd
import json
from datetime import datetime, timedelta

class PaperTradingJournal:
    def __init__(self):
        self.journal_file = 'data/paper_trades.csv'
        self.portfolio_file = 'data/portfolio_status.json'
        
        # Стартовый капитал для paper trading
        self.initial_capital = 50000  # $50k
        
        # Инициализируем файлы если их нет
        self._initialize_files()
    
    def _initialize_files(self):
        """Инициализация файлов журнала"""
        try:
            pd.read_csv(self.journal_file)
        except:
            # Создаем пустой журнал
            empty_journal = pd.DataFrame(columns=[
                'trade_id', 'timestamp', 'strategy', 'asset', 'action',
                'entry_price', 'exit_price', 'dte', 'position_size',
                'long_strike', 'short_strike', 'premium_paid', 'premium_received',
                'pnl', 'pnl_percent', 'status', 'exit_reason', 'notes'
            ])
            empty_journal.to_csv(self.journal_file, index=False)
        
        try:
            with open(self.portfolio_file) as f:
                json.load(f)
        except:
            # Создаем стартовое портфолио
            portfolio = {
                'cash': self.initial_capital,
                'total_value': self.initial_capital,
                'open_positions': [],
                'total_trades': 0,
                'winning_trades': 0,
                'total_pnl': 0,
                'created': datetime.now().isoformat()
            }
            with open(self.portfolio_file, 'w') as f:
                json.dump(portfolio, f, indent=2)
    
    def open_trade(self, strategy, asset, entry_price, dte=45, position_size=5000, 
                   long_strike=None, short_strike=None, notes=""):
        """Открыть новую сделку"""
        
        trade_id = f"{asset}_{strategy}_{datetime.now().strftime('%m%d_%H%M')}"
        
        # Расчет премии на основе стратегии
        if strategy == "Long Straddle":
            premium_paid = entry_price * 0.08 * (position_size / entry_price)
            premium_received = 0
        elif strategy in ["Bull Call Spread", "Bear Put Spread"]:
            premium_paid = position_size * 0.3  # 30% от позиции
            premium_received = 0
        elif strategy == "Iron Condor":
            premium_paid = 0
            premium_received = position_size * 0.05  # Получаем кредит
        else:
            premium_paid = position_size * 0.2
            premium_received = 0
        
        new_trade = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy,
            'asset': asset,
            'action': 'OPEN',
            'entry_price': entry_price,
            'exit_price': None,
            'dte': dte,
            'position_size': position_size,
            'long_strike': long_strike,
            'short_strike': short_strike,
            'premium_paid': premium_paid,
            'premium_received': premium_received,
            'pnl': 0,
            'pnl_percent': 0,
            'status': 'OPEN',
            'exit_reason': None,
            'notes': notes
        }
        
        # Добавляем в журнал
        df = pd.read_csv(self.journal_file)
        new_df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
        new_df.to_csv(self.journal_file, index=False)
        
        # Обновляем портфолио
        self._update_portfolio_on_open(new_trade)
        
        print(f"✅ TRADE OPENED: {trade_id}")
        print(f"Strategy: {strategy}")
        print(f"Asset: {asset} @ ${entry_price:,.2f}")
        print(f"Position Size: ${position_size:,.0f}")
        print(f"Premium: ${premium_paid:.0f} paid, ${premium_received:.0f} received")
        
        return trade_id
    
    def close_trade(self, trade_id, exit_price, exit_reason="Manual"):
        """Закрыть сделку"""
        
        df = pd.read_csv(self.journal_file)
        trade_index = df[df['trade_id'] == trade_id].index
        
        if len(trade_index) == 0:
            print(f"❌ Trade {trade_id} not found")
            return
        
        # Расчет P&L
        trade = df.loc[trade_index[0]]
        pnl = self._calculate_pnl(trade, exit_price)
        pnl_percent = (pnl / trade['position_size']) * 100
        
        # Обновляем запись
        df.loc[trade_index[0], 'exit_price'] = exit_price
        df.loc[trade_index[0], 'pnl'] = pnl
        df.loc[trade_index[0], 'pnl_percent'] = pnl_percent
        df.loc[trade_index[0], 'status'] = 'CLOSED'
        df.loc[trade_index[0], 'exit_reason'] = exit_reason
        
        df.to_csv(self.journal_file, index=False)
        
        # Обновляем портфолио
        self._update_portfolio_on_close(trade, pnl)
        
        print(f"✅ TRADE CLOSED: {trade_id}")
        print(f"Exit Price: ${exit_price:,.2f}")
        print(f"P&L: ${pnl:,.0f} ({pnl_percent:.1f}%)")
        print(f"Reason: {exit_reason}")
        
        return pnl
    
    def _calculate_pnl(self, trade, exit_price):
        """Расчет P&L на основе стратегии"""
        
        entry_price = trade['entry_price']
        strategy = trade['strategy']
        position_size = trade['position_size']
        
        if strategy == "Long Straddle":
            move_amount = abs(exit_price - entry_price)
            profit = move_amount - trade['premium_paid']
            return max(profit, -trade['premium_paid'])
        
        elif strategy == "Bull Call Spread":
            if exit_price <= trade['long_strike']:
                return -trade['premium_paid']
            elif exit_price >= trade['short_strike']:
                return (trade['short_strike'] - trade['long_strike']) - trade['premium_paid']
            else:
                return (exit_price - trade['long_strike']) - trade['premium_paid']
        
        elif strategy == "Bear Put Spread":
            if exit_price >= trade['long_strike']:
                return -trade['premium_paid']
            elif exit_price <= trade['short_strike']:
                return (trade['long_strike'] - trade['short_strike']) - trade['premium_paid']
            else:
                return (trade['long_strike'] - exit_price) - trade['premium_paid']
        
        elif strategy == "Iron Condor":
            move_percent = abs(exit_price - entry_price) / entry_price
            if move_percent < 0.08:
                return trade['premium_received']
            else:
                return -position_size * 0.2  # Max loss
        
        else:
            # Простая логика для других стратегий
            return (exit_price - entry_price) * (position_size / entry_price)
    
    def _update_portfolio_on_open(self, trade):
        """Обновление портфолио при открытии сделки"""
        with open(self.portfolio_file) as f:
            portfolio = json.load(f)
        
        # Резервируем средства
        cost = trade['premium_paid'] - trade['premium_received']
        portfolio['cash'] -= cost
        
        # Добавляем в открытые позиции
        portfolio['open_positions'].append({
            'trade_id': trade['trade_id'],
            'strategy': trade['strategy'],
            'asset': trade['asset'],
            'cost': cost,
            'timestamp': trade['timestamp']
        })
        
        with open(self.portfolio_file, 'w') as f:
            json.dump(portfolio, f, indent=2)
    
    def _update_portfolio_on_close(self, trade, pnl):
        """Обновление портфолио при закрытии сделки"""
        with open(self.portfolio_file) as f:
            portfolio = json.load(f)
        
        # Возвращаем средства + P&L
        portfolio['cash'] += trade['position_size'] + pnl
        portfolio['total_pnl'] += pnl
        portfolio['total_trades'] += 1
        
        if pnl > 0:
            portfolio['winning_trades'] += 1
        
        # Убираем из открытых позиций
        portfolio['open_positions'] = [
            pos for pos in portfolio['open_positions'] 
            if pos['trade_id'] != trade['trade_id']
        ]
        
        portfolio['total_value'] = portfolio['cash'] + sum(
            pos['cost'] for pos in portfolio['open_positions']
        )
        
        with open(self.portfolio_file, 'w') as f:
            json.dump(portfolio, f, indent=2)
    
    def show_portfolio_status(self):
        """Показать статус портфолио"""
        with open(self.portfolio_file) as f:
            portfolio = json.load(f)
        
        df = pd.read_csv(self.journal_file)
        
        print(f"\n=== PORTFOLIO STATUS ===")
        print(f"Cash: ${portfolio['cash']:,.0f}")
        print(f"Total Value: ${portfolio['total_value']:,.0f}")
        print(f"Total P&L: ${portfolio['total_pnl']:,.0f}")
        print(f"ROI: {(portfolio['total_pnl'] / self.initial_capital) * 100:.1f}%")
        
        if portfolio['total_trades'] > 0:
            win_rate = (portfolio['winning_trades'] / portfolio['total_trades']) * 100
            print(f"Win Rate: {win_rate:.1f}% ({portfolio['winning_trades']}/{portfolio['total_trades']})")
        
        print(f"Open Positions: {len(portfolio['open_positions'])}")
        
        if len(portfolio['open_positions']) > 0:
            print(f"\nOPEN TRADES:")
            for pos in portfolio['open_positions']:
                print(f"  {pos['trade_id']}: {pos['strategy']} ({pos['asset']})")
    
    def show_trade_history(self, last_n=10):
        """Показать историю сделок"""
        df = pd.read_csv(self.journal_file)
        
        if len(df) == 0:
            print("No trades yet")
            return
        
        recent_trades = df.tail(last_n)
        
        print(f"\n=== LAST {min(last_n, len(df))} TRADES ===")
        for _, trade in recent_trades.iterrows():
            status_icon = "✅" if trade['status'] == 'CLOSED' else "🔄"
            pnl_text = f"${trade['pnl']:,.0f}" if pd.notna(trade['pnl']) else "Open"
            
            print(f"{status_icon} {trade['trade_id']}")
            print(f"  {trade['strategy']} | {trade['asset']} | {pnl_text}")

def main():
    journal = PaperTradingJournal()
    
    print("=== PAPER TRADING JOURNAL INITIALIZED ===")
    journal.show_portfolio_status()
    journal.show_trade_history(5)

if __name__ == "__main__":
    main()
