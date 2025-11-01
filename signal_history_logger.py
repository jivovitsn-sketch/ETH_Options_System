#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIGNAL HISTORY LOGGER - Stage 1.4.8
Логирование полной истории сигналов для бэктеста и анализа
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalHistoryLogger:
    """Логирование полной истории сигналов для бэктеста и анализа"""
    
    def __init__(self):
        self.db_path = './data/signal_history.db'
        self.json_dir = Path('./data/signal_history_json/')
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Инициализация БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                asset TEXT,
                signal_type TEXT,
                confidence REAL,
                strength TEXT,
                spot_price REAL,
                config_hash TEXT,
                data_quality_status TEXT,
                data_quality_completeness REAL,
                reasoning TEXT,
                data_snapshot_json TEXT,
                strategies_json TEXT
            )
        ''')
        
        # Индексы
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON signal_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset ON signal_history(asset)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_config ON signal_history(config_hash)')
        
        conn.commit()
        conn.close()
        logger.info("✅ Signal history database initialized")
    
    def log_signal(self, signal_result: Dict[str, Any]):
        """Сохранить полную историю сигнала"""
        
        try:
            signal = signal_result['signal']
            data_snapshot = signal_result['data_snapshot']
            
            # Сохраняем в БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signal_history (
                    timestamp, asset, signal_type, confidence, strength,
                    spot_price, config_hash, data_quality_status,
                    data_quality_completeness, reasoning,
                    data_snapshot_json, strategies_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(datetime.now().timestamp()),
                signal_result['asset'],
                signal['signal_type'],
                signal['confidence'],
                signal['strength'],
                data_snapshot.get('spot_price'),
                signal.get('config_version'),
                data_snapshot.get('quality', {}).get('status'),
                data_snapshot.get('quality', {}).get('completeness'),
                json.dumps(signal.get('reasoning', [])),
                json.dumps(data_snapshot, default=str),
                json.dumps(signal_result.get('strategies', []), default=str)
            ))
            
            conn.commit()
            conn.close()
            
            # Сохраняем JSON
            self._save_to_json(signal_result)
            
            logger.info(f"📝 Logged signal for {signal_result['asset']}")
            
        except Exception as e:
            logger.error(f"❌ Error logging signal: {e}")
    
    def _save_to_json(self, signal_result: Dict[str, Any]):
        """Сохранение в JSON для ML обработки"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            asset = signal_result['asset']
            filename = f"{asset}_signal_{timestamp}.json"
            filepath = self.json_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(signal_result, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
    
    def get_signals_by_config(self, config_hash: str, limit: int = 100):
        """Получить сигналы для определенного конфига"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signal_history
            WHERE config_hash = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (config_hash, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_performance_stats(self, config_hash: str):
        """Статистика по конфигурации для бэктеста"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN strength = 'STRONG' THEN 1 END) as strong_signals,
                COUNT(CASE WHEN signal_type = 'BULLISH' THEN 1 END) as bullish_count,
                COUNT(CASE WHEN signal_type = 'BEARISH' THEN 1 END) as bearish_count
            FROM signal_history
            WHERE config_hash = ?
        ''', (config_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_signals': result[0],
            'avg_confidence': result[1],
            'strong_signals': result[2],
            'bullish_count': result[3],
            'bearish_count': result[4]
        }


if __name__ == '__main__':
    # Тестирование
    from data_integrator import DataIntegrator
    from signal_analyzer import SignalAnalyzer
    from backtest_params import get_default_config
    
    print("=" * 60)
    print("🧪 SIGNAL HISTORY LOGGER TEST")
    print("=" * 60)
    
    logger_instance = SignalHistoryLogger()
    
    config = get_default_config()
    integrator = DataIntegrator()
    analyzer = SignalAnalyzer(config)
    
    print("\n📝 Генерируем и логируем сигналы...")
    
    for asset in ['BTC', 'ETH']:
        data = integrator.get_all_data(asset)
        signal = analyzer.analyze(data)
        
        if signal:
            signal_result = {
                'asset': asset,
                'signal': signal,
                'data_snapshot': data,
                'strategies': []
            }
            
            logger_instance.log_signal(signal_result)
            print(f"✅ {asset}: Logged")
    
    # Статистика
    print("\n📊 Статистика:")
    stats = logger_instance.get_performance_stats(analyzer._get_config_hash())
    print(f"  Total signals: {stats['total_signals']}")
    print(f"  Avg confidence: {stats['avg_confidence']*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЁН")
    print("=" * 60)
