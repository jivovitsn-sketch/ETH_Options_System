#!/usr/bin/env python3
"""
ORDER BLOCKS (OB)
Зоны институциональных ордеров
"""

import pandas as pd
import numpy as np

class OrderBlocks:
    """
    Order Blocks - зоны где Smart Money размещает ордера
    """
    
    def __init__(self, swing_length: int = 5):
        self.swing_length = swing_length
        print(f"✅ Order Blocks initialized (swing_length={swing_length})")
    
    def find_swing_highs_lows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Найти swing highs и lows
        """
        df = df.copy()
        
        df['swing_high'] = False
        df['swing_low'] = False
        
        for i in range(self.swing_length, len(df) - self.swing_length):
            # Swing High
            is_high = True
            for j in range(1, self.swing_length + 1):
                if df.iloc[i]['high'] <= df.iloc[i-j]['high'] or \
                   df.iloc[i]['high'] <= df.iloc[i+j]['high']:
                    is_high = False
                    break
            
            if is_high:
                df.at[df.index[i], 'swing_high'] = True
            
            # Swing Low
            is_low = True
            for j in range(1, self.swing_length + 1):
                if df.iloc[i]['low'] >= df.iloc[i-j]['low'] or \
                   df.iloc[i]['low'] >= df.iloc[i+j]['low']:
                    is_low = False
                    break
            
            if is_low:
                df.at[df.index[i], 'swing_low'] = True
        
        return df
    
    def find_order_blocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Найти Order Blocks
        
        Bullish OB: последняя down-свеча перед swing low
        Bearish OB: последняя up-свеча перед swing high
        """
        df = self.find_swing_highs_lows(df)
        
        df['bullish_ob'] = False
        df['bearish_ob'] = False
        df['ob_top'] = np.nan
        df['ob_bottom'] = np.nan
        
        for i in range(1, len(df)):
            # Bullish Order Block
            if df.iloc[i]['swing_low']:
                # Найти последнюю down-свечу
                for j in range(i-1, max(0, i-10), -1):
                    if df.iloc[j]['close'] < df.iloc[j]['open']:
                        df.at[df.index[j], 'bullish_ob'] = True
                        df.at[df.index[j], 'ob_bottom'] = df.iloc[j]['low']
                        df.at[df.index[j], 'ob_top'] = df.iloc[j]['high']
                        break
            
            # Bearish Order Block
            if df.iloc[i]['swing_high']:
                # Найти последнюю up-свечу
                for j in range(i-1, max(0, i-10), -1):
                    if df.iloc[j]['close'] > df.iloc[j]['open']:
                        df.at[df.index[j], 'bearish_ob'] = True
                        df.at[df.index[j], 'ob_top'] = df.iloc[j]['high']
                        df.at[df.index[j], 'ob_bottom'] = df.iloc[j]['low']
                        break
        
        return df
    
    def get_active_obs(self, df: pd.DataFrame, lookback: int = 50) -> dict:
        """
        Получить активные Order Blocks
        """
        df_with_ob = self.find_order_blocks(df)
        current_price = df['close'].iloc[-1]
        
        # Только последние N свечей
        recent = df_with_ob.tail(lookback)
        
        bullish_obs = []
        bearish_obs = []
        
        for idx, row in recent.iterrows():
            if row['bullish_ob'] and pd.notna(row['ob_bottom']):
                # Активен если цена выше зоны
                if current_price > row['ob_top']:
                    bullish_obs.append({
                        'bottom': row['ob_bottom'],
                        'top': row['ob_top'],
                        'distance': current_price - row['ob_top']
                    })
            
            if row['bearish_ob'] and pd.notna(row['ob_bottom']):
                # Активен если цена ниже зоны
                if current_price < row['ob_bottom']:
                    bearish_obs.append({
                        'top': row['ob_top'],
                        'bottom': row['ob_bottom'],
                        'distance': row['ob_bottom'] - current_price
                    })
        
        return {
            'bullish': bullish_obs,
            'bearish': bearish_obs
        }

if __name__ == "__main__":
    print("Order Blocks module ready")
