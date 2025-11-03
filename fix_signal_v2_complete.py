#!/usr/bin/env python3

with open('send_smart_signal_v2.py', 'r') as f:
    content = f.read()

# Заменяем проблемный блок целиком
old_block = '''            if call_wall and put_wall:
                if put_wall < 10 or call_wall < 10:
                strategies.append(f"Iron Condor ${put_wall:.2f}-${call_wall:.2f}")
            else:
                strategies.append(f"Iron Condor ${put_wall:,.0f}-${call_wall:,.0f}")'''

new_block = '''            if call_wall and put_wall:
                if put_wall < 10 or call_wall < 10:
                    strategies.append(f"Iron Condor ${put_wall:.2f}-${call_wall:.2f}")
                else:
                    strategies.append(f"Iron Condor ${put_wall:,.0f}-${call_wall:,.0f}")'''

content = content.replace(old_block, new_block)

with open('send_smart_signal_v2.py', 'w') as f:
    f.write(content)

print("✅ send_smart_signal_v2.py полностью исправлен")
