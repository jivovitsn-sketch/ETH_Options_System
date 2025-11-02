#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURATION - Централизованная конфигурация системы
"""

# СПИСОК АКТИВОВ ДЛЯ АНАЛИЗА
ASSETS = ['BTC', 'ETH', 'XRP', 'SOL', 'DOGE', 'MNT']

# ПАРАМЕТРЫ АНАЛИЗА
ANALYSIS_WINDOW_DAYS = 45  # Скользящее окно для экспираций
MIN_CONFIDENCE = 0.60  # Минимальный confidence для сигналов
ANTI_DUPLICATE_HOURS = 4  # Окно антидубликатов

# ВЕСА ГРУПП
FUTURES_WEIGHT = 0.35
OPTIONS_WEIGHT = 0.45
TIMING_WEIGHT = 0.20

# ПАРАМЕТРЫ СТЕНОК
WALL_OI_THRESHOLD = 500  # Минимальный OI для стенки
WALL_ANALYSIS_HOURS = 24  # Анализ динамики стенок

# HEALTH MONITORING
HEALTH_CHECK_INTERVAL = 5  # минут
MAX_RESTART_ATTEMPTS = 3

# TELEGRAM
ADMIN_CHAT_ID = None  # Задаётся из .env

# DATABASE PATHS
DB_UNLIMITED_OI = './data/unlimited_oi.db'
DB_SIGNAL_HISTORY = './data/signal_history.db'
DB_LIQUIDATIONS = './data/liquidations.db'
DB_FUNDING_RATES = './data/funding_rates.db'
