#!/usr/bin/env python3
import requests
import json

def explore_api_structure():
    base_url = "https://api.bybit.com"
    
    print("=== ИССЛЕДОВАНИЕ СТРУКТУРЫ BYBIT API ===")
    
    # Получаем данные опционов
    response = requests.get(f"{base_url}/v5/market/instruments-info",
                          params={'category': 'option', 'baseCoin': 'BTC'})
    
    if response.status_code == 200:
        data = response.json()
        
        if data['retCode'] == 0:
            options = data['result']['list']
            
            print(f"Найдено опционов: {len(options)}")
            
            if options:
                # Смотрим структуру первого опциона
                first_option = options[0]
                print(f"\nСтруктура первого опциона:")
                for key, value in first_option.items():
                    print(f"  {key}: {value}")
                
                print(f"\nВсе доступные поля:")
                print(list(first_option.keys()))
                
                # Ищем поля связанные со страйками
                strike_fields = [k for k in first_option.keys() if 'strike' in k.lower() or 'price' in k.lower()]
                print(f"\nПоля со страйками/ценами: {strike_fields}")
                
                # Показываем несколько примеров
                print(f"\nПервые 5 опционов:")
                for i, opt in enumerate(options[:5]):
                    symbol = opt.get('symbol', 'N/A')
                    # Пробуем разные возможные поля для страйка
                    strike = opt.get('strikePrice') or opt.get('strike') or opt.get('exercisePrice') or 'N/A'
                    opt_type = opt.get('optionsType') or opt.get('side') or opt.get('type') or 'N/A'
                    exp = opt.get('deliveryTime') or opt.get('expiry') or 'N/A'
                    
                    print(f"  {i+1}. {symbol} | Strike: {strike} | Type: {opt_type}")
            
        else:
            print(f"API Error: {data}")
    else:
        print(f"HTTP Error: {response.status_code}")

if __name__ == "__main__":
    explore_api_structure()
