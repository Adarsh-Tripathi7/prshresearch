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

    # Find the premium-select-group that we created previously
    # We will replace them with custom-dropdown
    
    # Or, if we are starting from the clean state (if I revert again), we find segments.
    # Wait, the current state has <div class="premium-select-group">
    # Let's write regex to match either premium-select-group OR segments
    
    # Wait, I'm currently at the state where High/Low uses premium-select-group.
    pattern = re.compile(r'<div class="premium-select-group">\s*<label for="(segHlTarget|segClosePosTh|segHlSort)">([^<]+)</label>\s*<div class="select-wrapper">\s*<select id="\1">\s*(.*?)\s*</select>\s*</div>\s*</div>', re.DOTALL)
    
    def replace_dropdown(match):
        seg_id = match.group(1)
        label_text = match.group(2)
        options_html = match.group(3)
        
        # Parse options
        items = []
        active_val = ""
        active_text = ""
        
        opt_pattern = re.compile(r'<option\s+value="([^"]+)"(?:([^>]*)>|>)(.*?)</option>')
        for opt_match in opt_pattern.finditer(options_html):
            val = opt_match.group(1)
            attrs = opt_match.group(2) or ""
            text = opt_match.group(3)
            
            # fix unicode arrow that got mangled by powershell output earlier if any
            text = text.replace('ï¿½+"', '↓').replace('+"', '↓')
            
            is_active = 'selected' in attrs
            active_cls = ' active' if is_active else ''
            
            if is_active or not active_val:
                active_val = val
                active_text = text
                
            items.append(f'      <div class="cd-item{active_cls}" data-v="{val}">{text}</div>')
            
        items_str = '\n'.join(items)
        
        return f'''<div class="custom-dropdown" id="{seg_id}" data-v="{active_val}">
      <div class="cd-trigger">
        <span class="cd-label">{label_text}:</span>
        <span class="cd-val">{active_text}</span>
        <svg class="cd-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M7 10l5 5 5-5z"/></svg>
      </div>
      <div class="cd-menu">
{items_str}
      </div>
    </div>'''
            
    new_content = pattern.sub(replace_dropdown, content)
    
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

# Replace initSeg and segVal to support custom dropdowns
new_js = """function initSeg(id, cb) {
  const el = $(id); if (!el) return;
  
  if (el.classList.contains('custom-dropdown')) {
    // It's a custom dropdown
    const trigger = el.querySelector('.cd-trigger');
    const menu = el.querySelector('.cd-menu');
    const items = el.querySelectorAll('.cd-item');
    const valSpan = el.querySelector('.cd-val');
    
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      // Close all others
      document.querySelectorAll('.custom-dropdown').forEach(d => {
        if (d !== el) d.classList.remove('open');
      });
      el.classList.toggle('open');
    });
    
    items.forEach(item => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        items.forEach(x => x.classList.remove('active'));
        item.classList.add('active');
        el.dataset.v = item.dataset.v;
        valSpan.innerText = item.innerText;
        el.classList.remove('open');
        if (cb) cb(item.dataset.v);
      });
    });
    return;
  }

  // It's a standard segments button group
  el.querySelectorAll('button').forEach(b => {
    b.addEventListener('click', () => { el.querySelectorAll('button').forEach(x => x.classList.remove('active')); b.classList.add('active'); if (cb) cb(b.dataset.v); });
  });
}
function segVal(id) { 
  const el = $(id);
  if (!el) return '';
  if (el.classList.contains('custom-dropdown')) return el.dataset.v;
  const a = el.querySelector('button.active'); 
  return a ? a.dataset.v : ''; 
}
"""

old_seg_code_regex = r"function initSeg\(id, cb\) \{.*?\n  \}\n  function segVal\(id\) \{.*?\n  \}\n"
main_js = re.sub(old_seg_code_regex, new_js, main_js, flags=re.DOTALL)

# Add a global click listener to close dropdowns if clicking outside
# We can just append it if not already there
global_click = """
document.addEventListener('click', () => {
  document.querySelectorAll('.custom-dropdown').forEach(d => d.classList.remove('open'));
});
"""
if 'custom-dropdown' not in main_js:
    # Append after the new_js definition
    main_js = main_js.replace(new_js, new_js + global_click)

with open(main_js_path, 'w', encoding='utf-8') as f:
    f.write(main_js)

print("Updated main.js")

# Update CSS
css_path = r'd:\Antigravity\prshcapital\styles.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Remove old premium-select-group css if present
css = re.sub(r'/\* Premium Select Group \*/.*?(:root\[data-theme=\'light\'\] \.select-wrapper select option \{ background: #fff; color: #111; \})', '', css, flags=re.DOTALL)

new_css = """
/* Custom Dropdown (Top Website Style) */
.custom-dropdown { position: relative; display: inline-block; align-self: flex-start; margin-bottom: 8px; font-family: var(--font); }
.cd-trigger { display: flex; align-items: center; gap: 8px; background: rgba(20, 20, 25, 0.7); backdrop-filter: blur(8px); padding: 8px 12px 8px 16px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 2px 10px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.02); cursor: pointer; transition: all 0.2s var(--spring); }
.cd-trigger:hover { background: rgba(30, 30, 35, 0.9); border-color: rgba(255, 255, 255, 0.15); }
.custom-dropdown.open .cd-trigger { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent), 0 4px 15px rgba(0,0,0,0.3); background: rgba(30, 30, 35, 0.9); }
.cd-label { font-size: 11px; text-transform: uppercase; color: var(--text-3); font-weight: 600; letter-spacing: 0.5px; }
.cd-val { font-size: 13px; font-weight: 500; color: var(--text-1); }
.cd-icon { width: 16px; height: 16px; color: var(--text-2); transition: transform 0.2s var(--spring); }
.custom-dropdown.open .cd-icon { transform: rotate(180deg); color: var(--accent); }

.cd-menu { position: absolute; top: calc(100% + 6px); left: 0; min-width: 100%; background: #1a1a24; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,0,0,0.2); padding: 6px; z-index: 100; opacity: 0; visibility: hidden; transform: translateY(-10px); transition: all 0.2s var(--spring); white-space: nowrap; }
.custom-dropdown.open .cd-menu { opacity: 1; visibility: visible; transform: translateY(0); }
.cd-item { padding: 8px 12px; font-size: 13px; color: var(--text-2); font-weight: 500; border-radius: 6px; cursor: pointer; transition: all 0.15s; }
.cd-item:hover { background: rgba(255,255,255,0.05); color: var(--text-1); }
.cd-item.active { background: rgba(99, 102, 241, 0.15); color: var(--accent); }

:root[data-theme='light'] .cd-trigger { background: #ffffff; border-color: var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
:root[data-theme='light'] .cd-trigger:hover { background: #f8fafc; }
:root[data-theme='light'] .cd-menu { background: #ffffff; border-color: var(--border); box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
:root[data-theme='light'] .cd-item:hover { background: #f1f5f9; color: #000; }
:root[data-theme='light'] .cd-item.active { background: #e0e7ff; color: #4f46e5; }
"""

if '.custom-dropdown' not in css:
    css = css + new_css
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
    print("Updated styles.css")
