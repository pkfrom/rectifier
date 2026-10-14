import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
with open('control.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

for m in re.finditer(r'\.on\([\'"]click[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]', text):
    print(m.group(0))

print("=== Search for post= or attr('post') ===")
for m in re.finditer(r'(?:post|attr\([\'"]post[\'"]\))', text):
    idx = m.start()
    print(text[max(0, idx-80):min(len(text), idx+250)])
    print('='*50)
