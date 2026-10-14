import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import base64
import time
import json
from collect_rectifier_inventory import parse_device_data

def test_set_lvd(ip='10.209.30.21'):
    print(f"Connecting to {ip}...")
    # 1. Login
    login_url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_main.cgi?_={int(time.time()*1000)}"
    u_b64 = base64.b64encode(b"admin").decode()
    p_b64 = base64.b64encode(b"640275").decode()
    post_data = f"user_name={u_b64}&user_password={p_b64}".encode('utf-8')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f'http://{ip}/app/www_user/html/eng/index.html'
    }
    
    req = urllib.request.Request(login_url, data=post_data, headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        body = resp.read().decode('utf-8-sig', errors='ignore').strip()
        login_res = json.loads(body)
    
    if login_res.get('status') != 1:
        print("Login failed:", login_res)
        return
        
    cookie_str = login_res.get('cookie', '')
    cookies = {}
    for item in cookie_str.split(','):
        if '=' in item:
            k, v = item.split('=', 1)
            cookies[k.strip()] = v.strip()
    session_id = cookies.get('sessionId')
    print(f"Logged in. sessionId: {session_id}")
    
    # 2. Get setting row
    setting_url = f"http://{ip}/var/datas/data.setting.html?_={int(time.time()*1000)}"
    req_set = urllib.request.Request(setting_url, headers=headers)
    with urllib.request.urlopen(req_set, timeout=8) as resp:
        set_data = parse_device_data(resp.read())
        
    lvd_list = set_data.get('LVD', {}).get('list', [])
    lvd1_row = None
    for row in lvd_list:
        name = row[0][0] if isinstance(row[0], list) else str(row[0])
        if name.strip() == "LVD 1":
            lvd1_row = row
            break
            
    print("Found LVD 1 row:", lvd1_row)
    equip_id = lvd1_row[1]
    signal_type = lvd1_row[2]
    signal_id = lvd1_row[3]
    value_type = lvd1_row[8]
    curr_val = lvd1_row[9]
    print(f"Current LVD 1 value: {curr_val}")
    
    # 3. Post control
    ctrl_url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_control.cgi?_={int(time.time()*1000)}"
    payload = f"control_value=1&equip_ID={equip_id}&signal_type={signal_type}&signal_id={signal_id}&value_type={value_type}&control_type=1&sessionId={session_id}"
    print(f"Payload: {payload}")
    
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    cookie_header += f"; user_name={u_b64}; user_password={p_b64}; language_type=0"
    ctrl_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f'http://{ip}/app/www_user/html/eng/index.html',
        'Cookie': cookie_header
    }
    
    req_ctrl = urllib.request.Request(ctrl_url, data=payload.encode('utf-8'), headers=ctrl_headers)
    with urllib.request.urlopen(req_ctrl, timeout=10) as resp:
        ctrl_body = resp.read().decode('utf-8-sig', errors='ignore').strip()
        print(f"Response: {ctrl_body}")
        
    time.sleep(2)
    req_verify = urllib.request.Request(setting_url, headers=headers)
    with urllib.request.urlopen(req_verify, timeout=8) as resp:
        verify_data = parse_device_data(resp.read())
    for row in verify_data.get('LVD', {}).get('list', []):
        name = row[0][0] if isinstance(row[0], list) else str(row[0])
        if name.strip() == "LVD 1":
            print(f"Verified LVD 1: {row[9]} (Expected: 1)")

if __name__ == '__main__':
    test_set_lvd()
