import os
import glob
import re

dashboard_dir = r"d:\Antigravity\Dashboard"
html_files = glob.glob(os.path.join(dashboard_dir, "*.html"))

def patch_content(content):
    # 1. Prob heatmap
    pattern_prob = r"(c\.setOption\(\{[\s\n]*tooltip:\{\.\.\.TT,formatter:p=>`<b style=\"color:#ececef\">\$\{probData\[p\.value\[1\]\]\.Window\}</b><br>\$\{\[\'NQ\',\'ES\'\]\[p\.value\[0\]\]\}: <b>\$\{p\.value\[2\]\}%</b>`\},)"
    replacement_prob = r"document.getElementById('chartHeatmap').style.height = Math.max(620, windows.length * 22 + 100) + 'px';\n    c.resize();\n    \1"
    
    # 2. Corr heatmap
    pattern_corr = r"(c\.setOption\(\{[\s\n]*tooltip:\{\.\.\.TT,formatter:p=>`<b style=\"color:#ececef\">\$\{windows\[p\.value\[1\]\]\}</b><br>\$\{cols\[p\.value\[0\]\]\.label\}: <b>\$\{p\.value\[2\]\}%</b>`\},)"
    
    # 3. Ext heatmap
    pattern_ext = r"(c\.setOption\(\{[\s\n]*tooltip:\{\.\.\.TT,formatter:p=>`<b style=\"color:#ececef\">\$\{windows\[p\.value\[1\]\]\}</b> · \$\{PCT\[p\.value\[0\]\]\}<br>Extension: <b>\$\{p\.value\[2\]\}R</b>`\},)"

    content = re.sub(pattern_prob, replacement_prob, content)
    content = re.sub(pattern_corr, replacement_prob, content)
    content = re.sub(pattern_ext, replacement_prob, content)
    
    # Optional: also decrease the font size slightly or hide labels if it's too squished? 
    content = content.replace("fontSize:11,color:'#ececef',formatter:p=>p.value[2]+'%'}", "fontSize:10,color:'#ececef',formatter:p=>p.value[2]+'%'}")
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
        print(f"No changes for {file_path}")

# Also patch the experiment python script so future generations are fixed
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
