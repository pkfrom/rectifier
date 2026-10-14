import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import urllib.parse
import base64
import time
import json
from collect_rectifier_inventory import parse_device_data

STATIONS = [
    {"code": "CG", "name": "ฉลองกรุง", "ip": "10.209.39.21"},
    {"code": "LNB", "name": "ลานนาบุญ", "ip": "10.209.188.151"},
]

TARGET_SETTINGS = {
    "Under Voltage 1": 48.0,
    "Under Voltage 2": 46.0,
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

def fetch_uv(ip: str):
    url = f"http://{ip}/var/datas/data.setting.html?_={int(time.time()*1000)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as resp:
        d = parse_device_data(resp.read())
    charge_list = d.get('CHARGE', {}).get('list', [])
    res = {}
    for row in charge_list:
        p_name = row[0][0] if isinstance(row[0], list) else str(row[0])
        if p_name in TARGET_SETTINGS:
            res[p_name] = {
                'row': row,
                'val': row[9]
            }
    return res

def set_param(ip: str, cookies: dict, u_b64: str, p_b64: str, row: list, target_val: float):
    equip_id = row[1]
    signal_type = row[2]
    signal_id = row[3]
    value_type = row[8]
    session_id = cookies.get('sessionId')

    val_str = f"{target_val:.1f}"
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

def main():
    print("=== Under Voltage Configuration for CG & LNB ===")
    for st in STATIONS:
        code = st['code']
        name = st['name']
        ip = st['ip']
        print(f"\n[*] Processing [{code}] {name} ({ip})...")

        # 1. Check before
        before = fetch_uv(ip)
        print("  Current settings:")
        for k, v in before.items():
            print(f"    {k}: {v['val']} V")

        # 2. Login
        cookies, u_b64, p_b64 = login(ip)
        print(f"  Login OK, sessionId={cookies.get('sessionId')}")

        # 3. Apply changes
        for param_name, target_v in TARGET_SETTINGS.items():
            if param_name not in before:
                print(f"  [!] {param_name} not found in CHARGE list")
                continue
            curr_v = float(before[param_name]['val'])
            if curr_v == target_v:
                print(f"  [-] {param_name} is already {target_v:.1f} V. No change needed.")
                continue

            row = before[param_name]['row']
            print(f"  [>] Changing {param_name}: {curr_v:.1f} V -> {target_v:.1f} V...")
            ok, body = set_param(ip, cookies, u_b64, p_b64, row, target_v)
            if ok:
                print(f"    [+] API responded OK: {body}")
            else:
                print(f"    [-] API error: {body}")
            time.sleep(1.5)

    # Wait for controller commit
    print("\nWaiting 4 seconds for controllers to commit changes...")
    time.sleep(4)

    # 4. Verification
    print("\n=== VERIFICATION RESULTS ===")
    all_ok = True
    for st in STATIONS:
        code = st['code']
        name = st['name']
        ip = st['ip']
        after = fetch_uv(ip)
        print(f"\n[*] [{code}] {name} ({ip}):")
        for param_name, target_v in TARGET_SETTINGS.items():
            actual_v = float(after.get(param_name, {}).get('val', -999))
            if actual_v == target_v:
                print(f"  [PASS] {param_name}: {actual_v:.1f} V == {target_v:.1f} V")
            else:
                print(f"  [FAIL] {param_name}: {actual_v:.1f} V != {target_v:.1f} V")
                all_ok = False

    if all_ok:
        print("\n>>> ALL STATIONS CONFIGURED AND VERIFIED 100% SUCCESSFUL! <<<")
    else:
        print("\n>>> SOME PARAMETERS FAILED VERIFICATION <<<")

if __name__ == '__main__':
    main()
