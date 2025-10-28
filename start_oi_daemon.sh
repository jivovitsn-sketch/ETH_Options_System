#!/bin/bash

# Создаем tmux сессию для фонового запуска
SESSION_NAME="oi_signals"

# Убиваем существующую сессию если есть
tmux kill-session -t $SESSION_NAME 2>/dev/null

# Создаем новую сессию в фоне
tmux new-session -d -s $SESSION_NAME -c "$(pwd)"

# Запускаем демон OI сигналов
tmux send-keys -t $SESSION_NAME "python3 oi_signals_system.py daemon" C-m

echo "OI Signals daemon started in tmux session: $SESSION_NAME"
echo "To view: tmux attach -t $SESSION_NAME"
echo "To stop: tmux kill-session -t $SESSION_NAME"
