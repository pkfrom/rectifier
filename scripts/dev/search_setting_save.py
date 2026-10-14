with open('all.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re

# Look for Setting or Save or control_type or post in all.js
for m in re.finditer(r'(?:control_type|web_cgi|Save|Setting|submit)[^;]{10,120}', text, re.IGNORECASE):
    snippet = m.group(0)
    if any(k in snippet for k in ['cgi', 'POST', 'ajax', 'val', 'url', 'data']):
        print(snippet[:120])
