import urllib.request
import sys
from collect_rectifier_inventory import parse_device_data

sys.stdout.reconfigure(encoding='utf-8')

endpoints = [
    '/var/datas/data.setting.html',
    '/var/datas/data.sys_setting.html',
    '/var/datas/data.udef_setting.html',
    '/var/datas/data.install_wizard.html',
    '/var/datas/data.cabinet_map.html',
    '/var/datas/data.consumption_map.html',
    '/var/datas/data.system_inventory.html',
    '/var/datas/data.system_rectifier.html',
    '/var/datas/data.system_battery.html',
    '/var/datas/data.system_dc.html',
    '/var/datas/data.system_ac.html',
    '/var/datas/data.hybrid.html',
    '/var/datas/data.alarms.html',
]

all_params = []
for ep in endpoints:
    try:
        url = f'http://10.209.1.21{ep}'
        data = parse_device_data(urllib.request.urlopen(url, timeout=5).read())
        
        def walk(prefix, obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(f'{prefix}.{k}' if prefix else k, v)
            elif isinstance(obj, list):
                if obj and isinstance(obj[0], list):
                    for row in obj:
                        if len(row) >= 10 and isinstance(row[1], int) and isinstance(row[2], int) and isinstance(row[3], int):
                            name = row[0][0] if isinstance(row[0], list) else str(row[0])
                            all_params.append({
                                'endpoint': ep,
                                'path': prefix,
                                'name': name,
                                'equip_id': row[1],
                                'sig_type': row[2],
                                'sig_id': row[3],
                                'val_type': row[8] if len(row) > 8 else None,
                                'value': row[9] if len(row) > 9 else None,
                                'options': row[10] if len(row) > 10 else None
                            })
        walk('', data)
    except Exception as e:
        print(f'{ep}: {e}')

print(f'Total extractable setting parameters from live device: {len(all_params)}')
sections = {}
for p in all_params:
    sections.setdefault(p['path'], []).append(p)

for sec, params in sorted(sections.items()):
    print(f'=== {sec} ({len(params)} params) ===')
    for p in params:
        opt_str = ""
        if p['val_type'] == 5 and isinstance(p['options'], list):
            try:
                idx = int(p['value'])
                if 0 <= idx < len(p['options']):
                    opt = p['options'][idx]
                    opt_str = f" ({opt[0] if isinstance(opt, list) else opt})"
            except:
                pass
        print(f"  [{p['equip_id']}:{p['sig_type']}:{p['sig_id']}] {p['name']} = {p['value']}{opt_str}")
