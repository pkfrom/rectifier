import urllib.request

url = "http://10.209.30.21/app/www_user/html/eng/tmp.setting_tabs.html"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=5) as r:
    text = r.read().decode('utf-8', errors='ignore')

with open("tmp_setting_tabs.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Saved tmp_setting_tabs.html, length:", len(text))
print(text[:1000])
