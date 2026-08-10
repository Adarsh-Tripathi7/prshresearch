import os
import glob
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    labels = {
        'segHlTarget': 'Sequence',
        'segClosePosTh': 'Close',
        'segHlSort': 'Sort By'
    }

    # Only target the High/Low segments: segHlTarget, segClosePosTh, segHlSort
    pattern = re.compile(r'<div class="segments-scroll"[^>]*><div class="segments"\s+id="(segHlTarget|segClosePosTh|segHlSort)">\s*(.*?)\s*</div></div>', re.DOTALL)
    
    def replace_segment(match):
        seg_id = match.group(1)
        buttons_html = match.group(2)
        
        label_text = labels.get(seg_id, 'Filter')
        
        options_html = []
        button_pattern = re.compile(r'<button([^>]*)data-v="([^"]*)"[^>]*>(.*?)</button>')
        for btn_match in button_pattern.finditer(buttons_html):
            attrs = btn_match.group(1)
            val = btn_match.group(2)
            text = btn_match.group(3)
            selected = ' selected' if 'active' in attrs else ''
            options_html.append(f'              <option value="{val}"{selected}>{text}</option>')
            
        options_str = '\n'.join(options_html)
        
        return f'''<div class="premium-select-group">
              <label for="{seg_id}">{label_text}</label>
              <div class="select-wrapper">
                <select id="{seg_id}">
{options_str}
                </select>
              </div>
            </div>'''
            
    new_content = pattern.sub(replace_segment, content)
    
    # We also need to group these premium-select-groups so they appear inline nicely.
    # The original HTML had them as siblings inside .card-header.
    # We will just let them sit there; CSS flex will handle it since they are inline-flex.
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

# Update HTML files in prshcapital
html_files = glob.glob(r'd:\Antigravity\prshcapital\*.html')
for f in html_files:
    process_file(f)

# Update build scripts
process_file(r'd:\Antigravity\Workspace\python\build_mobile_dashboard.py')
process_file(r'd:\Antigravity\prshcapital\dashboard.html')

print("Done updating HTML.")

# Update main.js
main_js_path = r'd:\Antigravity\prshcapital\main.js'
with open(main_js_path, 'r', encoding='utf-8') as f:
    main_js = f.read()

# Fix grids
def replace_grid(match):
    full_str = match.group(0)
    if 'containLabel' not in full_str:
        return full_str.replace('}', ', containLabel: true }')
    return full_str

main_js = re.sub(r'grid:\s*\{\s*top:\s*\d+,\s*right:\s*\d+,\s*bottom:\s*\d+,\s*left:\s*\d+\s*\}', replace_grid, main_js)

# Fix initSeg and segVal
new_initSeg = """function initSeg(id, cb) {
  const el = $(id); if (!el) return;
  if (el.tagName && el.tagName.toLowerCase() === 'select') {
    el.addEventListener('change', (e) => { if (cb) cb(e.target.value); });
    return;
  }
  el.querySelectorAll('button').forEach(b => {
    b.addEventListener('click', () => { el.querySelectorAll('button').forEach(x => x.classList.remove('active')); b.classList.add('active'); if (cb) cb(b.dataset.v); });
  });
}
function segVal(id) { 
  const el = $(id);
  if (!el) return '';
  if (el.tagName && el.tagName.toLowerCase() === 'select') return el.value;
  const a = el.querySelector('button.active'); 
  return a ? a.dataset.v : ''; 
}"""

old_seg_code_regex = r"function initSeg\(id, cb\) \{.*?\n  \}\n  function segVal\(id\) \{ const a = \$\(id\)\?\.querySelector\('button\.active'\); return a \? a\.dataset\.v : ''; \}\n"
main_js = re.sub(old_seg_code_regex, new_initSeg + "\n", main_js, flags=re.DOTALL)

with open(main_js_path, 'w', encoding='utf-8') as f:
    f.write(main_js)

print("Updated main.js")

# Update CSS
css_path = r'd:\Antigravity\prshcapital\styles.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

new_css = """
/* Premium Select Group */
.premium-select-group {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(20, 20, 25, 0.6);
  padding: 6px 8px 6px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.02);
  margin-bottom: 4px;
}
.premium-select-group label {
  font-size: 11px;
  text-transform: uppercase;
  color: var(--text-3);
  letter-spacing: 0.5px;
  font-weight: 600;
  margin: 0;
}
.select-wrapper {
  position: relative;
  display: inline-block;
}
.select-wrapper select {
  appearance: none;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-1);
  font-family: var(--font);
  font-size: 13px;
  font-weight: 500;
  padding: 8px 36px 8px 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  cursor: pointer;
  outline: none;
  transition: all 0.2s ease;
}
.select-wrapper select:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}
.select-wrapper select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(99,102,241,0.2);
}
.select-wrapper::after {
  content: '';
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 10px;
  height: 6px;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%228%22%3E%3Cpath%20fill%3D%22%23a1a1aa%22%20d%3D%22M1.41%200L6%204.58L10.59%200L12%201.41L6%207.41L0%201.41L1.41%200Z%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  pointer-events: none;
}
.select-wrapper select option {
  background: var(--bg-surface);
  color: var(--text-1);
}
:root[data-theme='light'] .premium-select-group { background: #ffffff; border-color: var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
:root[data-theme='light'] .select-wrapper select { background: #f4f4f5; border-color: #e4e4e7; color: #111; }
:root[data-theme='light'] .select-wrapper select:hover { background: #e4e4e7; }
:root[data-theme='light'] .select-wrapper select option { background: #fff; color: #111; }
"""

if '.premium-select-group' not in css:
    css = css + new_css
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
    print("Updated styles.css")
