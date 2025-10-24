#!/usr/bin/env python3
"""
FEATURE ENGINEERING V20.2
Полный набор технических индикаторов и паттернов
БЕЗ ЗАГЛУШЕК!
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

class FeatureEngineer:
    """
    Создание фичей для ML моделей
    """
    
    def __init__(self):
        self.feature_names = []
        print("✅ Feature Engineer initialized")
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Создать ВСЕ фичи
        """
        df = df.copy()
        
        print(f"📊 Creating features for {len(df)} candles...")
        
        # 1. PRICE FEATURES
        df = self._add_price_features(df)
        
        # 2. TECHNICAL INDICATORS
        df = self._add_technical_indicators(df)
        
        # 3. VOLUME FEATURES
        df = self._add_volume_features(df)
        
        # 4. VOLATILITY FEATURES
        df = self._add_volatility_features(df)
        
        # 5. PATTERN FEATURES
        df = self._add_pattern_features(df)
        
        # 6. MOMENTUM FEATURES
        df = self._add_momentum_features(df)
        
        # Drop NaN
        initial_len = len(df)
        df = df.dropna()
        dropped = initial_len - len(df)
        
        print(f"✅ Created {len([c for c in df.columns if c not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']])} features")
        print(f"   Dropped {dropped} rows with NaN")
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price-based features"""
        
        # Returns
        df['return_1'] = df['close'].pct_change(1)
        df['return_5'] = df['close'].pct_change(5)
        df['return_10'] = df['close'].pct_change(10)
        df['return_20'] = df['close'].pct_change(20)
        
        # High-Low spread
        df['hl_spread'] = (df['high'] - df['low']) / df['close']
        
        # Close position in range
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-10)
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Технические индикаторы"""
        
        # === SMA ===
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
        
        # SMA crosses
        df['sma_5_20_cross'] = (df['sma_5'] > df['sma_20']).astype(int)
        df['sma_20_50_cross'] = (df['sma_20'] > df['sma_50']).astype(int)
        
        # === EMA ===
        for period in [12, 26]:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # === RSI ===
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # RSI zones
        df['rsi_oversold'] = (df['rsi_14'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi_14'] > 70).astype(int)
        
        # === MACD ===
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # === Bollinger Bands ===
        for period in [20]:
            sma = df['close'].rolling(period).mean()
            std = df['close'].rolling(period).std()
            df[f'bb_upper_{period}'] = sma + 2 * std
            df[f'bb_lower_{period}'] = sma - 2 * std
            df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / sma
            df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'] + 1e-10)
        
        # === Stochastic ===
        low_14 = df['low'].rolling(14).min()
        high_14 = df['high'].rolling(14).max()
        df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14 + 1e-10)
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        
        return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volume features"""
        
        # Volume moving averages
        df['volume_sma_5'] = df['volume'].rolling(5).mean()
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        
        # Volume ratio
        df['volume_ratio_5'] = df['volume'] / (df['volume_sma_5'] + 1e-10)
        df['volume_ratio_20'] = df['volume'] / (df['volume_sma_20'] + 1e-10)
        
        # Price-Volume
        df['pv_trend'] = df['close'].pct_change() * df['volume_ratio_5']
        
        return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volatility features"""
        
        # ATR (Average True Range)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr_14'] = df['tr'].rolling(14).mean()
        df['atr_ratio'] = df['atr_14'] / df['close']
        
        # Historical volatility
        df['volatility_10'] = df['return_1'].rolling(10).std()
        df['volatility_20'] = df['return_1'].rolling(20).std()
        
        return df
    
    def _add_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pattern recognition features"""
        
        # Candle patterns
        df['body'] = df['close'] - df['open']
        df['body_pct'] = df['body'] / (df['open'] + 1e-10)
        
        df['upper_shadow'] = df['high'] - np.maximum(df['open'], df['close'])
        df['lower_shadow'] = np.minimum(df['open'], df['close']) - df['low']
        
        # Bullish/Bearish
        df['bullish_candle'] = (df['close'] > df['open']).astype(int)
        
        # Doji
        df['is_doji'] = (abs(df['body_pct']) < 0.001).astype(int)
        
        # Hammer/Shooting Star
        df['is_hammer'] = ((df['lower_shadow'] > 2 * abs(df['body'])) & (df['bullish_candle'] == 1)).astype(int)
        df['is_shooting_star'] = ((df['upper_shadow'] > 2 * abs(df['body'])) & (df['bullish_candle'] == 0)).astype(int)
        
        # Swing highs/lows
        df['swing_high'] = ((df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))).astype(int)
        df['swing_low'] = ((df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))).astype(int)
        
        return df
    
    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Momentum indicators"""
        
        # Rate of Change (ROC)
        for period in [5, 10, 20]:
            df[f'roc_{period}'] = df['close'].pct_change(period)
        
        # Momentum
        df['momentum_10'] = df['close'] - df['close'].shift(10)
        df['momentum_20'] = df['close'] - df['close'].shift(20)
        
        # Price acceleration
        df['acceleration'] = df['return_1'].diff()
        
        return df
    
    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """Получить список фичей (без target и timestamp)"""
        exclude = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                   'target', 'target_return', 'target_direction']
        return [col for col in df.columns if col not in exclude]


if __name__ == "__main__":
    print("Feature Engineering ready")
