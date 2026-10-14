import re
with open('web_assets/all.js', 'r', encoding='utf-8', errors='ignore') as fp:
    text = fp.read()
matches = set(re.findall(r'[^a-zA-Z0-9_]([a-zA-Z0-9_\./\-]*history[a-zA-Z0-9_\./\-]*)', text, re.I))
for m in sorted(matches):
    print(m)
