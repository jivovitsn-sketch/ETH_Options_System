#!/usr/bin/env python3
from paper_trading_journal import PaperTradingJournal
import requests

def get_real_bybit_spread_cost(long_strike, short_strike, exp="14NOV25"):
    """Получаем реальную стоимость спреда с Bybit"""
    base_url = "https://api.bybit.com"
    
    # Реальные символы
    long_symbol = f"BTC-{exp}-{long_strike}-C-USDT"
    short_symbol = f"BTC-{exp}-{short_strike}-C-USDT"
    
    try:
        # Long call (покупаем по ask)
        long_response = requests.get(f"{base_url}/v5/market/tickers",
                                   params={'category': 'option', 'symbol': long_symbol})
        long_data = long_response.json()['result']['list'][0]
        long_cost = float(long_data['ask1Price'])
        
        # Short call (продаем по bid)
        short_response = requests.get(f"{base_url}/v5/market/tickers", 
                                    params={'category': 'option', 'symbol': short_symbol})
        short_data = short_response.json()['result']['list'][0]
        short_credit = float(short_data['bid1Price'])
        
        spread_cost = long_cost - short_credit
        max_profit = (short_strike - long_strike) - spread_cost
        
        return {
            'cost': spread_cost,
            'max_profit': max_profit,
            'long_ask': long_cost,
            'short_bid': short_credit
        }
        
    except Exception as e:
        print(f"Error getting spread cost: {e}")
        return None

# Тестируем открытие реального спреда
journal = PaperTradingJournal()

print("=== РЕАЛЬНЫЙ BYBIT SPREAD ДЛЯ PAPER TRADING ===")

spread_data = get_real_bybit_spread_cost(111000, 112000)

if spread_data:
    print(f"Bull Call Spread 111k/112k:")
    print(f"  Стоимость: ${spread_data['cost']:,.0f}")
    print(f"  Макс прибыль: ${spread_data['max_profit']:,.0f}")
    print(f"  ROI: {(spread_data['max_profit']/spread_data['cost'])*100:.1f}%")
    
    # Открываем в paper trading
    position_size = spread_data['cost']
    
    trade_id = journal.open_trade(
        strategy="Bull Call Spread (Real Bybit)",
        asset="BTC", 
        entry_price=112451,  # Текущий спот
        position_size=position_size,
        long_strike=111000,
        short_strike=112000,
        notes=f"Real Bybit spread: ${spread_data['long_ask']:.0f}/{spread_data['short_bid']:.0f}"
    )
    
    print(f"\nPaper trade opened: {trade_id}")
