import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import base64
import time
import json
from collect_rectifier_inventory import parse_device_data
from configure_and_verify_stations import login, fetch_settings, set_parameter

TARGET_STATIONS = [
    {"code": "KRT", "name": "คลองรังสิต", "ip": "10.209.182.21"},
    {"code": "SYI", "name": "สวนใหญ่", "ip": "10.209.186.21"},
    {"code": "BTD", "name": "เขตบางขุนเทียน", "ip": "10.209.254.20"},
    {"code": "AUG", "name": "ออเงิน", "ip": "10.209.30.21"},
    {"code": "RTR", "name": "รัตนราช", "ip": "10.209.51.21"},
    {"code": "KP", "name": "กิ่งเพชร", "ip": "10.209.8.21"},
]

EXTRA_SETTINGS = {
    "TEMPERATURE": {
        "Ambient Temp High1": 38,
        "Ambient Temp Low": 15,
    },
    "BATT_TEST": {
        "Number of Planned Tests per Year": 12,
    },
    "RECT": {
        "HVSD": 0,
        "Sequence Start Interval": 0,
    },
    "CHARGE": {
        "Calculate Battery Current": 0,
    }
}

for st in TARGET_STATIONS:
    ip = st["ip"]
    code = st["code"]
    print(f"Applying final settings for [{code}] ({ip})...")
    try:
        cookies, u_b64, p_b64 = login(ip)
        data = fetch_settings(ip)
        for sec_name, params in EXTRA_SETTINGS.items():
            sec_obj = data.get(sec_name, {})
            rows = { (r[0][0] if isinstance(r[0], list) else str(r[0])).strip(): r for r in sec_obj.get('list', []) if isinstance(r, list) and len(r) >= 10 }
            for p_name, t_val in params.items():
                row = rows.get(p_name)
                if not row: continue
                curr_val = row[9]
                if str(curr_val) != str(t_val):
                    print(f"  Setting [{sec_name}] {p_name}: {curr_val} -> {t_val}")
                    set_parameter(ip, cookies, u_b64, p_b64, row, t_val)
                    time.sleep(0.3)
    except Exception as e:
        print(f"Error {code}: {e}")

print("Done applying extra settings.")
