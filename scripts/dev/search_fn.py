import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
with open('control.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

for m in re.finditer(r'["\']fn["\']', text):
    idx = m.start()
    print(text[max(0, idx-60):min(len(text), idx+200)])
    print('-'*40)
