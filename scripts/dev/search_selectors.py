import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
for name in ['control.js', 'page.js', 'config.js']:
    with open(name, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    for pattern in [r'\.btn_set\b', r'#settingForm', r'\bbtn_set\b', r'web_cgi_control']:
        for m in re.finditer(pattern, text):
            idx = m.start()
            print(f'=== In {name} match {pattern} at {idx} ===')
            print(text[max(0, idx-80):min(len(text), idx+250)])
