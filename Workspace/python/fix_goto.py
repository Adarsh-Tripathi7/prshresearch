import os
import glob
import re

directories = [
    r"d:\Antigravity\Workspace\python",
    r"d:\Antigravity\Results",
    r"d:\Antigravity\Dashboard",
    r"d:\Antigravity\imobile ib dashboard"
]

for d in directories:
    for ext in ["*.py", "*.html"]:
        for fpath in glob.glob(os.path.join(d, "**", ext), recursive=True):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if it already has the new code
                if "if ($('spotlight') && $('spotlight').classList.contains('open')) { $('search').dispatchEvent(new Event('input')); }" in content:
                    continue
                
                # Replace the end of goTo function
                pattern = re.compile(r'(if \(pg\) \{ pg\.classList\.add\(\'active\'\); setTimeout\(resizeAll, 50\); \})')
                
                new_content = pattern.sub(r'\1\n  if ($(\'spotlight\') && $(\'spotlight\').classList.contains(\'open\')) { $(\'search\').dispatchEvent(new Event(\'input\')); }', content)
                
                if new_content != content:
                    print(f"Updated {fpath}")
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(new_content)
            except Exception as e:
                pass
