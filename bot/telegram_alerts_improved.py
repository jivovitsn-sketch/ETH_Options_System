#!/usr/bin/env python3
"""
УЛУЧШЕННЫЙ TELEGRAM ALERTS с полными данными опционов
"""
import requests
import json
from datetime import datetime
from pathlib import Path
from options_calculator import OptionsCalculator

class TelegramAlertsImproved:
    def __init__(self):
        config_file = Path(__file__).parent.parent / 'config' / 'telegram.json'
        
        with open(config_file) as f:
            config = json.load(f)
        
        self.token = config['bot_token']
        self.channels = config['channels']
        self.proxies = config['proxy']
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
        self.options_calc = OptionsCalculator()
        
        print("Telegram Alerts Improved initialized")
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Отправка сообщения"""
        url = f"{self.api_url}/sendMessage"
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        
        try:
            response = requests.post(url, json=data, proxies=self.proxies, timeout=15)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def vip_trade_opened_full(self, trade_data):
        """VIP канал - ПОЛНАЯ информация об опционной сделке"""
        
        # Получаем полный расчет опциона
        spot_price = trade_data['entry']
        signal_type = trade_data['signal']
        dte = trade_data.get('dte', 60)
        
        option_details = self.options_calc.calculate_option_details(spot_price, signal_type, dte)
        
        strategy_name = "Bull Call Spread" if signal_type == "BUY" else "Bear Put Spread"
        
        message = f"""
📊 <b>VIP TRADE OPENED</b>

<b>Asset:</b> {trade_data['asset']}
<b>Strategy:</b> {strategy_name} {dte}DTE
<b>Spot Price:</b> ${spot_price:,.2f}

<b>🎯 STRIKES:</b>
Long: ${option_details['long_strike']:,.0f}
Short: ${option_details['short_strike']:,.0f}

<b>📅 EXPIRATION:</b>
{option_details['expiry_date'].strftime('%Y-%m-%d')} ({dte} days)

<b>💰 FINANCIALS:</b>
Net Debit: ${option_details['net_debit']:.2f}
Max Profit: ${option_details['max_profit']:.2f}
Max Loss: ${option_details['max_loss']:.2f}
ROI Potential: {option_details['roi_potential']:.1f}%

<b>⚖️ BREAKEVEN:</b> ${option_details['breakeven']:.2f}

<b>🎯 TAKE PROFITS:</b>
TP1: ${option_details['tp1_price']:.2f} (+${option_details['tp1_profit']:.2f})
TP2: ${option_details['tp2_price']:.2f} (+${option_details['tp2_profit']:.2f})  
TP3: ${option_details['tp3_price']:.2f} (+${option_details['tp3_profit']:.2f})

<b>📊 GREEKS:</b>
Delta: {trade_data.get('delta', 0.071):.4f}
Theta: {trade_data.get('theta', -0.05):.3f}/day

<i>Paper Trading Mode</i>
        """
        
        return self.send_message(self.channels['vip'], message.strip())
    
    def free_signal_improved(self, asset, signal, price):
        """FREE канал - улучшенный формат"""
        message = f"""
🔥 <b>{signal} SIGNAL</b>

<b>Asset:</b> {asset}
<b>Price:</b> ${price:,.2f}
<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

<i>Check VIP for details</i>
        """
        
        return self.send_message(self.channels['free'], message.strip())

if __name__ == "__main__":
    # Тест улучшенного формата
    telegram = TelegramAlertsImproved()
    
    test_trade = {
        'asset': 'ETHUSDT',
        'signal': 'BUY',
        'entry': 3939,
        'dte': 60,
        'delta': 0.071,
        'theta': -0.05
    }
    
    print("Отправляю улучшенные форматы...")
    telegram.free_signal_improved('ETHUSDT', 'BUY', 3939)
    telegram.vip_trade_opened_full(test_trade)
