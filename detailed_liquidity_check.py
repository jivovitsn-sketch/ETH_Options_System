#!/usr/bin/env python3
import requests
import re

def detailed_check():
    base_url = "https://api.bybit.com"
    
    print("=== ДЕТАЛЬНАЯ ПРОВЕРКА ЛИКВИДНОСТИ ===")
    
    # Получаем конкретный символ из предыдущего анализа
    test_symbol = "BTC-14NOV25-112000-C-USDT"  # ATM call из результатов
    
    print(f"Тестируем конкретный символ: {test_symbol}")
    
    # Проверяем разные способы получения цен
    
    # Способ 1: Все тикеры опционов
    print(f"\n1. Все тикеры опционов:")
    response1 = requests.get(f"{base_url}/v5/market/tickers", 
                            params={'category': 'option'})
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"Статус: {response1.status_code}")
        print(f"retCode: {data1.get('retCode')}")
        print(f"Всего тикеров: {len(data1['result']['list'])}")
        
        # Ищем наш символ
        found = False
        for ticker in data1['result']['list']:
            if ticker['symbol'] == test_symbol:
                found = True
                print(f"НАЙДЕН: {test_symbol}")
                print(f"  bid1Price: {ticker.get('bid1Price')}")
                print(f"  ask1Price: {ticker.get('ask1Price')}")
                print(f"  lastPrice: {ticker.get('lastPrice')}")
                print(f"  volume24h: {ticker.get('volume24h')}")
                break
        
        if not found:
            print(f"НЕ НАЙДЕН: {test_symbol}")
            print("Доступные символы (первые 5):")
            for ticker in data1['result']['list'][:5]:
                print(f"  {ticker['symbol']}")
    
    # Способ 2: Конкретный символ
    print(f"\n2. Конкретный символ:")
    response2 = requests.get(f"{base_url}/v5/market/tickers",
                            params={'category': 'option', 'symbol': test_symbol})
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"Статус: {response2.status_code}")
        print(f"retCode: {data2.get('retCode')}")
        if data2.get('result') and data2['result'].get('list'):
            ticker = data2['result']['list'][0]
            print(f"Данные: {ticker}")
    
    # Способ 3: Orderbook
    print(f"\n3. Стакан заявок:")
    response3 = requests.get(f"{base_url}/v5/market/orderbook",
                            params={'category': 'option', 'symbol': test_symbol})
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"Статус: {response3.status_code}")
        print(f"retCode: {data3.get('retCode')}")
        
        if data3.get('result'):
            result = data3['result']
            bids = result.get('b', [])
            asks = result.get('a', [])
            
            print(f"Bids: {len(bids)} уровней")
            print(f"Asks: {len(asks)} уровней")
            
            if bids:
                print(f"Лучший bid: {bids[0]}")
            if asks:
                print(f"Лучший ask: {asks[0]}")
    else:
        print(f"Ошибка orderbook: {response3.status_code}")
    
    # Способ 4: Проверяем реальные торгуемые символы
    print(f"\n4. Поиск реально торгуемых символов:")
    response4 = requests.get(f"{base_url}/v5/market/tickers",
                            params={'category': 'option'})
    
    if response4.status_code == 200:
        data4 = response4.json()
        
        active_symbols = []
        for ticker in data4['result']['list']:
            bid = ticker.get('bid1Price')
            ask = ticker.get('ask1Price')
            volume = ticker.get('volume24h')
            
            if bid and ask and float(bid) > 0 and float(ask) > 0:
                active_symbols.append({
                    'symbol': ticker['symbol'],
                    'bid': float(bid),
                    'ask': float(ask), 
                    'volume': float(volume) if volume else 0
                })
        
        print(f"Активных символов с bid/ask: {len(active_symbols)}")
        
        if active_symbols:
            print("Топ-5 по объему:")
            sorted_by_volume = sorted(active_symbols, key=lambda x: x['volume'], reverse=True)
            for i, symbol in enumerate(sorted_by_volume[:5]):
                print(f"  {i+1}. {symbol['symbol']}")
                print(f"     Bid/Ask: {symbol['bid']}/{symbol['ask']}")
                print(f"     Volume: {symbol['volume']}")

if __name__ == "__main__":
    detailed_check()
