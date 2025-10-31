# 🧠 AI_CLOUD_PROTOCOL - СТРОГАЯ ВЕРСИЯ

## 🚨 КРИТИЧЕСКИЕ ПРАВИЛА:

### 1. ДОРОЖНАЯ КАРТА = ЗАКОН
- ❌ Нельзя отступать от roadmap
- ❌ Нельзя создавать файлы не по плану
- ❌ Нельзя пропускать чекапы
- ✅ Каждый этап = Pre-flight check → Execute → Validate → Commit

### 2. ЧИСТОТА ПРОЕКТА
- ❌ НЕТ мусорных файлов
- ❌ НЕТ дублей процессов
- ❌ НЕТ старых ботов
- ✅ Только рабочие скрипты из roadmap

### 3. СИСТЕМА ЧЕКАПОВ

**Перед КАЖДЫМ действием:**
```python
def pre_flight_check():
    """Обязательная проверка перед действием"""
    checks = {
        'data_freshness': check_db_timestamps(),
        'processes_running': check_active_monitors(),
        'disk_space': check_storage(),
        'github_sync': check_git_status(),
        'roadmap_compliance': verify_stage()
    }
    
    if not all(checks.values()):
        raise Exception("Pre-flight failed - STOP")
    
    return True
```

**После КАЖДОГО действия:**
```python
def post_action_validate():
    """Обязательная проверка после действия"""
    checks = {
        'files_created': verify_expected_files(),
        'data_updated': check_db_changes(),
        'no_errors': scan_logs(),
        'git_committed': verify_commit(),
        'cleanup_done': check_no_temp_files()
    }
    
    if not all(checks.values()):
        rollback()
        raise Exception("Validation failed - ROLLBACK")
    
    return True
```

### 4. УТИЛИЗАЦИЯ МУСОРА

**Автоматическая чистка:**
```bash
# После каждого этапа
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.log" -mtime +7 -delete
find . -name "*_old.py" -delete
find . -name "*_backup*" -delete
```

**Архивация:**
```bash
# Старые файлы → archive/
mkdir -p archive/stage_{X}
mv old_file.py archive/stage_{X}/
```

### 5. GITHUB = SINGLE SOURCE OF TRUTH

**Каждый коммит:**
```bash
# 1. Проверка чистоты
git status --short | wc -l  # Должно быть 0 или только нужные файлы

# 2. Коммит ТОЛЬКО нужного
git add [конкретные_файлы]  # НЕ git add -A
git commit -m "STAGE X.Y.Z: [дата] - краткое описание"

# 3. Проверка после push
git log --oneline -1
git diff origin/main
```

---

## 📋 ПРОТОКОЛ ВЫПОЛНЕНИЯ ЭТАПА:
```
╔════════════════════════════════════════════╗
║  ЭТАП {X.Y.Z}: {НАЗВАНИЕ}                 ║
╚════════════════════════════════════════════╝

┌─ PRE-FLIGHT CHECK ────────────────────────┐
│ 1. Проверка данных (< 15 min)            │
│ 2. Проверка процессов (2-3 running)      │
│ 3. Проверка roadmap (на нужном этапе)    │
│ 4. Проверка git (синхронизирован)        │
│ 5. Проверка места (> 1GB free)           │
└───────────────────────────────────────────┘
          ↓ [ALL GREEN] ↓
┌─ EXECUTION ───────────────────────────────┐
│ 1. Создание файла                         │
│ 2. Запуск                                 │
│ 3. Мониторинг логов                       │
└───────────────────────────────────────────┘
          ↓ [SUCCESS] ↓
┌─ VALIDATION ──────────────────────────────┐
│ 1. Результаты созданы (JSON/Charts/DB)   │
│ 2. Логи без ошибок                        │
│ 3. Данные актуальны                       │
└───────────────────────────────────────────┘
          ↓ [VALIDATED] ↓
┌─ CLEANUP & COMMIT ────────────────────────┐
│ 1. Удаление temp файлов                   │
│ 2. Git add только нужных файлов           │
│ 3. Commit с правильным message            │
│ 4. Push & verify                          │
└───────────────────────────────────────────┘
          ↓ [COMPLETE] ↓
┌─ REPORT ──────────────────────────────────┐
│ 1. Обновление ROADMAP_PROGRESS.md        │
│ 2. Создание STAGE_X.Y.Z_REPORT.json      │
│ 3. Проверка соответствия roadmap          │
└───────────────────────────────────────────┘
```

