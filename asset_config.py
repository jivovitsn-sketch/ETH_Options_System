#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
НАСТРОЙКИ АКТИВОВ - ПОКА ЕДИНЫЕ, ПОТОМ ИНДИВИДУАЛЬНЫЕ ПОСЛЕ БЭКТЕСТА
"""

# Единая настройка для всех активов (пока нет данных для индивидуальных)
DEFAULT_MIN_CONFIDENCE = 0.75  # 75%
DEFAULT_MIN_INTERVAL_HOURS = 2  # 2 часа между сигналами

def get_min_confidence(asset):
    """Минимальная confidence (пока одинаковая для всех)"""
    return DEFAULT_MIN_CONFIDENCE

def get_min_interval(asset):
    """Минимальный интервал в часах (пока одинаковый)"""
    return DEFAULT_MIN_INTERVAL_HOURS
