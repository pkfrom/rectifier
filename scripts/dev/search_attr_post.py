with open('all.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.finditer(r'attr\s*\(\s*["\']post["\']\s*\)', text)
for m in matches:
    print("Match at:", m.start())
    print(text[max(0, m.start()-100):min(len(text), m.end()+400)])
    print("=" * 60)
