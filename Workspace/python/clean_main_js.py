import re

main_js = r"d:\Antigravity\banknifty_dashboard\main.js"

with open(main_js, 'r', encoding='utf-8') as f:
    js = f.read()

# H/L First table headers
js = js.replace("'Opp Break NQ %'", "'Opp Break BNF %'")
js = js.replace("'Cond Opp Break NQ %'", "'Cond Opp Break BNF %'")

# Extensions table NQ/ES removal
ext_table_old = r"""      // Both NQ and ES rows
      const nqRow = extData\('nq'\)\.find\(x => x\.Window === r\.Window\);
      const esRow = extData\('es'\)\.find\(x => x\.Window === r\.Window\);
      
      if \(nqRow\) \{
        tb \+= `<tr\$\{cls\} data-i="\$\{i\}"><td class="c-mono">\$\{r\.Window\}</td><td class="c-mono" style="color:#6366f1">NQ</td>`;
        PCT\.forEach\(p => \{ const v = nqRow\[p\]; tb \+= `<td class="r c-mono" style="background:\$\{typeof v==='number' \? cellBg\(v\) : 'transparent'\}">\$\{typeof v==='number' \? v\.toFixed\(2\) : v\}</td>`; \}\);
        tb \+= '</tr>';
      \}
      if \(esRow\) \{
        tb \+= `<tr\$\{cls\} data-i="\$\{i\}"><td class="c-mono">\$\{r\.Window\}</td><td class="c-mono" style="color:#38bdf8">ES</td>`;
        PCT\.forEach\(p => \{ const v = esRow\[p\]; tb \+= `<td class="r c-mono" style="background:\$\{typeof v==='number' \? cellBg\(v\) : 'transparent'\}">\$\{typeof v==='number' \? v\.toFixed\(2\) : v\}</td>`; \}\);
        tb \+= '</tr>';
      \}"""

ext_table_new = r"""      const bnfRow = extData('bnf').find(x => x.Window === r.Window);
      if (bnfRow) {
        tb += `<tr${cls} data-i="${i}"><td class="c-mono">${r.Window}</td><td class="c-mono" style="color:#10b981">BNF</td>`;
        PCT.forEach(p => { const v = bnfRow[p]; tb += `<td class="r c-mono" style="background:${typeof v==='number' ? cellBg(v) : 'transparent'}">${typeof v==='number' ? v.toFixed(2) : v}</td>`; });
        tb += '</tr>';
      }"""

js = re.sub(ext_table_old, ext_table_new, js)

with open(main_js, 'w', encoding='utf-8') as f:
    f.write(js)
print("done")
