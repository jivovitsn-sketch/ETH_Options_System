#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

def get_real_eth_options():
    """Получаем реальные опционы ETH с Deribit"""
    try:
        url = "https://www.deribit.com/api/v2/public/get_instruments"
        params = {'currency': 'ETH', 'kind': 'option', 'expired': 'false'}
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            instruments = data['result']
            
            # Парсим и группируем по экспирациям
            expirations = {}
            
            for inst in instruments:
                name = inst['instrument_name']
                # ETH-29NOV24-3200-C
                parts = name.split('-')
                if len(parts) == 4:
                    exp_str = parts[1]
                    strike = float(parts[2])
                    option_type = parts[3]
                    
                    if exp_str not in expirations:
                        expirations[exp_str] = {'calls': [], 'puts': [], 'date': exp_str}
                    
                    if option_type == 'C':
                        expirations[exp_str]['calls'].append(strike)
                    else:
                        expirations[exp_str]['puts'].append(strike)
            
            # Сортируем страйки
            for exp in expirations.values():
                exp['calls'].sort()
                exp['puts'].sort()
            
            return expirations
            
    except Exception as e:
        print(f"Deribit error: {e}")
    
    return {}

def get_eth_price():
    """Получаем текущую цену ETH"""
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=10)
        if response.status_code == 200:
            return float(response.json()['price'])
    except:
        pass
    return None

def find_best_expiration(expirations, min_dte=20, max_dte=60):
    """Находим лучшую экспирацию (20-60 дней)"""
    today = datetime.now()
    
    for exp_str, data in expirations.items():
        try:
            # Парсим дату ETH-29NOV24
            exp_date = datetime.strptime(exp_str, '%d%b%y')
            dte = (exp_date - today).days
            
            if min_dte <= dte <= max_dte:
                return exp_str, dte, data
                
        except:
            continue
    
    return None, None, None

def create_professional_signal(eth_price, expirations):
    """Создаем профессиональный сигнал с реальными данными"""
    
    # Находим подходящую экспирацию
    exp_str, dte, exp_data = find_best_expiration(expirations)
    
    if not exp_str:
        return None
    
    # Определяем тренд
    price_level = round(eth_price / 50) * 50
    
    if eth_price > price_level + 30:
        direction = "BULLISH"
        action = "BUY"
        strategy = "Bull Call Spread"
        option_type = "C"
        
        # Находим реальные страйки
        available_strikes = exp_data['calls']
        long_strike = min(available_strikes, key=lambda x: abs(x - price_level))
        short_strike = min([s for s in available_strikes if s > long_strike + 150], 
                          key=lambda x: abs(x - (long_strike + 200)), default=None)
        
    elif eth_price < price_level - 30:
        direction = "BEARISH"
        action = "SELL"
        strategy = "Bear Put Spread"
        option_type = "P"
        
        # Находим реальные страйки
        available_strikes = exp_data['puts']
        long_strike = min(available_strikes, key=lambda x: abs(x - price_level))
        short_strike = min([s for s in available_strikes if s < long_strike - 150], 
                          key=lambda x: abs(x - (long_strike - 200)), default=None)
    else:
        return None
    
    if not short_strike:
        return None
    
    # Расчет экономики
    spread_width = abs(long_strike - short_strike)
    estimated_cost = spread_width * 0.25  # 25% от ширины спреда
    max_profit = spread_width - estimated_cost
    breakeven = long_strike + estimated_cost if action == "BUY" else long_strike - estimated_cost
    
    return {
        'action': action,
        'direction': direction,
        'strategy': strategy,
        'eth_price': eth_price,
        'long_strike': long_strike,
        'short_strike': short_strike,
        'expiry': exp_str,
        'dte': dte,
        'option_type': option_type,
        'cost': estimated_cost,
        'max_profit': max_profit,
        'breakeven': breakeven,
        'spread_width': spread_width
    }

def send_vip_signal(signal):
    """Отправляем VIP-качества сигнал"""
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        # Профессиональное сообщение
        message = f"""🎯 <b>ETH OPTIONS TRADE ALERT</b>

<b>🔥 SIGNAL: {signal['action']} {signal['strategy']}</b>

<b>📊 MARKET ANALYSIS:</b>
- ETH Spot: <code>${signal['eth_price']:,.2f}</code>
- Trend: <b>{signal['direction']}</b>
- Time to Expiry: <b>{signal['dte']} days</b>

<b>📋 TRADE EXECUTION:</b>
<code>BUY:  ETH-{signal['expiry']}-{signal['long_strike']:.0f}-{signal['option_type']}</code>
<code>SELL: ETH-{signal['expiry']}-{signal['short_strike']:.0f}-{signal['option_type']}</code>

<b>💰 TRADE ECONOMICS:</b>
- Spread Width: <code>${signal['spread_width']:.0f}</code>
- Est. Net Debit: <code>{signal['cost']:.3f} ETH</code>
- Max Profit: <code>{signal['max_profit']:.3f} ETH</code>
- Breakeven: <code>${signal['breakeven']:,.2f}</code>
- ROI Potential: <b>{(signal['max_profit']/signal['cost']*100):.0f}%</b>

<b>⚡ RISK MANAGEMENT:</b>
- Max Loss: Limited to net debit
- Profit Target: 50% of max profit
- Stop Loss: 50% of net debit

<b>📅 EXPIRATION: {signal['expiry']} ({signal['dte']}DTE)</b>

<i>🏆 VIP Exclusive - Real Market Data</i>"""
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        
        if response.status_code == 200:
            print(f"✅ VIP signal sent: {signal['action']} @ ${signal['eth_price']}")
            return True
        else:
            print(f"❌ Telegram failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Send error: {e}")
    
    return False

def main():
    print(f"=== Real ETH Options System: {datetime.now().strftime('%H:%M')} ===")
    
    # Получаем реальные опционы
    print("Fetching real options data...")
    expirations = get_real_eth_options()
    
    if not expirations:
        print("❌ Failed to get options data")
        return
    
    print(f"✅ Found {len(expirations)} expirations")
    
    # Получаем цену ETH
    eth_price = get_eth_price()
    if not eth_price:
        print("❌ Failed to get ETH price")
        return
    
    print(f"ETH Price: ${eth_price:,.2f}")
    
    # Создаем профессиональный сигнал
    signal = create_professional_signal(eth_price, expirations)
    
    if signal:
        print(f"Signal: {signal['action']} {signal['strategy']}")
        print(f"Strikes: {signal['long_strike']}/{signal['short_strike']}")
        print(f"Expiry: {signal['expiry']} ({signal['dte']}DTE)")
        send_vip_signal(signal)
    else:
        print("No clear signal with current market conditions")

if __name__ == "__main__":
    main()
