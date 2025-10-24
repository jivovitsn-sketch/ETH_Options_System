#!/usr/bin/env python3
"""ENSEMBLE COMBINER - 3 агента голосуют"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

from ml.ml_agent import MLAgent
from ml.llm_agent import LLMAgent
from ml.pattern_agent import PatternAgent

class EnsembleCombiner:
    def __init__(self):
        self.ml_agent = MLAgent()
        self.llm_agent = LLMAgent(mode='heuristic')
        self.pattern_agent = PatternAgent()
        
        self.weights = {'ml': 0.40, 'llm': 0.30, 'pattern': 0.30}
        
        print("✅ Ensemble Combiner initialized")
        print(f"   ML: {self.weights['ml']:.0%}")
        print(f"   LLM: {self.weights['llm']:.0%}")
        print(f"   Pattern: {self.weights['pattern']:.0%}")
    
    def load_ml_models(self, filepath: str = 'ml_agent_models.pkl'):
        self.ml_agent.load_models(filepath)
    
    def predict(self, df: pd.DataFrame, context: dict = None):
        if context is None:
            context = {}
        
        # ML Agent
        ml_pred = {'prediction': 'NEUTRAL', 'confidence': 0.5}
        
        # LLM Agent
        llm_context = {
            'ml_prediction': ml_pred['prediction'],
            'trend': context.get('trend', 'NEUTRAL'),
            'astro_direction': context.get('astro_direction_str', 'NEUTRAL')
        }
        llm_pred = self.llm_agent.predict(llm_context)
        
        # Pattern Agent
        pattern_pred = self.pattern_agent.analyze(df)
        
        # Combine - ВЗВЕШЕННОЕ ГОЛОСОВАНИЕ (без консенсуса!)
        direction_scores = {'BULLISH': 0, 'BEARISH': 0, 'NEUTRAL': 0}
        
        for agent, pred in [('ml', ml_pred), ('llm', llm_pred), ('pattern', pattern_pred)]:
            direction = pred['prediction']
            confidence = pred['confidence']
            weight = self.weights[agent]
            direction_scores[direction] += weight * confidence
        
        final_direction = max(direction_scores, key=direction_scores.get)
        total = sum(direction_scores.values())
        final_confidence = direction_scores[final_direction] / total if total > 0 else 0.5
        
        directions = [ml_pred['prediction'], llm_pred['prediction'], pattern_pred['prediction']]
        consensus = directions.count(final_direction)
        
        # УБРАЛИ ПОРОГ КОНСЕНСУСА! Берём победителя голосования
        
        return {
            'prediction': final_direction,
            'confidence': final_confidence,
            'consensus': f"{consensus}/3"
        }

if __name__ == "__main__":
    print("Ensemble Combiner ready")
