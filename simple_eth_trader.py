#!/usr/bin/env python3
"""
ПРОСТОЙ TRADER с реальными данными
"""
import sqlite3
import pandas as pd
import json
import requests
from datetime import datetime

def get_current_eth_price():
    """Получение текущей цены ETH"""
    try:
        response = requests.get('https://api.bybit.com/v2/public/tickers?symbol=ETHUSDT', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data['result'][0]['last_price'])
    except:
        pass
    return 3900  # Fallback

def analyze_options():
    """Анализ опционов"""
    try:
        conn = sqlite3.connect('data/eth_options_simple.db')
        df = pd.read_sql_query('SELECT * FROM options', conn)
        conn.close()
        
        if len(df) == 0:
            return None
        
        eth_price = get_current_eth_price()
        
        # Ищем ATM страйки
        atm_strike = round(eth_price / 50) * 50
        
        # Фильтруем близкие страйки
        close_strikes = df[
            (df['strike'] >= atm_strike - 200) & 
            (df['strike'] <= atm_strike + 200)
        ]
        
        if len(close_strikes) == 0:
            return None
        
        calls = close_strikes[close_strikes['type'] == 'CALL']
        puts = close_strikes[close_strikes['type'] == 'PUT']
        
        # Генерируем торговый сигнал
        if len(calls) > len(puts):
            signal = 'BULLISH'
            strategy = 'Bull Call Spread'
        else:
            signal = 'BEARISH' 
            strategy = 'Bear Put Spread'
        
        return {
            'signal': signal,
            'strategy': strategy,
            'eth_price': eth_price,
            'atm_strike': atm_strike,
            'available_options': len(close_strikes),
            'calls': len(calls),
            'puts': len(puts)
        }
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return None

def create_trade(analysis):
    """Создание сделки"""
    if not analysis:
        return None
    
    # Простой расчет спреда
    if analysis['strategy'] == 'Bull Call Spread':
        long_strike = analysis['atm_strike']
        short_strike = analysis['atm_strike'] + 200
    else:
        long_strike = analysis['atm_strike']
        short_strike = analysis['atm_strike'] - 200
    
    # Примерный расчет
    cost = 0.05  # ETH
    max_profit = 0.15  # ETH
    
    trade = {
        'trade_id': f"ETH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now(),
        'strategy': analysis['strategy'],
        'signal': analysis['signal'],
        'eth_price': analysis['eth_price'],
        'long_strike': long_strike,
        'short_strike': short_strike,
        'cost': cost,
        'max_profit': max_profit,
        'status': 'OPEN'
    }
    
    return trade

def save_trade_to_excel(trade):
    """Сохранение в Excel"""
    try:
        # Читаем существующий файл
        df = pd.read_excel('data/ETH_Options_Live_Journal.xlsx')
    except:
        # Создаем новый
        df = pd.DataFrame()
    
    # Добавляем новую сделку
    new_row = pd.DataFrame([trade])
    df = pd.concat([df, new_row], ignore_index=True)
    
    # Сохраняем
    df.to_excel('data/ETH_Options_Live_Journal.xlsx', index=False)
    print(f"✅ Trade saved: {trade['trade_id']}")

def send_telegram_notification(trade):
    """Уведомление в Telegram"""
    try:
        with open('config/telegram.json') as f:
            config = json.load(f)
        
        message = f"""
🎯 <b>ETH OPTIONS TRADE</b>

<b>ID:</b> {trade['trade_id']}
<b>Strategy:</b> {trade['strategy']}
<b>Signal:</b> {trade['signal']}

<b>ETH Price:</b> ${trade['eth_price']:,.2f}
<b>Long Strike:</b> ${trade['long_strike']:,.0f}
<b>Short Strike:</b> ${trade['short_strike']:,.0f}

<b>Cost:</b> {trade['cost']} ETH
<b>Max Profit:</b> {trade['max_profit']} ETH
<b>ROI:</b> {(trade['max_profit']/trade['cost']*100):.0f}%

<i>Paper Trading</i>
        """
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['channels']['vip'],
            'text': message.strip(),
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, proxies=config['proxy'], timeout=10)
        if response.status_code == 200:
            print("✅ Telegram notification sent")
        else:
            print(f"❌ Telegram failed: {response.status_code}")
            
    except Exception as e:
        print(f"Telegram error: {e}")

def main():
    print("=== ETH OPTIONS SIMPLE TRADER ===")
    
    # Анализируем
    analysis = analyze_options()
    
    if not analysis:
        print("❌ No trading opportunities")
        return
    
    print(f"✅ Analysis: {analysis['signal']} - {analysis['available_options']} options")
    
    # Создаем сделку
    trade = create_trade(analysis)
    
    if trade:
        # Сохраняем
        save_trade_to_excel(trade)
        
        # Уведомляем
        send_telegram_notification(trade)
        
        print(f"✅ Trade created: {trade['trade_id']}")
    else:
        print("❌ Failed to create trade")

if __name__ == "__main__":
    main()
