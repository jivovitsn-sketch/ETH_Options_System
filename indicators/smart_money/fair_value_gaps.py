#!/usr/bin/env python3
"""
FAIR VALUE GAPS (FVG)
Зоны дисбаланса (imbalance) в структуре рынка
"""

import pandas as pd
import numpy as np

class FairValueGaps:
    """
    Определение FVG - зон где цена двигалась слишком быстро
    """
    
    def __init__(self):
        print("✅ Fair Value Gaps initialized")
    
    def find_fvg(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Найти FVG зоны
        
        Bullish FVG: Candle 1 high < Candle 3 low (gap вверх)
        Bearish FVG: Candle 1 low > Candle 3 high (gap вниз)
        """
        df = df.copy()
        
        df['fvg_bullish'] = False
        df['fvg_bearish'] = False
        df['fvg_zone_top'] = np.nan
        df['fvg_zone_bottom'] = np.nan
        
        for i in range(2, len(df)):
            # Bullish FVG
            if df.iloc[i-2]['high'] < df.iloc[i]['low']:
                df.at[df.index[i], 'fvg_bullish'] = True
                df.at[df.index[i], 'fvg_zone_bottom'] = df.iloc[i-2]['high']
                df.at[df.index[i], 'fvg_zone_top'] = df.iloc[i]['low']
            
            # Bearish FVG
            if df.iloc[i-2]['low'] > df.iloc[i]['high']:
                df.at[df.index[i], 'fvg_bearish'] = True
                df.at[df.index[i], 'fvg_zone_top'] = df.iloc[i-2]['low']
                df.at[df.index[i], 'fvg_zone_bottom'] = df.iloc[i]['high']
        
        return df
    
    def get_active_fvgs(self, df: pd.DataFrame, current_price: float) -> dict:
        """
        Получить активные (не заполненные) FVG зоны
        """
        df_with_fvg = self.find_fvg(df)
        
        bullish_fvgs = []
        bearish_fvgs = []
        
        for idx, row in df_with_fvg.iterrows():
            if row['fvg_bullish']:
                # FVG активен если цена не заполнила зону
                if current_price > row['fvg_zone_top']:
                    bullish_fvgs.append({
                        'bottom': row['fvg_zone_bottom'],
                        'top': row['fvg_zone_top'],
                        'distance': current_price - row['fvg_zone_top']
                    })
            
            if row['fvg_bearish']:
                if current_price < row['fvg_zone_bottom']:
                    bearish_fvgs.append({
                        'top': row['fvg_zone_top'],
                        'bottom': row['fvg_zone_bottom'],
                        'distance': row['fvg_zone_bottom'] - current_price
                    })
        
        return {
            'bullish': bullish_fvgs,
            'bearish': bearish_fvgs
        }

if __name__ == "__main__":
    print("FVG module ready")
