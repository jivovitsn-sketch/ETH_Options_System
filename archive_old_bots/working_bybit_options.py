#!/usr/bin/env python3
import requests
import re
import time

def get_real_option_data(symbol):
    """Получаем данные конкретного опциона"""
    base_url = "https://api.bybit.com"
    
    try:
        response = requests.get(f"{base_url}/v5/market/tickers",
                               params={'category': 'option', 'symbol': symbol})
        
        if response.status_code == 200:
            data = response.json()
            if data['retCode'] == 0 and data['result']['list']:
                return data['result']['list'][0]
    except:
        pass
    
    return None

def analyze_atm_spreads():
    """Анализ реальных ATM спредов"""
    
    # BTC спот
    base_url = "https://api.bybit.com"
    spot_response = requests.get(f"{base_url}/v5/market/tickers", 
                                params={'category': 'spot', 'symbol': 'BTCUSDT'})
    btc_price = float(spot_response.json()['result']['list'][0]['lastPrice'])
    
    print(f"=== РЕАЛЬНЫЕ BYBIT ОПЦИОНЫ ===")
    print(f"BTC Spot: ${btc_price:,.0f}")
    
    # ATM страйки около текущей цены
    atm_strikes = [110000, 111000, 112000, 113000, 114000, 115000]
    exp = "14NOV25"
    
    # Проверяем конкретные символы
    spreads = []
    
    for strike in atm_strikes:
        call_symbol = f"BTC-{exp}-{strike}-C-USDT"
        put_symbol = f"BTC-{exp}-{strike}-P-USDT"
        
        print(f"\nСтрайк ${strike:,}:")
        
        # Call опцион
        call_data = get_real_option_data(call_symbol)
        if call_data:
            call_bid = float(call_data['bid1Price'])
            call_ask = float(call_data['ask1Price'])
            call_spread = call_ask - call_bid
            call_mid = (call_bid + call_ask) / 2
            
            print(f"  Call: ${call_bid:,.0f} / ${call_ask:,.0f} (спред ${call_spread:,.0f})")
            print(f"        Volume: {call_data['volume24h']}, OI: {call_data['openInterest']}")
        
        # Put опцион  
        put_data = get_real_option_data(put_symbol)
        if put_data:
            put_bid = float(put_data['bid1Price'])
            put_ask = float(put_data['ask1Price'])
            put_spread = put_ask - put_bid
            put_mid = (put_bid + put_ask) / 2
            
            print(f"  Put:  ${put_bid:,.0f} / ${put_ask:,.0f} (спред ${put_spread:,.0f})")
            print(f"        Volume: {put_data['volume24h']}, OI: {put_data['openInterest']}")
        
        # Bull Call Spread возможности
        if call_data and strike < 114000:  # Есть следующий страйк
            next_strike = strike + 1000
            next_call_symbol = f"BTC-{exp}-{next_strike}-C-USDT"
            next_call_data = get_real_option_data(next_call_symbol)
            
            if next_call_data:
                long_cost = call_ask  # Покупаем по ask
                short_credit = float(next_call_data['bid1Price'])  # Продаем по bid
                spread_cost = long_cost - short_credit
                max_profit = 1000 - spread_cost  # Ширина минус стоимость
                
                spreads.append({
                    'long_strike': strike,
                    'short_strike': next_strike,
                    'cost': spread_cost,
                    'max_profit': max_profit,
                    'breakeven': strike + spread_cost
                })
        
        time.sleep(0.1)  # Не спамим API
    
    # Анализ спредов
    if spreads:
        print(f"\n=== РЕАЛЬНЫЕ BULL CALL SPREADS ===")
        for spread in spreads:
            roi = (spread['max_profit'] / spread['cost']) * 100 if spread['cost'] > 0 else 0
            print(f"${spread['long_strike']:,} / ${spread['short_strike']:,}:")
            print(f"  Стоимость: ${spread['cost']:,.0f}")
            print(f"  Макс прибыль: ${spread['max_profit']:,.0f}")
            print(f"  ROI: {roi:.1f}%")
            print(f"  Breakeven: ${spread['breakeven']:,.0f}")

if __name__ == "__main__":
    analyze_atm_spreads()
