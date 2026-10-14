import glob, re, os

for fn in ['all.js', 'control.js', 'page.js']:
    if os.path.exists(fn):
        with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            matches = set(re.findall(r'/var/datas/[a-zA-Z0-9_\.]+', content))
            print(f'{fn}:')
            for m in sorted(matches):
                print(f'   {m}')
