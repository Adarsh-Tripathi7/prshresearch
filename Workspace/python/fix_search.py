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
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Skip if we already did the replace
            if ".replace(/:/g, '')" in content:
                continue
                
            new_content = content.replace(
                "const q = this.value.trim().toLowerCase();",
                "const q = this.value.trim().toLowerCase().replace(/:/g, '');"
            ).replace(
                "const q=this.value.trim().toLowerCase();",
                "const q=this.value.trim().toLowerCase().replace(/:/g, '');"
            ).replace(
                "td.textContent.toLowerCase().includes(q)",
                "td.textContent.toLowerCase().replace(/:/g, '').includes(q)"
            ).replace(
                "d.Window.toLowerCase().includes(q)",
                "d.Window.toLowerCase().replace(/:/g, '').includes(q)"
            )
            
            if new_content != content:
                print(f"Updated {fpath}")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
