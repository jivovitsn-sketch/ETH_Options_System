#!/usr/bin/env python3
import requests
import json

def check_specific_options():
    base_url = "https://api.bybit.com"
    
    # Сначала получаем текущую цену BTC
    spot_response = requests.get(f"{base_url}/v5/market/tickers", 
                                params={'category': 'spot', 'symbol': 'BTCUSDT'})
    
    if spot_response.status_code == 200:
        spot_data = spot_response.json()
        btc_price = float(spot_data['result']['list'][0]['lastPrice'])
        print(f"BTC Spot: ${btc_price:,.0f}")
    
    # Получаем все опционы
    options_response = requests.get(f"{base_url}/v5/market/instruments-info",
                                   params={'category': 'option', 'baseCoin': 'BTC'})
    
    if options_response.status_code == 200:
        data = options_response.json()
        options = data['result']['list']
        
        # Фильтруем по ближайшей экспирации и ATM страйкам
        nearest_exp = min([opt['deliveryTime'] for opt in options])
        
        atm_options = []
        for opt in options:
            if opt['deliveryTime'] == nearest_exp:
                strike = float(opt['strikePrice'])
                if abs(strike - btc_price) / btc_price < 0.05:  # В пределах 5%
                    atm_options.append(opt)
        
        print(f"\nATM опционы экспирация {nearest_exp}:")
        for opt in atm_options[:10]:
            print(f"  {opt['symbol']}: Strike ${opt['strikePrice']} {opt['optionsType']}")
        
        # Проверяем цены этих опционов
        symbols = [opt['symbol'] for opt in atm_options[:5]]
        if symbols:
            prices_response = requests.get(f"{base_url}/v5/market/tickers",
                                         params={'category': 'option'})
            
            if prices_response.status_code == 200:
                price_data = prices_response.json()
                
                print(f"\nЦены ATM опционов:")
                found_prices = False
                for ticker in price_data['result']['list']:
                    if ticker['symbol'] in symbols:
                        found_prices = True
                        bid = ticker['bid1Price']
                        ask = ticker['ask1Price']
                        volume = ticker['volume24h']
                        
                        print(f"  {ticker['symbol']}:")
                        print(f"    Bid: {bid} | Ask: {ask}")
                        print(f"    Volume 24h: {volume}")
                
                if not found_prices:
                    print("  Нет активных цен для ATM опционов")
                    print("  Возможно рынок неликвиден")

if __name__ == "__main__":
    check_specific_options()
