import urllib.request
import re

url = "http://10.209.30.21/app/www_user/html/js/release/emerson.control.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=5) as r:
    text = r.read().decode('utf-8', errors='ignore')

with open("control.js", "w", encoding="utf-8") as f:
    f.write(text)

print("Downloaded control.js, length:", len(text))

# Search for btn_set
for m in re.finditer(r'btn_set', text):
    start = max(0, m.start() - 150)
    end = min(len(text), m.end() + 350)
    print("\n=== btn_set match ===")
    print(text[start:end])
