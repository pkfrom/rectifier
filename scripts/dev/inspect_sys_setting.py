import urllib.request
import sys
from collect_rectifier_inventory import parse_device_data

sys.stdout.reconfigure(encoding='utf-8')

for ip, name in [('10.209.254.20', 'BTD'), ('10.209.30.21', 'AUG')]:
    url = f'http://{ip}/var/datas/data.sys_setting.html'
    data = parse_device_data(urllib.request.urlopen(url, timeout=3).read())
    ps = data.get('PowerSystem', {})
    print(f"\n=================== {name} ===================")
    for target in ['SYSTEM_GROUP', 'DC_UNIT', 'DCMETER_UNIT', 'EIB_UNIT', 'SMDU_UNIT']:
        if target in ps:
            print(f"--- {target} ---")
            lst = ps[target]
            if isinstance(lst, list):
                for row in lst:
                    if isinstance(row, list) and len(row) > 9:
                        r_name = row[0][0] if isinstance(row[0], list) else str(row[0])
                        val = row[9]
                        unit = row[10] if len(row) > 10 else ''
                        print(f"  {r_name}: {val} {unit}")
