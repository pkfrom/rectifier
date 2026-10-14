import urllib.request

url = 'http://10.209.30.21/var/datas/data.setting.html'
resp = urllib.request.urlopen(url, timeout=5)
text = resp.read().decode('utf-8', errors='ignore')
idx = text.find('CHARGE')
print('Index:', idx)
if idx != -1:
    snippet = text[idx:idx+1500]
    # safe print without encoding issues
    print(snippet.encode('ascii', errors='replace').decode('ascii'))
