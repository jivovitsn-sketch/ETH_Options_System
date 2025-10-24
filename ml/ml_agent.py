#!/usr/bin/env python3
"""ML AGENT - Machine Learning"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class MLAgent:
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        print("✅ ML Agent initialized")

    def predict(self, features: np.ndarray):
        if not self.models:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}
        
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        if features.shape[1] < len(self.feature_names):
            features = np.pad(features, ((0, 0), (0, len(self.feature_names) - features.shape[1])))
        
        features_scaled = self.scaler.transform(features)
        
        probas = []
        for model in self.models.values():
            proba = model.predict_proba(features_scaled)[0]
            probas.append(proba[1])
        
        avg_proba = np.mean(probas)
        
        if avg_proba > 0.55:
            return {'prediction': 'BULLISH', 'confidence': avg_proba}
        elif avg_proba < 0.45:
            return {'prediction': 'BEARISH', 'confidence': 1 - avg_proba}
        else:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}
    
    def load_models(self, filepath: str = 'ml_agent_models.pkl'):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        self.models = data['models']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        print(f"✅ Models loaded from {filepath}")

if __name__ == "__main__":
    print("ML Agent ready")
