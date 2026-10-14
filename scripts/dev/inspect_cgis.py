import urllib.request
import re

ip = "10.209.30.21"

def download(url_path, save_as):
    url = f"http://{ip}{url_path}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as r:
        content = r.read()
    with open(save_as, "wb") as f:
        f.write(content)
    print(f"Downloaded {url_path} -> {save_as} ({len(content)} bytes)")

download("/app/www_user/html/js/emerson.login.min.js", "login.js")
download("/app/www_user/html/js/emerson.all.js", "all.js")

# Inspect login.js
with open("login.js", "r", encoding="utf-8", errors="ignore") as f:
    login_text = f.read()

print("\n--- Searches in login.js ---")
cgi_in_login = re.findall(r'[^"\';\s]+(?:cgi|login)[^"\';\s]*', login_text)
print("Endpoints in login.js:", set(cgi_in_login[:10]))

# Inspect all.js
with open("all.js", "r", encoding="utf-8", errors="ignore") as f:
    all_text = f.read()

print("\n--- Searches in all.js for CGI / Save / Setting ---")
cgis = re.findall(r'["\']([^"\']*\.cgi[^"\']*)["\']', all_text)
print("CGIs in all.js:", set(cgis))

# Look for setting submit pattern
for m in re.finditer(r'web_cgi_main\.cgi', all_text):
    start = max(0, m.start() - 150)
    end = min(len(all_text), m.end() + 150)
    print("\nFound web_cgi_main snippet:")
    print(all_text[start:end])
