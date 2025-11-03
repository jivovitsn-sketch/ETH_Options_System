#!/usr/bin/env python3
with open('send_smart_signal_v2.py', 'r') as f:
    lines = f.readlines()

# Исправляем строку 277 и следующие
for i in range(len(lines)):
    if i == 276:  # строка 277 (индекс 276)
        if 'if put_wall < 10 or call_wall < 10:' in lines[i]:
            # Добавляем отступ для следующей строки
            if i+1 < len(lines):
                lines[i+1] = '        ' + lines[i+1].lstrip()
    if i == 278:  # строка 279
        if 'else:' in lines[i]:
            # Убедимся что else тоже с правильным отступом
            lines[i] = '        else:\n'
    if i == 279:  # строка 280
        if 'strategies.append' in lines[i] and not lines[i].startswith('        '):
            lines[i] = '            ' + lines[i].lstrip()

with open('send_smart_signal_v2.py', 'w') as f:
    f.writelines(lines)

print("✅ Исправлены отступы в send_smart_signal_v2.py")
