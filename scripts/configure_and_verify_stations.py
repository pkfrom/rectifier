import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import urllib.parse
import base64
import time
import json
from collect_rectifier_inventory import parse_device_data

TARGET_STATIONS = [
    {"code": "KRT", "name": "คลองรังสิต", "ip": "10.209.182.21"},
    {"code": "SYI", "name": "สวนใหญ่", "ip": "10.209.186.21"},
    {"code": "BTD", "name": "เขตบางขุนเทียน", "ip": "10.209.254.20"},
    {"code": "AUG", "name": "ออเงิน", "ip": "10.209.30.21"},
    {"code": "RTR", "name": "รัตนราช", "ip": "10.209.51.21"},
    {"code": "KP", "name": "กิ่งเพชร", "ip": "10.209.8.21"},
]

DESIRED_SETTINGS = {
    "LVD": {
        "LVD 1": 1,                      # Enabled (1)
        "LVD 1 Voltage": 43.2,           # 43.2 V
        "LVD 1 Reconnect Voltage": 49.0, # 49.0 V
        "LVD 2": 1,                      # Enabled (1)
        "LVD 2 Voltage": 43.2,           # 43.2 V
        "LVD 2 Reconnect Voltage": 49.0, # 49.0 V
        "LVD Contactor Type": 1,         # Mono-Stable (1)
    },
    "CHARGE": {
        "Under Voltage 1": 48.0,         # 48.0 V
        "Under Voltage 2": 46.0,         # 46.0 V
        "Comp Temp High1": 50,           # 50 C
        "Comp Temp High2": 50,           # 50 C
    },
    "BATT_TEST": {
        "End Test Capacity": 70.0,       # 70.0 %
        "Test Voltage Level": 45.0,      # 45.0 V
        "End Test Voltage": 45.2,        # 45.2 V
        "End Test Time": 30,             # 30 min
    },
    "RECT": {
        "Walk-In": 1,                    # Enabled (1)
        "Walk-In Time": 8,               # 8 s
        "Rectifier Trim": 53.2,          # 53.2 V
    },
    "TEMPERATURE": {
        "System Temp 1": 1,              # Ambient (1)
        "System Temp 2": 2,              # Battery (2)
        "Ambient Temp Sensor": 3,        # System Temp1 (3)
        "Temp Compensation Probe Number": 5, # System Temp2 (5)
        "Comp Temp High1": 50,           # 50 C
        "Comp Temp High2": 50,           # 50 C
    }
}

def login(ip: str):
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
        res = json.loads(resp.read().decode('utf-8-sig', errors='ignore').strip())
    if res.get('status') != 1:
        raise RuntimeError(f"Login failed: status={res.get('status')}")
    cookies = {k.strip(): v.strip() for item in res['cookie'].split(',') if '=' in item for k, v in [item.split('=', 1)]}
    return cookies, u_b64, p_b64

def fetch_settings(ip: str):
    setting_url = f"http://{ip}/var/datas/data.setting.html?_={int(time.time()*1000)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(setting_url, headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        return parse_device_data(resp.read())

