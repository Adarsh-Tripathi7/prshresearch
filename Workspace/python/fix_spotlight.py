import os
import glob
import re

directories = [
    r"d:\Antigravity\Workspace\python",
    r"d:\Antigravity\Results",
    r"d:\Antigravity\Dashboard",
    r"d:\Antigravity\imobile ib dashboard"
]

NEW_FUNC = """function showSpotlight(win) {
  $('spotTitle').innerHTML = `Window: ${win}`;
  const p = probData.find(d => d.Window === win);
  const pf = (typeof _D !== 'undefined' && _D.prob_first) ? _D.prob_first.find(d => d.Window === win) : null;
  const currentView = document.querySelector('.page.active')?.id || 'page-overview';
  let html = '';
  
  const showProb = currentView === 'page-overview' || currentView === 'page-probability';
  const showExt = currentView === 'page-overview' || currentView === 'page-extensions';

  if (showProb && p) {
    html += `<div class="spot-card"><div class="spot-card-title">Double Break % (Combined)</div><div class="spot-row"><span class="lbl">NQ</span><span class="val c-dn">${p.NQ_DB_Prob.toFixed(1)}%</span></div><div class="spot-row"><span class="lbl">ES</span><span class="val c-dn">${p.ES_DB_Prob.toFixed(1)}%</span></div></div>`;
    if (currentView === 'page-probability' && pf) {
        html += `<div class="spot-card"><div class="spot-card-title">Double Break % (High First)</div><div class="spot-row"><span class="lbl">NQ</span><span class="val c-dn">${pf.NQ_H_First_DB_Prob?.toFixed(1) || '—'}%</span></div><div class="spot-row"><span class="lbl">ES</span><span class="val c-dn">${pf.ES_H_First_DB_Prob?.toFixed(1) || '—'}%</span></div></div>`;
        html += `<div class="spot-card"><div class="spot-card-title">Double Break % (Low First)</div><div class="spot-row"><span class="lbl">NQ</span><span class="val c-dn">${pf.NQ_L_First_DB_Prob?.toFixed(1) || '—'}%</span></div><div class="spot-row"><span class="lbl">ES</span><span class="val c-dn">${pf.ES_L_First_DB_Prob?.toFixed(1) || '—'}%</span></div></div>`;
    }
  }

  if (showExt) {
    for (const asset of ['nq','es']) {
      for (const brk of ['double_break','single_break']) {
        const d = EXT[asset]?.[brk]?.combined; if (!d) continue;
        const row = d.find(r => r.Window === win); if (!row) continue;
        const lbl = `${asset.toUpperCase()} ${brk==='double_break'?'DB':'SB'}`;
        
        if (currentView === 'page-overview') {
          html += `<div class="spot-card"><div class="spot-card-title">${lbl} (Combined)</div><div class="spot-row"><span class="lbl">Median</span><span class="val" style="color:var(--warm)">${row['50%']?.toFixed(2)||'—'}R</span></div><div class="spot-row"><span class="lbl">90th pctl</span><span class="val" style="color:var(--accent)">${row['90%']?.toFixed(2)||'—'}R</span></div></div>`;
        } else if (currentView === 'page-extensions') {
          html += `<div class="spot-card"><div class="spot-card-title">${lbl} (Combined)</div>`;
          html += `<div class="spot-row"><span class="lbl">25th pctl</span><span class="val" style="color:var(--text-1)">${row['25%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">Median</span><span class="val" style="color:var(--warm)">${row['50%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">75th pctl</span><span class="val" style="color:var(--up)">${row['75%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">90th pctl</span><span class="val" style="color:var(--accent)">${row['90%']?.toFixed(2)||'—'}R</span></div>`;
          html += `</div>`;
        }
      }
    }
  }
  
  $('spotGrid').innerHTML = html;
}"""

# regex to find the old function
pattern = re.compile(r'function showSpotlight\(win\) \{.*?\$\(\'spotGrid\'\)\.innerHTML = html;\n\}', re.DOTALL)

for d in directories:
    for ext in ["*.py", "*.html"]:
        for fpath in glob.glob(os.path.join(d, "**", ext), recursive=True):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if it already has the new code (e.g. page.active)
                if "const currentView = document.querySelector('.page.active')?.id || 'page-overview';" in content:
                    continue
                    
                new_content = pattern.sub(NEW_FUNC, content)
                
                if new_content != content:
                    print(f"Updated {fpath}")
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(new_content)
            except Exception as e:
                print(f"Error processing {fpath}: {e}")