---

## 🗑️ СПИСОК УТИЛИЗАЦИИ (для текущего проекта):
```
❌ УДАЛИТЬ НЕМЕДЛЕННО:
├── *_old.py
├── *_backup*
├── *_test*.py (если не в roadmap)
├── temp_*
├── unused_*
└── duplicate_*

📦 АРХИВИРОВАТЬ:
├── archive_old_bots/* (уже сделано)
├── Старые версии скриптов
└── Неиспользуемые эксперименты

✅ ОСТАВИТЬ:
├── *_monitor.py (3 файла)
├── gamma_exposure_calculator.py
├── max_pain_calculator.py
├── volatility_greeks_analyzer.py
├── archive_expired_options.py
└── Roadmap & Report файлы
```

---

## 🎯 ROADMAP ЭТАПОВ (СТРОГО):
```
STAGE 1: ДАННЫЕ
├── 1.1: Options Data Collection ✅
├── 1.2: Futures Data Collection ✅
├── 1.3: Analytics
│   ├── 1.3.1: Gamma Exposure ✅
│   ├── 1.3.2: Max Pain ✅
│   ├── 1.3.3: Volatility & Greeks ✅
│   └── 1.3.4: Combined Signals ⏳ ← ТЕКУЩИЙ
└── 1.4: Signal System ⏳

STAGE 2: СТРАТЕГИИ (после Stage 1)
STAGE 3: BACKTESTING (после Stage 2)
STAGE 4: LIVE TRADING (после Stage 3)
```

**ПРАВИЛО:** Нельзя начинать Stage 2 пока не завершен Stage 1!

---

## ⚡ АВАРИЙНЫЕ КОМАНДЫ:
```bash
# Откат к последнему stable state
git reset --hard origin/main
killall python3
./restart_system.sh

# Полная чистка
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
git clean -fdx  # Осторожно!

# Проверка состояния
./system_health_check.sh
```

---

## 📊 МЕТРИКИ КОНТРОЛЯ:
```
✅ ХОРОШО:
- Активных процессов: 2-3
- Файлов .py в корне: < 20
- Размер данных: растёт линейно
- Commits: чистые, с описанием
- Roadmap: этапы последовательны

❌ ПЛОХО:
- Процессов > 5 (дубли!)
- Файлов .py > 30 (мусор!)
- Данные не обновляются
- Commits без описания
- Пропущенные этапы roadmap
```

---

## 🚨 СИСТЕМА ШТРАФОВ (для ИИ):

Если ИИ нарушает протокол:
1. ❌ Создал файл не по roadmap → ROLLBACK + удалить
2. ❌ Пропустил pre-flight check → STOP + исправить
3. ❌ Не сделал cleanup → WARNING + очистить
4. ❌ Коммит всего подряд (git add -A) → REVERT
5. ❌ Старый мусор остался → УТИЛИЗИРОВАТЬ

---

## ✅ ФИНАЛЬНЫЙ CHECKLIST ЭТАПА:
```
[ ] Pre-flight check пройден
[ ] Код создан и работает
[ ] Результаты валидны
[ ] Логи чистые
[ ] Мусор удалён
[ ] Git коммит чистый
[ ] Roadmap обновлён
[ ] Отчёт создан
[ ] Следующий этап определён
```

**ТОЛЬКО ПОСЛЕ ВСЕХ ✅ → ПЕРЕХОД К СЛЕДУЮЩЕМУ ЭТАПУ!**
