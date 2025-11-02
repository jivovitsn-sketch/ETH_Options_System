# ПАТЧ для signal_analyzer.py - метод _analyze_timing

def _analyze_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Анализ тайминговых индикаторов - ОБНОВЛЕНО"""
    confidence = 0.5
    signal = 'NEUTRAL'
    reasons = []
    
    # PCR RSI
    pcr_rsi = data.get('pcr_rsi')
    if pcr_rsi is not None:
        if pcr_rsi > 70:
            confidence += 0.12
            signal = 'BULLISH'
            reasons.append(f"PCR RSI {pcr_rsi:.0f} (fear)")
        elif pcr_rsi < 30:
            confidence -= 0.12
            signal = 'BEARISH'
            reasons.append(f"PCR RSI {pcr_rsi:.0f} (greed)")
    
    # GEX RSI
    gex_rsi = data.get('gex_rsi')
    if gex_rsi is not None:
        if gex_rsi > 70:
            confidence += 0.08
            reasons.append(f"GEX RSI {gex_rsi:.0f} (high)")
        elif gex_rsi < 30:
            confidence -= 0.08
            reasons.append(f"GEX RSI {gex_rsi:.0f} (low)")
    
    # OI MACD
    oi_macd = data.get('oi_macd')
    if oi_macd and 'histogram' in oi_macd:
        hist = oi_macd['histogram']
        if abs(hist) > 100:
            if hist > 0:
                confidence += 0.10
                signal = 'BULLISH' if signal == 'NEUTRAL' else signal
                reasons.append(f"OI MACD +{hist:.0f}")
            else:
                confidence -= 0.10
                signal = 'BEARISH' if signal == 'NEUTRAL' else signal
                reasons.append(f"OI MACD {hist:.0f}")
    
    return {
        'signal': signal,
        'confidence': max(min(confidence, 1.0), 0.0),
        'reasoning': reasons,
        'data_used': ['pcr_rsi', 'gex_rsi', 'oi_macd']
    }
