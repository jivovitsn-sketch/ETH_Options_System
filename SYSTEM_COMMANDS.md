# ETH OPTIONS SYSTEM - УПРАВЛЕНИЕ

## СТАТУС
```bash
python3 system_status.py
```

## РУЧНОЙ ЗАПУСК СИГНАЛОВ
```bash
python3 working_multi_signals.py
```

## ЛОГИ
```bash
tail -f logs/signals.log
```

## УПРАВЛЕНИЕ CRONTAB
```bash
crontab -l                    # Посмотреть
crontab -r                    # Удалить все
crontab -e                    # Редактировать
```

## АКТИВЫ И ТРИГГЕРЫ
- ETH: BUY >$4000, SELL <$3800
- BTC: BUY >$72000, SELL <$68000  
- SOL: BUY >$200, SELL <$160
- XRP: BUY >$2.8, SELL <$2.2

## РАСПИСАНИЕ
Автозапуск каждые 6 часов: 00:00, 06:00, 12:00, 18:00

## VIP КАНАЛ
-1003001252760 (ETH Options - VIP Group)
