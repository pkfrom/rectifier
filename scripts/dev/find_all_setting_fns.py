with open('all.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.finditer(r'[\s,{]Setting\s*:\s*function', text)
for m in matches:
    pos = m.start()
    print("Match at:", pos)
    print(text[pos:pos+400])
    print("=" * 60)
