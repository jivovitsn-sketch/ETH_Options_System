#!/usr/bin/env python3
import re

with open('send_smart_signal_v2.py', 'r') as f:
    content = f.read()

# Исправляем возможные проблемы с отступами
content = re.sub(r'if\s+.*:\s*\n\s*(\w+)', r'if \1', content)

with open('send_smart_signal_v2.py', 'w') as f:
    f.write(content)

print("✅ send_smart_signal_v2.py исправлен")
