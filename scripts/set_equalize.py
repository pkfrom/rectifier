import urllib.request
import urllib.parse
import base64
import time
import json
import sys
from collect_rectifier_inventory import parse_device_data

sys.stdout.reconfigure(encoding='utf-8')

TARGET_STATIONS = [
    {"code": "AUG", "name": "ออเงิน", "ip": "10.209.30.21"},
    {"code": "KP", "name": "กิ่งเพชร", "ip": "10.209.8.21"},
    {"code": "RTR", "name": "รัตนราช", "ip": "10.209.51.21"},
    {"code": "SYI", "name": "สวนใหญ่", "ip": "10.209.186.21"},
]

def set_equalize_voltage(station, target_val=53.6):
    ip = station["ip"]
    code = station["code"]
    name = station["name"]
    print(f"\n==========================================")
    print(f"Configuring [{code}] {name} ({ip}) -> Target Equalize: {target_val} V")
    
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
    
    try:
        req = urllib.request.Request(login_url, data=post_data, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode('utf-8-sig', errors='ignore').strip()
            login_res = json.loads(body)
    except Exception as e:
        print(f"[{code}] Login error: {e}")
        return False, str(e)
    
    if login_res.get('status') != 1:
        print(f"[{code}] Login failed! Response: {body}")
        return False, f"Login failed status {login_res.get('status')}"
    
    # Parse cookie string
    cookie_str = login_res.get('cookie', '')
    cookies = {}
    for item in cookie_str.split(','):
        if '=' in item:
            k, v = item.split('=', 1)
            cookies[k.strip()] = v.strip()
    
    session_id = cookies.get('sessionId')
    print(f"[{code}] Logged in. sessionId: {session_id}, Authority: {cookies.get('nAuthority')}")
    
    # 2. Get current setting params from data.setting.html
    setting_url = f"http://{ip}/var/datas/data.setting.html?_={int(time.time()*1000)}"
    try:
        req_set = urllib.request.Request(setting_url, headers=headers)
        with urllib.request.urlopen(req_set, timeout=8) as resp:
            set_data = parse_device_data(resp.read())
    except Exception as e:
        print(f"[{code}] Error fetching data.setting.html: {e}")
        return False, str(e)
    
    charge_list = set_data.get('CHARGE', {}).get('list', [])
    eq_row = None
    for row in charge_list:
        row_name = row[0][0] if isinstance(row[0], list) else str(row[0])
        if "Equalize Charge Voltage" in row_name:
            eq_row = row
            break
            
    if not eq_row:
        print(f"[{code}] Could not find Equalize Charge Voltage row!")
        return False, "Equalize row not found"
        
    equip_id = eq_row[1]
    signal_type = eq_row[2]
    signal_id = eq_row[3]
    value_type = eq_row[8]
    curr_val = eq_row[9]
    print(f"[{code}] Current Setting: {curr_val} V (equip_ID={equip_id}, sig_type={signal_type}, sig_id={signal_id})")
    
    if str(curr_val) == str(target_val) or float(curr_val) == float(target_val):
        print(f"[{code}] Already set to {target_val} V!")
        return True, f"Already {target_val} V"
    
    # 3. Build POST request to web_cgi_control.cgi
    ctrl_url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_control.cgi?_={int(time.time()*1000)}"
    payload = f"control_value={target_val:.1f}&equip_ID={equip_id}&signal_type={signal_type}&signal_id={signal_id}&value_type={value_type}&control_type=1&sessionId={session_id}"
    print(f"[{code}] Sending control payload: {payload}")
    
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    cookie_header += f"; user_name={u_b64}; user_password={p_b64}; language_type=0"
    
    ctrl_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f'http://{ip}/app/www_user/html/eng/index.html',
        'Cookie': cookie_header
    }
    
    try:
        req_ctrl = urllib.request.Request(ctrl_url, data=payload.encode('utf-8'), headers=ctrl_headers)
        with urllib.request.urlopen(req_ctrl, timeout=10) as resp:
            ctrl_body = resp.read().decode('utf-8-sig', errors='ignore').strip()
            print(f"[{code}] Control response: {ctrl_body}")
    except Exception as e:
        print(f"[{code}] Control request error: {e}")
        return False, str(e)
    
    # 4. Wait 2 seconds and verify
    time.sleep(2)
    try:
        req_verify = urllib.request.Request(setting_url, headers=headers)
        with urllib.request.urlopen(req_verify, timeout=8) as resp:
            verify_data = parse_device_data(resp.read())
    except Exception as e:
        print(f"[{code}] Verification fetch error: {e}")
        return False, str(e)
    
    v_list = verify_data.get('CHARGE', {}).get('list', [])
    for row in v_list:
        row_name = row[0][0] if isinstance(row[0], list) else str(row[0])
        if "Equalize Charge Voltage" in row_name:
            new_val = row[9]
            print(f"[{code}] VERIFIED NEW VALUE: {new_val} V")
            if str(new_val) == str(target_val) or float(new_val) == float(target_val):
                print(f"[{code}] SUCCESS! Setting applied.")
                return True, f"Success ({curr_val}V -> {new_val}V)"
            else:
                print(f"[{code}] Mismatch: expected {target_val}, got {new_val}")
                return False, f"Mismatch ({new_val})"
    return False, "Not verified"

if __name__ == '__main__':
    results = {}
    for st in TARGET_STATIONS:
        ok, msg = set_equalize_voltage(st, 53.6)
        results[st['code']] = (ok, msg)
        time.sleep(1)
        
    print("\n==========================================")
    print("FINAL SUMMARY:")
    for code, (ok, msg) in results.items():
        status_txt = "OK" if ok else "FAIL"
        print(f"  [{code}] -> {status_txt}: {msg}")
