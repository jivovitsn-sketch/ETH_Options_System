#!/usr/bin/env python3
"""
SIMPLE ML AGENT - Только XGBoost (лучшая модель)
БЕЗ ENSEMBLE!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import pickle
from ml.feature_engineering import FeatureEngineer

class SimpleMLAgent:
    """
    Простой ML агент - только XGBoost
    """
    
    def __init__(self, threshold: float = 0.40):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.feature_engineer = FeatureEngineer()
        self.threshold = threshold
        print(f"✅ Simple ML Agent initialized (threshold={threshold})")
    
    def predict(self, df: pd.DataFrame):
        """Предсказание направления"""
        if self.model is None:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}
        
        try:
            # Create features
            df_features = self.feature_engineer.create_features(df)
            
            if df_features.empty or len(df_features) < 10:
                return {'prediction': 'NEUTRAL', 'confidence': 0.5}
            
            # Get last row
            X = df_features[self.feature_names].iloc[-1:].values
            
            # Scale
            X_scaled = self.scaler.transform(X)
            
            # Predict (XGBoost binary: BULLISH or not)
            proba = self.model.predict_proba(X_scaled)[0][1]
            
            # Decision
            if proba > (0.5 + self.threshold):
                direction = 'BULLISH'
                confidence = proba
            elif proba < (0.5 - self.threshold):
                direction = 'BEARISH'
                confidence = 1 - proba
            else:
                direction = 'NEUTRAL'
                confidence = 0.5
            
            return {
                'prediction': direction,
                'confidence': confidence,
                'proba_bullish': proba
            }
        
        except Exception as e:
            print(f"⚠️  Prediction error: {e}")
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}
    
    def load_models(self, filepath: str = 'ml_agent_models_new.pkl'):
        """Load XGBoost model"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['models']['xgboost']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            
            print(f"✅ XGBoost model loaded from {filepath}")
            print(f"   Features: {len(self.feature_names)}")
        
        except Exception as e:
            print(f"❌ Could not load models: {e}")

if __name__ == "__main__":
    print("Simple ML Agent ready")