def set_parameter(ip: str, cookies: dict, u_b64: str, p_b64: str, row: list, target_val: any):
    equip_id = row[1]
    signal_type = row[2]
    signal_id = row[3]
    value_type = row[8]
    session_id = cookies.get('sessionId')

    if isinstance(target_val, float):
        val_str = f"{target_val:.1f}"
    else:
        val_str = str(target_val)

    payload = f"control_value={val_str}&equip_ID={equip_id}&signal_type={signal_type}&signal_id={signal_id}&value_type={value_type}&control_type=1&sessionId={session_id}"
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()]) + f"; user_name={u_b64}; user_password={p_b64}; language_type=0"
    ctrl_headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f'http://{ip}/app/www_user/html/eng/index.html',
        'Cookie': cookie_header
    }
    ctrl_url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_control.cgi?_={int(time.time()*1000)}"
    req = urllib.request.Request(ctrl_url, data=payload.encode('utf-8'), headers=ctrl_headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode('utf-8-sig', errors='ignore').strip()
        res = json.loads(body)
        return res.get('status') == 1, body

def process_station(station: dict):
    code = station["code"]
    name = station["name"]
    ip = station["ip"]
    print(f"\n=======================================================")
    print(f"[*] Processing [{code}] {name} ({ip})")
    print(f"=======================================================")

    try:
        cookies, u_b64, p_b64 = login(ip)
        print(f"  [+] Logged in successfully. SessionId={cookies.get('sessionId')}")
    except Exception as e:
        print(f"  [-] Login error: {e}")
        return {"code": code, "status": "LOGIN_FAIL", "error": str(e), "changes": []}

    try:
        data_before = fetch_settings(ip)
    except Exception as e:
        print(f"  [-] Fetch settings before failed: {e}")
        return {"code": code, "status": "FETCH_FAIL", "error": str(e), "changes": []}

    changes_attempted = []
    
    for sec_name, params in DESIRED_SETTINGS.items():
        sec_obj = data_before.get(sec_name, {})
        rows = { (r[0][0] if isinstance(r[0], list) else str(r[0])).strip(): r for r in sec_obj.get('list', []) if isinstance(r, list) and len(r) >= 10 }
        
        for param_name, target_val in params.items():
            row = rows.get(param_name)
            if not row:
                continue
            curr_val = row[9]
            
            # Check if match
            is_match = False
            try:
                if float(curr_val) == float(target_val):
                    is_match = True
            except:
                if str(curr_val) == str(target_val):
                    is_match = True
                    
            if not is_match:
                print(f"  --> Changing [{sec_name}] {param_name}: {curr_val} -> {target_val}")
                try:
                    ok, resp = set_parameter(ip, cookies, u_b64, p_b64, row, target_val)
                    changes_attempted.append({
                        "section": sec_name,
                        "param": param_name,
                        "before": curr_val,
                        "target": target_val,
                        "unit": row[10] if len(row) > 10 else "",
                        "ok": ok,
                        "resp": resp
                    })
                    time.sleep(0.3)
                except Exception as ex:
                    print(f"      [!] Failed to set {param_name}: {ex}")
                    changes_attempted.append({
                        "section": sec_name,
                        "param": param_name,
                        "before": curr_val,
                        "target": target_val,
                        "unit": row[10] if len(row) > 10 else "",
                        "ok": False,
                        "resp": str(ex)
                    })

    if not changes_attempted:
        print(f"  [i] All parameters are ALREADY matching standard! No changes needed.")
        return {"code": code, "status": "ALREADY_STD", "changes": []}

    print(f"  [*] Waiting 4 seconds for controller to persist settings...")
    time.sleep(4)

    try:
        data_after = fetch_settings(ip)
    except Exception as e:
        print(f"  [-] Fetch settings after failed: {e}")
        return {"code": code, "status": "VERIFY_FETCH_FAIL", "changes": changes_attempted}

    verified_changes = []
    all_ok = True
    for ch in changes_attempted:
        sec_name = ch["section"]
        param_name = ch["param"]
        target_val = ch["target"]
        sec_obj = data_after.get(sec_name, {})
        rows = { (r[0][0] if isinstance(r[0], list) else str(r[0])).strip(): r for r in sec_obj.get('list', []) if isinstance(r, list) and len(r) >= 10 }
        r_after = rows.get(param_name)
        after_val = r_after[9] if r_after else None
        
        is_verified = False
        try:
            if float(after_val) == float(target_val):
                is_verified = True
        except:
            if str(after_val) == str(target_val):
                is_verified = True
                
        status_str = "OK" if is_verified else "MISMATCH"
        if not is_verified:
            all_ok = False
        print(f"  [VERIFY] {param_name:30s} | Before: {str(ch['before']):8s} | Expected: {str(target_val):8s} | After: {str(after_val):8s} | Result: {status_str}")
        ch["after"] = after_val
        ch["verified"] = is_verified
        verified_changes.append(ch)

    return {
        "code": code,
        "name": name,
        "ip": ip,
        "status": "SUCCESS" if all_ok else "PARTIAL",
        "changes": verified_changes
    }

def main():
    overall = []
    for st in TARGET_STATIONS:
        res = process_station(st)
        overall.append(res)
        time.sleep(1)

    print("\n" + "="*80)
    print("FINAL SUMMARY REPORT FOR 6 STATIONS")
    print("="*80)
    for r in overall:
        print(f"[{r.get('code')}] {r.get('name', '')} ({r.get('ip', '')}): Status={r.get('status')}")
        for c in r.get('changes', []):
            mark = "✓" if c.get('verified') else "✗"
            print(f"    {mark} [{c['section']}] {c['param']}: {c['before']} -> {c['after']} (Target: {c['target']})")
    
if __name__ == '__main__':
    main()
