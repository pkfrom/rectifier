import re

for fname in ['all.js', 'login.js']:
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        t = f.read()
    print(f"=== File: {fname} ===")
    for m in re.finditer(r'type\s*:\s*["\']post["\']', t, re.IGNORECASE):
        s = max(0, m.start() - 50)
        e = min(len(t), m.end() + 350)
        print("MATCH:", t[s:e])
        print("-" * 50)
