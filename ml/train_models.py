#!/usr/bin/env python3
"""
ML TRAINING PIPELINE V20.2
Полное обучение моделей без заглушек
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

from ml.feature_engineering import FeatureEngineer

class ModelTrainer:
    """
    Обучение ML моделей
    """
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        print("✅ Model Trainer initialized")
    
    def load_data(self, symbol: str = 'BTCUSDT', days: int = 180):
        """Загрузить исторические данные"""
        data_dir = Path(__file__).parent.parent / 'data' / 'raw' / symbol
        
        if not data_dir.exists():
            print(f"❌ No data for {symbol}")
            return pd.DataFrame()
        
        files = sorted(data_dir.glob("*.csv"))[-days:]
        
        if not files:
            print(f"❌ No CSV files for {symbol}")
            return pd.DataFrame()
        
        print(f"📂 Loading {len(files)} days of data for {symbol}...")
        
        dfs = []
        for file in files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        df = pd.concat(dfs, ignore_index=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"✅ Loaded {len(df)} candles")
        return df
    
    def create_targets(self, df: pd.DataFrame, horizon: int = 24):
        """
        Создать таргеты для обучения
        horizon: через сколько часов смотрим результат
        """
        df = df.copy()
        
        # Future return
        df['target_return'] = df['close'].shift(-horizon) / df['close'] - 1
        
        # Classification target
        df['target'] = 0  # NEUTRAL
        df.loc[df['target_return'] > 0.01, 'target'] = 1  # BULLISH (>1%)
        df.loc[df['target_return'] < -0.01, 'target'] = -1  # BEARISH (<-1%)
        
        # Remove last horizon rows (no future data)
        df = df.iloc[:-horizon]
        
        return df
    
    def prepare_training_data(self, symbol: str = 'BTCUSDT', days: int = 180):
        """
        Подготовить данные для обучения
        """
        print(f"\n{'='*70}")
        print(f"📊 PREPARING TRAINING DATA")
        print(f"{'='*70}")
        
        # Load data
        df = self.load_data(symbol, days)
        
        if df.empty:
            return None, None, None, None
        
        # Create features
        df = self.feature_engineer.create_features(df)
        
        # Create targets
        df = self.create_targets(df, horizon=24)
        
        # Get feature columns
        self.feature_names = self.feature_engineer.get_feature_names(df)
        
        print(f"\n📈 Features: {len(self.feature_names)}")
        print(f"   Samples: {len(df)}")
        
        # Check class distribution
        target_dist = df['target'].value_counts()
        print(f"\n📊 Target distribution:")
        print(f"   BEARISH (-1): {target_dist.get(-1, 0)} ({target_dist.get(-1, 0)/len(df)*100:.1f}%)")
        print(f"   NEUTRAL (0):  {target_dist.get(0, 0)} ({target_dist.get(0, 0)/len(df)*100:.1f}%)")
        print(f"   BULLISH (1):  {target_dist.get(1, 0)} ({target_dist.get(1, 0)/len(df)*100:.1f}%)")
        
        # Split features and target
        X = df[self.feature_names].values
        y = df['target'].values
        
        # Train/test split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False  # No shuffle for time series
        )
        
        print(f"\n📦 Train size: {len(X_train)}")
        print(f"📦 Test size:  {len(X_test)}")
        
        # Scale features
        X_train = self.scaler.fit_transform(X_train)
        X_test = self.scaler.transform(X_test)
        
        return X_train, X_test, y_train, y_test
    
    def train_random_forest(self, X_train, y_train):
        """Train Random Forest"""
        print(f"\n🌲 Training Random Forest...")
        
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1
        )
        
        rf.fit(X_train, y_train)
        
        train_score = rf.score(X_train, y_train)
        print(f"   Train accuracy: {train_score:.2%}")
        
        return rf
    
    def train_xgboost(self, X_train, y_train):
        """Train XGBoost"""
        print(f"\n🚀 Training XGBoost...")
        
        # Convert to binary classification (BULLISH vs REST)
        y_binary = (y_train == 1).astype(int)
        
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        xgb_model.fit(X_train, y_binary)
        
        train_score = xgb_model.score(X_train, y_binary)
        print(f"   Train accuracy: {train_score:.2%}")
        
        return xgb_model
    
    def evaluate_models(self, X_test, y_test):
        """Evaluate models on test set"""
        print(f"\n{'='*70}")
        print(f"📊 MODEL EVALUATION")
        print(f"{'='*70}")
        
        for model_name, model in self.models.items():
            if model_name == 'xgboost':
                # XGBoost is binary
                y_test_binary = (y_test == 1).astype(int)
                score = model.score(X_test, y_test_binary)
            else:
                score = model.score(X_test, y_test)
            
            print(f"\n{model_name.upper()}:")
            print(f"   Test accuracy: {score:.2%}")
    
    def save_models(self, filepath: str = 'ml_agent_models_new.pkl'):
        """Save trained models"""
        data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'trained_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"\n💾 Models saved to {filepath}")
    
    def train_all(self, symbol: str = 'BTCUSDT', days: int = 180):
        """
        Train all models
        """
        print(f"\n╔════════════════════════════════════════════════╗")
        print(f"║       ML TRAINING PIPELINE V20.2              ║")
        print(f"╚════════════════════════════════════════════════╝")
        
        # Prepare data
        X_train, X_test, y_train, y_test = self.prepare_training_data(symbol, days)
        
        if X_train is None:
            print("❌ Training failed - no data")
            return
        
        # Train models
        self.models['random_forest'] = self.train_random_forest(X_train, y_train)
        self.models['xgboost'] = self.train_xgboost(X_train, y_train)
        
        # Evaluate
        self.evaluate_models(X_test, y_test)
        
        # Feature importance
        self._print_feature_importance()
        
        # Save
        self.save_models()
        
        print(f"\n{'='*70}")
        print(f"✅ TRAINING COMPLETE")
        print(f"{'='*70}")
    
    def _print_feature_importance(self):
        """Print top 20 most important features"""
        print(f"\n📊 TOP 20 FEATURES (Random Forest):")
        
        rf = self.models.get('random_forest')
        if rf is None:
            return
        
        importances = rf.feature_importances_
        indices = np.argsort(importances)[::-1][:20]
        
        for i, idx in enumerate(indices, 1):
            print(f"   {i:2d}. {self.feature_names[idx]:25s} {importances[idx]:.4f}")


if __name__ == "__main__":
    trainer = ModelTrainer()
    
    # Train on BTCUSDT data (last 180 days)
    trainer.train_all(symbol='BTCUSDT', days=180)
