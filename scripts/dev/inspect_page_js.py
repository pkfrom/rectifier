import urllib.request

url = "http://10.209.30.21/app/www_user/html/js/release/emerson.page.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=5) as r:
    text = r.read().decode('utf-8', errors='ignore')

with open("page.js", "w", encoding="utf-8") as f:
    f.write(text)

print("Downloaded page.js, length:", len(text))

import re
# Search for web_cgi or btn_set or Setting in page.js
for m in re.finditer(r'(?:web_cgi|btn_set|\.cgi|post=)[^\n;]{5,100}', text, re.IGNORECASE):
    print("Match:", m.group(0)[:100])
