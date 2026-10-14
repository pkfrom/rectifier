with open("control.js", "r", encoding="utf-8") as f:
    text = f.read()

import re

# Look for Setting or submit in control.js
for m in re.finditer(r'(?:Setting|Submit|post|control\.cgi)[^;\n]{10,100}', text, re.IGNORECASE):
    s = m.group(0)
    if any(k in s for k in ['cgi', 'ajax', 'attr', 'form', 'val', 'click']):
        print(s[:100])
