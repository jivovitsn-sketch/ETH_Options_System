#!/usr/bin/env python3
"""
ENSEMBLE V2 - ML + ASTRO
Два агента: технический анализ + астрология
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime

from ml.simple_ml_agent import SimpleMLAgent
from ml.astro_agent import AstroAgent

class EnsembleV2:
    """
    Новый ансамбль: ML (60%) + Astro (40%)
    """
    
    def __init__(self, ml_weight: float = 0.60, astro_weight: float = 0.40):
        self.ml_agent = SimpleMLAgent(threshold=0.10)
        self.astro_agent = AstroAgent()
        
        self.ml_weight = ml_weight
        self.astro_weight = astro_weight
        
        print(f"✅ Ensemble V2 initialized")
        print(f"   ML Weight: {ml_weight:.0%}")
        print(f"   Astro Weight: {astro_weight:.0%}")
    
    def load_ml_models(self, filepath: str = 'ml_agent_models_new.pkl'):
        """Load ML models"""
        self.ml_agent.load_models(filepath)
    
    def predict(self, df: pd.DataFrame, date: datetime = None):
        """
        Комбинированное предсказание
        """
        if date is None:
            date = df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
        
        # ML prediction
        ml_pred = self.ml_agent.predict(df)
        
        # Astro prediction
        astro_pred = self.astro_agent.predict(date)
        
        # Weighted voting
        scores = {'BULLISH': 0, 'BEARISH': 0, 'NEUTRAL': 0}
        
        # ML vote
        ml_dir = ml_pred['prediction']
        ml_conf = ml_pred['confidence']
        scores[ml_dir] += self.ml_weight * ml_conf
        
        # Astro vote
        astro_dir = astro_pred['prediction']
        astro_conf = astro_pred['confidence']
        scores[astro_dir] += self.astro_weight * astro_conf
        
        # Winner
        final_direction = max(scores, key=scores.get)
        total = sum(scores.values())
        final_confidence = scores[final_direction] / total if total > 0 else 0.5
        
        # Agreement bonus
        if ml_dir == astro_dir and ml_dir != 'NEUTRAL':
            final_confidence *= 1.2
            final_confidence = min(final_confidence, 0.90)
        
        return {
            'prediction': final_direction,
            'confidence': final_confidence,
            'ml_pred': ml_dir,
            'astro_pred': astro_dir,
            'agreement': ml_dir == astro_dir
        }

if __name__ == "__main__":
    print("Ensemble V2 ready")
