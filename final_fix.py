#!/usr/bin/env python3

with open('send_smart_signal_v2.py', 'r') as f:
    lines = f.readlines()

# Исправляем конкретные проблемные строки (277-280)
for i in range(len(lines)):
    # Строка 277: добавляем отступ для strategies.append
    if i == 276 and 'strategies.append(f"Iron Condor' in lines[i] and not lines[i].startswith('                    '):
        lines[i] = '                    ' + lines[i].lstrip()
    
    # Строка 278: исправляем else
    if i == 277 and 'else:' in lines[i]:
        lines[i] = '                else:\n'
    
    # Строка 279: добавляем отступ для следующего strategies.append
    if i == 278 and 'strategies.append(f"Iron Condor' in lines[i] and not lines[i].startswith('                    '):
        lines[i] = '                    ' + lines[i].lstrip()

with open('send_smart_signal_v2.py', 'w') as f:
    f.writelines(lines)

print("✅ Окончательное исправление применено")
