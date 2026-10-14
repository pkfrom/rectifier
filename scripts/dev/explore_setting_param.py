import tarfile
import struct
import urllib.request
import json
import base64
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# 1. Parse SettingParam.run records
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

def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MEA-Rectifier-Inventory/1.0", "Cache-Control": "no-cache"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return parse_device_data(res.read())
    except Exception as e:
        print(f'Error fetching {url}: {e}')
        return {}




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


lookup = {}

def walk_json(prefix, obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk_json(f'{prefix}.{k}' if prefix else k, v)
    elif isinstance(obj, list):
        if obj and isinstance(obj[0], list):
            for row in obj:
                # check if row is parameter format: [name, equip_ID, sig_type, sig_id, ...]
                if len(row) >= 10 and isinstance(row[1], int) and isinstance(row[2], int) and isinstance(row[3], int):
                    name = row[0][0] if isinstance(row[0], list) else str(row[0])
                    eq = row[1]
                    st = row[2]
                    si = row[3]
                    vt = row[8] if len(row) > 8 else None
                    cval = row[9] if len(row) > 9 else None
                    opts = row[10] if len(row) > 10 else None
                    lookup[(eq, st, si)] = {
                        'path': prefix,
                        'name': name,
                        'value_type': vt,
                        'live_val': cval,
                        'opts': opts,
                        'raw': row
                    }

for ep in endpoints:
    d = get_json(f'http://10.209.1.21/{ep}')
    if d:
        walk_json(ep, d)

print(f'Total parameters found across live endpoints: {len(lookup)}')

matched = 0
results = []
for r in records:
    key = (r['equip'], r['sig_type'], r['sig_id'])
    if key in lookup:
        matched += 1
        info = lookup[key]
        val_display = r['val_float'] if info['value_type'] == 2 else r['val_int']
        results.append({
            'matched': True,
            'equip': r['equip'],
            'sig_type': r['sig_type'],
            'sig_id': r['sig_id'],
            'name': info['name'],
            'path': info['path'],
            'value_type': info['value_type'],
            'run_val': val_display,
            'live_val': info['live_val'],
            'opts': info['opts'],
            'ts': r['ts']
        })
        print(f"MATCH: [{r['equip']}:{r['sig_type']}:{r['sig_id']}] {info['path']} -> {info['name']} | Run: {val_display} | Live: {info['live_val']}")
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
        print(f"UNMATCHED: [{r['equip']}:{r['sig_type']}:{r['sig_id']}] val_int={r['val_int']} float={r['val_float']:.2f}")

print(f'\nTotal: {len(records)}, Matched: {matched}, Unmatched: {len(records) - matched}')
