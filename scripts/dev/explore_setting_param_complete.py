import tarfile
import struct
import urllib.request
import json
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Parse SettingParam.run
with tarfile.open('config/SettingParam.tar') as t:
    data = t.extractfile('./config/run/SettingParam.run').read()

offset = 24
records = []
while offset + 16 <= len(data):
    equip, sig_id, sig_type, val_int, ts = struct.unpack_from('<IHHiI', data, offset)
    val_float, = struct.unpack_from('<f', data, offset + 8)
    if equip > 1000 or sig_type not in (1, 2, 3, 4, 5):
        break
    records.append({
        'offset': offset,
        'equip': equip,
        'sig_type': sig_type,
        'sig_id': sig_id,
        'val_int': val_int,
        'val_float': val_float,
        'ts': ts
    })
    offset += 16

print(f'Total records in SettingParam.run: {len(records)}')

from collect_rectifier_inventory import parse_device_data

lookup = {}

def walk_tree(prefix, node):
    if isinstance(node, dict):
        for k, v in node.items():
            walk_tree(f"{prefix}.{k}" if prefix else k, v)
    elif isinstance(node, list):
        # check if it's a list of rows
        for item in node:
            if isinstance(item, list) and len(item) >= 10 and isinstance(item[1], int) and isinstance(item[2], int) and isinstance(item[3], int):
                name = item[0][0] if isinstance(item[0], list) else str(item[0])
                eq, st, si = item[1], item[2], item[3]
                vt = item[8]
                cval = item[9]
                opts = item[10] if len(item) > 10 else None
                lookup[(eq, st, si)] = {
                    'path': prefix,
                    'name': name,
                    'value_type': vt,
                    'live_val': cval,
                    'opts': opts
                }
            elif isinstance(item, dict):
                walk_tree(prefix, item)

endpoints = [
    '/var/datas/data.setting.html',
    '/var/datas/data.sys_setting.html',
    '/var/datas/data.udef_setting.html',
    '/var/datas/data.install_wizard.html',
    '/var/datas/data.system_rectifier.html',
    '/var/datas/data.system_battery.html',
    '/var/datas/data.system_dc.html',
    '/var/datas/data.system_ac.html',
    '/var/datas/data.hybrid.html',
    '/var/datas/data.system_inventory.html',
]

for ep in endpoints:
    url = f'http://10.209.1.21{ep}'
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MEA-Rectifier/1.0"})
        d = parse_device_data(urllib.request.urlopen(req, timeout=5).read())
        walk_tree(ep, d)
    except Exception as e:
        print(f'Error fetching {ep}: {e}')

print(f'Total signals indexed in lookup: {len(lookup)}')

matched = 0
results = []
for r in records:
    key = (r['equip'], r['sig_type'], r['sig_id'])
    if key in lookup:
        matched += 1
        info = lookup[key]
        val_display = round(r['val_float'], 2) if info['value_type'] == 2 else r['val_int']
        opt_str = ""
        if info['value_type'] == 5 and isinstance(info['opts'], list):
            try:
                idx = int(r['val_int'])
                if 0 <= idx < len(info['opts']):
                    o = info['opts'][idx]
                    opt_str = f" ({o[0] if isinstance(o, list) else o})"
            except:
                pass
        results.append({
            'matched': True,
            'equip': r['equip'],
            'sig_type': r['sig_type'],
            'sig_id': r['sig_id'],
            'name': info['name'],
            'path': info['path'],
            'value_type': info['value_type'],
            'run_val': f"{val_display}{opt_str}",
            'live_val': info['live_val'],
            'ts': r['ts']
        })
        print(f"MATCH [{r['equip']}:{r['sig_type']}:{r['sig_id']}] {info['name']} -> Run: {val_display}{opt_str} | Live: {info['live_val']} ({info['path']})")
    else:
        results.append({
            'matched': False,
            'equip': r['equip'],
            'sig_type': r['sig_type'],
            'sig_id': r['sig_id'],
            'val_int': r['val_int'],
            'val_float': r['val_float'],
            'ts': r['ts']
        })
        print(f"UNMATCHED [{r['equip']}:{r['sig_type']}:{r['sig_id']}] val_int={r['val_int']} float={r['val_float']:.2f}")

print(f"\nFinal: {matched}/{len(records)} matched!")
