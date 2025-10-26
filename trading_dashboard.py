#!/usr/bin/env python3
import pandas as pd
import json
from datetime import datetime

def create_dashboard():
    try:
        df = pd.read_csv('data/paper_trades.csv')
        with open('data/portfolio_status.json') as f:
            portfolio = json.load(f)
    except:
        print("No trading data found. Start trading first!")
        return
    
    print("=" * 60)
    print("         PAPER TRADING DASHBOARD")
    print("=" * 60)
    
    # Основная статистика
    print(f"💰 Portfolio Value: ${portfolio['total_value']:,.0f}")
    print(f"💵 Available Cash: ${portfolio['cash']:,.0f}")
    print(f"📈 Total P&L: ${portfolio['total_pnl']:,.0f}")
    
    roi = (portfolio['total_pnl'] / 50000) * 100
    print(f"📊 ROI: {roi:.1f}%")
    
    if portfolio['total_trades'] > 0:
        win_rate = (portfolio['winning_trades'] / portfolio['total_trades']) * 100
        print(f"🎯 Win Rate: {win_rate:.1f}%")
    
    print(f"🔄 Open Positions: {len(portfolio['open_positions'])}")
    
    # Статистика по стратегиям
    if len(df) > 0:
        closed_trades = df[df['status'] == 'CLOSED']
        if len(closed_trades) > 0:
            print(f"\n📋 STRATEGY PERFORMANCE:")
            strategy_stats = closed_trades.groupby('strategy').agg({
                'pnl': ['count', 'sum', 'mean'],
                'pnl_percent': 'mean'
            }).round(1)
            
            for strategy, stats in strategy_stats.iterrows():
                count = stats[('pnl', 'count')]
                total_pnl = stats[('pnl', 'sum')]
                avg_pnl = stats[('pnl', 'mean')]
                avg_percent = stats[('pnl_percent', 'mean')]
                
                print(f"  {strategy}: {count} trades, ${total_pnl:,.0f} total, {avg_percent:.1f}% avg")
    
    # Открытые позиции
    if len(portfolio['open_positions']) > 0:
        print(f"\n🔄 OPEN POSITIONS:")
        for pos in portfolio['open_positions']:
            print(f"  {pos['trade_id']}: {pos['strategy']} ({pos['asset']})")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    create_dashboard()
