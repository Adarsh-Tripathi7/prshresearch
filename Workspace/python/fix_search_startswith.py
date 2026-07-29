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
        for f in glob.glob(os.path.join(d, ext)):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                
                # Replace .includes(q) with .startsWith(q) in the search listener
                new_content = re.sub(
                    r"const matchWin = probData\.find\(d => d\.Window\.toLowerCase\(\)\.replace\(/:/g, ''\)\.includes\(q\)\);",
                    r"const matchWin = probData.find(d => d.Window.toLowerCase().replace(/:/g, '').startsWith(q));",
                    content
                )
                
                if new_content != content:
                    with open(f, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    print(f"Updated {f}")
            except Exception as e:
                print(f"Error processing {f}: {e}")

print("Done replacing includes with startsWith in search listener.")
