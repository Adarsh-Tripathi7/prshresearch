import os

filepath = r"D:\Antigravity\Workspace\python\ib_interactive_dashboard_experiment.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update segType
old_segType = """      <div class="seg-group" id="segType">
        <button class="active" data-v="prob">DB Probability</button>
        <button data-v="ext_db">DB Extension</button>
        <button data-v="ext_sb">SB Extension</button>
        <button data-v="ext_ab">All Breaks Ext</button>
        <button data-v="corr">Directional Corr</button>
      </div>"""

new_segType = """      <div class="seg-group" id="segType">
        <button class="active" data-v="ext_ab">All Breaks Ext</button>
        <button data-v="corr">Directional Corr</button>
      </div>"""

content = content.replace(old_segType, new_segType)

# 2. Update segHmType
old_segHmType = """      <div class="seg-group" id="segHmType">
        <button class="active" data-v="prob">DB Probability</button>
        <button data-v="ext_db">DB Extension</button>
        <button data-v="ext_sb">SB Extension</button>
        <button data-v="ext_ab">All Breaks Ext</button>
        <button data-v="corr">First Side Same Break Prob</button>
      </div>"""

new_segHmType = """      <div class="seg-group" id="segHmType">
        <button class="active" data-v="ext_ab">All Breaks Ext</button>
        <button data-v="corr">First Side Same Break Prob</button>
      </div>"""

content = content.replace(old_segHmType, new_segHmType)

# 3. Update initSeg defaults
# In JS, let type='prob', asset='nq', dir='combined';
old_js_vars = "let type='prob', asset='nq', dir='combined';"
new_js_vars = "let type='ext_ab', asset='nq', dir='combined';"
content = content.replace(old_js_vars, new_js_vars)

# Write back
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("ib_interactive_dashboard_experiment.py patched successfully.")
