import urllib.request
import re

url = "http://10.209.30.21/app/www_user/html/js/emerson.base.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=5) as r:
    text = r.read().decode('utf-8', errors='ignore')

print("emerson.base.js length:", len(text))

# Search for btn_set
matches = re.finditer(r'btn_set', text)
for m in matches:
    pos = m.start()
    print("Match at pos:", pos)
    print(text[max(0, pos-100):min(len(text), pos+300)])
    print("=" * 60)
