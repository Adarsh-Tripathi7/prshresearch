import os
import glob
import re

dashboard_dir = r"d:\Antigravity\Dashboard"
html_files = glob.glob(os.path.join(dashboard_dir, "*.html"))

def patch_content(content):
    # 1. Fix chartBar bottom margin from 32 to 56
    content = content.replace("grid:{top:10,right:12,bottom:32,left:48}", "grid:{top:10,right:12,bottom:60,left:48}")
    
    # 2. Add sorting logic to Javascript
    # The original table code:
    old_th = "let th='<tr><th>Window</th>';PCT.forEach(p=>th+=`<th class=\"r\">${p}</th>`);th+='</tr>';"
    new_th = "let th='<tr><th style=\"cursor:pointer;user-select:none\" onclick=\"window.sortCol=\\\'Window\\\';window.sortAsc=!window.sortAsc;updateExt()\">Window'+(window.sortCol==='Window'?(window.sortAsc?'▲':'▼'):'')+'</th>';PCT.forEach(p=>th+=`<th class=\"r\" style=\"cursor:pointer;user-select:none\" onclick=\"window.sortCol=\\''+p+'\\';window.sortAsc=!window.sortAsc;updateExt()\">${p}`+(window.sortCol===p?(window.sortAsc?'▲':'▼'):'')+'</th>');th+='</tr>';"
    
    content = content.replace(old_th, new_th)
    
    # The original array copy in updateExt:
    # const d=extData();
    # if(!d.length)return;
    old_d = "const d=extData();\n  if(!d.length)return;"
    new_d = """let d=[...extData()];
  if(!d.length)return;
  if(window.sortCol) {
    d.sort((a,b)=>{
      let va=a[window.sortCol], vb=b[window.sortCol];
      if(window.sortCol==='Window') return window.sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      return window.sortAsc ? va-vb : vb-va;
    });
  }"""
    content = content.replace(old_d, new_d)

    return content

for file_path in html_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = patch_content(content)
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Patched {file_path}")
    else:
        print(f"No changes for {file_path} (maybe already patched or format differs)")

exp_path = r"d:\Antigravity\Workspace\python\ib_interactive_dashboard_experiment.py"
with open(exp_path, "r", encoding="utf-8") as f:
    exp_content = f.read()

new_exp_content = patch_content(exp_content)
if new_exp_content != exp_content:
    with open(exp_path, "w", encoding="utf-8") as f:
        f.write(new_exp_content)
    print("Patched ib_interactive_dashboard_experiment.py")
else:
    print("No changes for ib_interactive_dashboard_experiment.py")
