# 🔧 DISCORD SETUP GUIDE

## 1. Создать Discord Server

1. Открой Discord
2. Нажми "+" → "Create My Own" → "For me and my friends"
3. Назови: "ETH Options Trading"

---

## 2. Создать 3 Канала

### Free Channel (для всех подписчиков)
```
#free-signals
```
Базовые сигналы: BUY/SELL + цена

### VIP Channel (платная подписка)
```
#vip-analytics
```
Детальная аналитика: Greeks, TP levels, R:R, качество сигнала

### Admin Channel (только для тебя)
```
#admin-logs
```
Служебная информация: errors, backups, health checks, GitHub sync

---

## 3. Создать Webhooks

### Для каждого канала:

1. Правой кнопкой на канале → **Edit Channel**
2. **Integrations** → **Webhooks** → **Create Webhook**
3. Назови (например: "Free Signals Bot")
4. **Copy Webhook URL**
5. Сохрани URL

---

## 4. Добавить URLs в Config
```bash
nano config/discord.json
```

Вставь свои webhooks:
```json
{
  "free_channel": "https://discord.com/api/webhooks/YOUR_FREE_WEBHOOK",
  "vip_channel": "https://discord.com/api/webhooks/YOUR_VIP_WEBHOOK",
  "admin_channel": "https://discord.com/api/webhooks/YOUR_ADMIN_WEBHOOK"
}
```

**Сохрани:** Ctrl+O, Enter, Ctrl+X

---

## 5. Тест
```bash
python3 bot/discord_multi_channel.py
```

Должны придти тестовые сообщения в каналы!

---

## 📱 Структура Сообщений

### FREE Channel
```
🟢 BUY Signal
Asset: ETHUSDT
Price: $3,939.00
```

### VIP Channel
```
🟢 VIP Trade Opened
Asset: ETHUSDT
Strategy: Bull Call 60DTE
Entry: $3,939.00
Size: $500.00
Delta: 0.0711
Theta: 0.05/day
Risk/Reward: 1:2
```

### ADMIN Channel
```
🚀 System Started
Mode: Paper Trading
Time: 2025-10-25 12:00:00

💾 Backup Complete
Files: 109
Size: 2.3 MB

📁 GitHub Sync Complete
Commit: Auto-sync trades
Files: 5
```

---

## 🎯 Готово!

Теперь все сигналы, сделки и служебная информация будут автоматически отправляться в Discord!
