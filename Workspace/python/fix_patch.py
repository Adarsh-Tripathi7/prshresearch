import os
import glob

dashboard_dir = r"d:\Antigravity\Dashboard"
html_files = glob.glob(os.path.join(dashboard_dir, "*.html"))

def fix_content(content):
    # My previous buggy replacement:
    old_buggy = "onclick=\"window.sortCol=\\''+p+'\\';window.sortAsc=!window.sortAsc;updateExt()\">${p}`+(window.sortCol===p?(window.sortAsc?'▲':'▼'):'')+'</th>');th+='</tr>';"
    
    # What it should be:
    # Use `${p}` inside the template literal for the onclick handler, and also evaluate the chevron inside the template literal!
    new_fixed = "onclick=\"window.sortCol=\\'${p}\\';window.sortAsc=!window.sortAsc;updateExt()\">${p}${window.sortCol===p?(window.sortAsc?'▲':'▼'):''}</th>`);th+='</tr>';"
    
    return content.replace(old_buggy, new_fixed)

for file_path in html_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = fix_content(content)
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed {file_path}")

exp_path = r"d:\Antigravity\Workspace\python\ib_interactive_dashboard_experiment.py"
with open(exp_path, "r", encoding="utf-8") as f:
    exp_content = f.read()

new_exp_content = fix_content(exp_content)
if new_exp_content != exp_content:
    with open(exp_path, "w", encoding="utf-8") as f:
        f.write(new_exp_content)
    print("Fixed ib_interactive_dashboard_experiment.py")
