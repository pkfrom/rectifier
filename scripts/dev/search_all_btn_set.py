import glob
import re

for path in glob.glob("*.js") + glob.glob("*.html"):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    matches = list(re.finditer(r'btn_set', content))
    if matches:
        print(f"\n=== File: {path} ({len(matches)} matches) ===")
        for m in matches[:5]:
            pos = m.start()
            print(content[max(0, pos-80):min(len(content), pos+200)])
            print("-" * 40)
