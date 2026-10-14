with open('all.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
print("All .cgi in all.js:")
for m in set(re.findall(r'[^"\'\s\(\)]+\.cgi[^"\'\s\(\)]*', text)):
    print(" ", m)

print("\nAll $.ajax or $.post calls in all.js:")
for m in re.finditer(r'\$\.(?:ajax|post)\s*\(\s*\{([^}]+)\}', text):
    snippet = m.group(1)
    if "url" in snippet:
        # extract url line
        urls = re.findall(r'url\s*:\s*([^,\n]+)', snippet)
        datas = re.findall(r'data\s*:\s*([^,\n]+)', snippet)
        print(f"  URL: {urls} | Data: {datas}")
