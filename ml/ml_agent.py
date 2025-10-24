#!/usr/bin/env python3
"""ML AGENT - Machine Learning with NEW models"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import pickle
from ml.feature_engineering import FeatureEngineer

class MLAgent:
    def __init__(self):
        self.models = {}
        self.scaler = None
        self.feature_names = []
        self.feature_engineer = FeatureEngineer()
        print("✅ ML Agent initialized")

    def predict(self, df: pd.DataFrame):
        """Predict with ensemble of models"""
        if not self.models:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}
        
        # Create features
        df_features = self.feature_engineer.create_features(df)
        
        if df_features.empty or len(df_features) < 10:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}
        
        # Get last row features
        X = df_features[self.feature_names].iloc[-1:].values
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict with all models
        predictions = []
        
        # Random Forest (multiclass)
        if 'random_forest' in self.models:
            rf_pred = self.models['random_forest'].predict(X_scaled)[0]
            rf_proba = self.models['random_forest'].predict_proba(X_scaled)[0]
            predictions.append({
                'pred': rf_pred,
                'proba': max(rf_proba)
            })
        
        # XGBoost (binary: bullish or not)
        if 'xgboost' in self.models:
            xgb_proba = self.models['xgboost'].predict_proba(X_scaled)[0][1]
            xgb_pred = 1 if xgb_proba > 0.55 else (0 if xgb_proba < 0.45 else 0)
            predictions.append({
                'pred': xgb_pred,
                'proba': abs(xgb_proba - 0.5) * 2  # Convert to 0-1 confidence
            })
        
        # Ensemble vote
        if not predictions:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}
        
        # Count votes
        votes = {'BULLISH': 0, 'BEARISH': 0, 'NEUTRAL': 0}
        total_confidence = 0
        
        for p in predictions:
            if p['pred'] == 1:
                votes['BULLISH'] += 1
            elif p['pred'] == -1:
                votes['BEARISH'] += 1
            else:
                votes['NEUTRAL'] += 1
            total_confidence += p['proba']
        
        # Get majority
        final_direction = max(votes, key=votes.get)
        avg_confidence = total_confidence / len(predictions)
        
        return {
            'prediction': final_direction,
            'confidence': avg_confidence
        }
    
    def load_models(self, filepath: str = 'ml_agent_models_new.pkl'):
        """Load trained models"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            self.models = data['models']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            print(f"✅ Models loaded from {filepath}")
        except Exception as e:
            print(f"⚠️  Could not load models: {e}")

if __name__ == "__main__":
    print("ML Agent ready")
