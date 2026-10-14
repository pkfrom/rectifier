import sys
sys.stdout.reconfigure(encoding='utf-8')
from collect_rectifier_inventory import get_json

ip_std = '10.209.1.21'
std_data = get_json(ip_std, '/var/datas/data.setting.html', 5.0)

target_ips = {
    'KRT': '10.209.182.21',
    'SYI': '10.209.186.21',
    'BTD': '10.209.254.20',
    'AUG': '10.209.30.21',
    'RTR': '10.209.51.21',
    'KP': '10.209.8.21'
}

for code, ip in target_ips.items():
    t_data = get_json(ip, '/var/datas/data.setting.html', 5.0)
    print(f"\n=======================================================")
    print(f"DIFFERENCES FOR [{code}] ({ip}) vs STD ({ip_std})")
    print(f"=======================================================")
    diff_count = 0
    for sec_name, sec_obj in std_data.items():
        if not isinstance(sec_obj, dict):
            continue
        t_sec = t_data.get(sec_name, {})
        std_list = { (row[0][0] if isinstance(row[0], list) else str(row[0])).strip(): row for row in sec_obj.get('list', []) if isinstance(row, list) and len(row) >= 10 }
        t_list = { (row[0][0] if isinstance(row[0], list) else str(row[0])).strip(): row for row in t_sec.get('list', []) if isinstance(row, list) and len(row) >= 10 }
        
        for param, std_row in std_list.items():
            t_row = t_list.get(param)
            if not t_row:
                continue
            std_val = std_row[9]
            t_val = t_row[9]
            if str(std_val) != str(t_val):
                unit = std_row[10] if len(std_row) > 10 else ""
                val_type = std_row[8]
                print(f"  [{sec_name}] {param:30s} | val_type={val_type} | STD={str(std_val):10s} | {code}={str(t_val):10s} | unit={unit}")
                diff_count += 1
    if diff_count == 0:
        print("  NO DIFFERENCES FOUND!")
