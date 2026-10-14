with open('all.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'btn_set', text)]
print(f"Total btn_set matches: {len(matches)}")
for idx, pos in enumerate(matches):
    print(f"\n--- Match {idx} (pos {pos}) ---")
    start = max(0, pos - 150)
    end = min(len(text), pos + 350)
    print(text[start:end])
