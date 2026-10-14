with open('all.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.finditer(r'(?:Setting\s*[:=]\s*function|fn\.Setting)', text)
for m in matches:
    print("Match at:", m.start())
    print(text[m.start():m.start()+500])
    print("-" * 50)
