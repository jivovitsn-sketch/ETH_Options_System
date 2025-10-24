#!/usr/bin/env python3
"""LLM AGENT - Эвристика (БЕСПЛАТНО!)"""

class LLMAgent:
    def __init__(self, mode: str = 'heuristic'):
        self.mode = mode
        print("✅ LLM Agent initialized (HEURISTIC mode - FREE!)")
    
    def predict(self, context: dict):
        ml_pred = context.get('ml_prediction', 'NEUTRAL')
        trend = context.get('trend', 'NEUTRAL')
        astro = context.get('astro_direction', 'NEUTRAL')
        
        score = 0
        if ml_pred == trend and ml_pred != 'NEUTRAL':
            score += 0.3
        if ml_pred == astro and ml_pred != 'NEUTRAL':
            score += 0.25
        if ml_pred == trend == astro and ml_pred != 'NEUTRAL':
            score += 0.3
        
        if score > 0.6:
            return {'prediction': ml_pred, 'confidence': min(0.7 + score * 0.2, 0.9)}
        elif score > 0.3:
            return {'prediction': ml_pred, 'confidence': 0.6}
        else:
            return {'prediction': 'NEUTRAL', 'confidence': 0.5}

if __name__ == "__main__":
    print("LLM Agent ready")
