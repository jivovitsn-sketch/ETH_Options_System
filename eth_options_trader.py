#!/usr/bin/env python3
"""
РЕАЛЬНЫЙ ETH OPTIONS TRADER - принимает решения и ведет журнал
"""
import sqlite3
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill

class ETHOptionsTrader:
    def __init__(self):
        self.db_file = "data/eth_options.db"
        self.journal_file = "data/ETH_Options_Live_Journal.xlsx"
        self.log_file = "logs/eth_trader.log"
        self.capital = 10000  # Starting capital
        self.position_size = 500  # Per trade
        
        # Telegram
        with open('config/telegram.json') as f:
            config = json.load(f)
        self.token = config['bot_token']
        self.channels = config['channels']
        self.proxies = config['proxy']
        
        # Initialize journal
        self.init_journal()
        self.log("ETH Options Trader initialized")
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(self.log_file, 'a') as f:
            f.write(log_line + '\n')
    
    def init_journal(self):
        """Создание Excel журнала сделок"""
        try:
            # Читаем существующий файл
            df = pd.read_excel(self.journal_file)
        except:
            # Создаем новый
            columns = [
                'Trade_ID', 'Timestamp', 'Signal', 'Strategy', 'ETH_Price',
                'Long_Strike', 'Short_Strike', 'Expiry', 'DTE',
                'Entry_Cost', 'Max_Profit', 'Breakeven',
                'Delta', 'Theta', 'IV', 'Status',
                'Exit_Price', 'Exit_Time', 'Actual_PnL', 'ROI_Percent'
            ]
            df = pd.DataFrame(columns=columns)
            df.to_excel(self.journal_file, index=False)
        
        self.log(f"Journal initialized: {self.journal_file}")
    
    def get_latest_options_data(self):
        """Получение последних данных опционов"""
        conn = sqlite3.connect(self.db_file)
        
        # Последние данные за час
        query = '''
            SELECT * FROM eth_options 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def analyze_trading_opportunity(self, options_df):
        """Анализ торговых возможностей"""
        if len(options_df) == 0:
            return None
        
        current_eth_price = options_df['underlying_price'].iloc[0]
        
        # Фильтруем опционы с хорошей ликвидностью
        liquid_options = options_df[
            (options_df['volume_24h'] > 0.1) & 
            (options_df['open_interest'] > 5)
        ]
        
        if len(liquid_options) == 0:
            return None
        
        # Ищем 30-60 DTE опционы
        today = datetime.now().date()
        liquid_options['dte'] = (pd.to_datetime(liquid_options['expiration_date']).dt.date - today).dt.days
        
        good_dte = liquid_options[
            (liquid_options['dte'] >= 30) & 
            (liquid_options['dte'] <= 60)
        ]
        
        if len(good_dte) == 0:
            return None
        
        # Анализируем Put/Call соотношение
        calls = good_dte[good_dte['option_type'] == 'CALL']
        puts = good_dte[good_dte['option_type'] == 'PUT']
        
        if len(calls) == 0 or len(puts) == 0:
            return None
        
        # Высокая IV = потенциал продажи
        # Низкая IV = потенциал покупки
        avg_iv = good_dte['implied_volatility'].mean()
        
        # Ищем ATM и OTM страйки
        atm_strike = round(current_eth_price / 50) * 50
        
        # Bull Call Spread если тренд вверх
        if self.detect_bullish_signal(current_eth_price, good_dte):
            
            # Long ATM Call
            long_call = calls[calls['strike'] == atm_strike]
            if len(long_call) == 0:
                return None
            
            # Short OTM Call
            short_strike = atm_strike + 200
            short_call = calls[calls['strike'] == short_strike]
            if len(short_call) == 0:
                return None
            
            long_premium = long_call.iloc[0]['mark_price']
            short_premium = short_call.iloc[0]['mark_price']
            net_debit = long_premium - short_premium
            max_profit = (short_strike - atm_strike) - net_debit
            breakeven = atm_strike + net_debit
            
            if net_debit > 0 and max_profit > net_debit * 0.5:  # Минимум 50% потенциальная прибыль
                return {
                    'signal': 'BUY',
                    'strategy': 'Bull Call Spread',
                    'eth_price': current_eth_price,
                    'long_strike': atm_strike,
                    'short_strike': short_strike,
                    'expiry': long_call.iloc[0]['expiration_date'],
                    'dte': long_call.iloc[0]['dte'],
                    'entry_cost': net_debit,
                    'max_profit': max_profit,
                    'breakeven': breakeven,
                    'delta': long_call.iloc[0]['delta'] - short_call.iloc[0]['delta'],
                    'theta': long_call.iloc[0]['theta'] - short_call.iloc[0]['theta'],
                    'iv': avg_iv,
                    'confidence': 'HIGH' if avg_iv < 0.6 else 'MEDIUM'
                }
        
        # Bear Put Spread если тренд вниз
        elif self.detect_bearish_signal(current_eth_price, good_dte):
            
            # Long ATM Put
            long_put = puts[puts['strike'] == atm_strike]
            if len(long_put) == 0:
                return None
            
            # Short OTM Put
            short_strike = atm_strike - 200
            short_put = puts[puts['strike'] == short_strike]
            if len(short_put) == 0:
                return None
            
            long_premium = long_put.iloc[0]['mark_price']
            short_premium = short_put.iloc[0]['mark_price']
            net_debit = long_premium - short_premium
            max_profit = (atm_strike - short_strike) - net_debit
            breakeven = atm_strike - net_debit
            
            if net_debit > 0 and max_profit > net_debit * 0.5:
                return {
                    'signal': 'SELL',
                    'strategy': 'Bear Put Spread',
                    'eth_price': current_eth_price,
                    'long_strike': atm_strike,
                    'short_strike': short_strike,
                    'expiry': long_put.iloc[0]['expiration_date'],
                    'dte': long_put.iloc[0]['dte'],
                    'entry_cost': net_debit,
                    'max_profit': max_profit,
                    'breakeven': breakeven,
                    'delta': long_put.iloc[0]['delta'] - short_put.iloc[0]['delta'],
                    'theta': long_put.iloc[0]['theta'] - short_put.iloc[0]['theta'],
                    'iv': avg_iv,
                    'confidence': 'HIGH' if avg_iv > 0.7 else 'MEDIUM'
                }
        
        return None
    
    def detect_bullish_signal(self, current_price, options_df):
        """Простое определение бычьего сигнала"""
        # Если много активности в call опционах
        calls = options_df[options_df['option_type'] == 'CALL']
        puts = options_df[options_df['option_type'] == 'PUT']
        
        call_volume = calls['volume_24h'].sum()
        put_volume = puts['volume_24h'].sum()
        
        # Call/Put ratio > 1.2 = bullish
        if put_volume > 0:
            cp_ratio = call_volume / put_volume
            return cp_ratio > 1.2
        
        return False
    
    def detect_bearish_signal(self, current_price, options_df):
        """Простое определение медвежьего сигнала"""
        calls = options_df[options_df['option_type'] == 'CALL']
        puts = options_df[options_df['option_type'] == 'PUT']
        
        call_volume = calls['volume_24h'].sum()
        put_volume = puts['volume_24h'].sum()
        
        # Put/Call ratio > 1.2 = bearish
        if call_volume > 0:
            pc_ratio = put_volume / call_volume
            return pc_ratio > 1.2
        
        return False
    
    def execute_trade(self, trade_signal):
        """Выполнение сделки"""
        # Генерируем Trade ID
        trade_id = f"ETH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Добавляем в журнал
        new_trade = {
            'Trade_ID': trade_id,
            'Timestamp': datetime.now(),
            'Signal': trade_signal['signal'],
            'Strategy': trade_signal['strategy'],
            'ETH_Price': trade_signal['eth_price'],
            'Long_Strike': trade_signal['long_strike'],
            'Short_Strike': trade_signal['short_strike'],
            'Expiry': trade_signal['expiry'],
            'DTE': trade_signal['dte'],
            'Entry_Cost': trade_signal['entry_cost'],
            'Max_Profit': trade_signal['max_profit'],
            'Breakeven': trade_signal['breakeven'],
            'Delta': trade_signal['delta'],
            'Theta': trade_signal['theta'],
            'IV': trade_signal['iv'],
            'Status': 'OPEN',
            'Exit_Price': '',
            'Exit_Time': '',
            'Actual_PnL': '',
            'ROI_Percent': ''
        }
        
        # Читаем существующий журнал
        try:
            df = pd.read_excel(self.journal_file)
            df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
        except:
            df = pd.DataFrame([new_trade])
        
        # Сохраняем
        df.to_excel(self.journal_file, index=False)
        
        self.log(f"Trade executed: {trade_id} - {trade_signal['strategy']}")
        
        # Отправляем в Telegram
        self.send_trade_notification(trade_signal, trade_id)
        
        return trade_id
    
    def send_trade_notification(self, trade, trade_id):
        """Отправка уведомления о сделке"""
        message = f"""
🎯 <b>ETH OPTIONS TRADE EXECUTED</b>

<b>Trade ID:</b> {trade_id}
<b>Strategy:</b> {trade['strategy']}
<b>Signal:</b> {trade['signal']}

<b>ETH Price:</b> ${trade['eth_price']:,.2f}
<b>Strikes:</b> Long ${trade['long_strike']:,.0f} | Short ${trade['short_strike']:,.0f}
<b>Expiry:</b> {trade['expiry']} ({trade['dte']} DTE)

<b>Economics:</b>
Cost: ${trade['entry_cost']:.4f} ETH
Max Profit: ${trade['max_profit']:.4f} ETH
Breakeven: ${trade['breakeven']:,.2f}
ROI Potential: {(trade['max_profit']/trade['entry_cost']*100):.1f}%

<b>Greeks:</b>
Delta: {trade['delta']:.4f}
Theta: {trade['theta']:.4f}
IV: {trade['iv']*100:.1f}%

<i>Paper Trading Mode</i>
        """
        
        self.send_telegram(message.strip())
    
    def send_telegram(self, message):
        """Отправка в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': self.channels['vip'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, proxies=self.proxies, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def run_trading_cycle(self):
        """Один цикл торговли"""
        self.log("Starting trading cycle")
        
        # Получаем данные опционов
        options_data = self.get_latest_options_data()
        
        if len(options_data) == 0:
            self.log("No options data available")
            return
        
        # Анализируем возможности
        trade_signal = self.analyze_trading_opportunity(options_data)
        
        if trade_signal:
            # Выполняем сделку
            trade_id = self.execute_trade(trade_signal)
            self.log(f"Trade executed: {trade_id}")
            return trade_id
        else:
            self.log("No trading opportunities found")
            return None

if __name__ == "__main__":
    trader = ETHOptionsTrader()
    result = trader.run_trading_cycle()
    
    if result:
        print(f"Trade executed: {result}")
    else:
        print("No trades executed")
