import os
import re

dir_path = r"d:\Antigravity\banknifty_dashboard"

# 1. Adapt index.html
with open(os.path.join(dir_path, "index.html"), "r", encoding="utf-8") as f:
    idx_content = f.read()

idx_content = idx_content.replace("Prsh Capital | Research Hub", "Bank Nifty Dashboard")
idx_content = idx_content.replace("Advanced quantitative analysis, probability models, and market extension matrices for NQ and ES futures.", "Advanced quantitative analysis, probability models, and market extension matrices for Bank Nifty.")
idx_content = idx_content.replace("NQ, ES", "Bank Nifty")
idx_content = idx_content.replace("NQ and ES", "Bank Nifty")

# Remove heatmap card
idx_content = re.sub(r'<a href="dashboard\.html\?tf=[^"]+" class="nav-card">.*?<div class="nav-title">Cross-Asset Heatmap</div>.*?</a>', '', idx_content, flags=re.DOTALL)

with open(os.path.join(dir_path, "index.html"), "w", encoding="utf-8") as f:
    f.write(idx_content)


# 2. Adapt dashboard.html
with open(os.path.join(dir_path, "dashboard.html"), "r", encoding="utf-8") as f:
    dash_content = f.read()

dash_content = dash_content.replace("Prsh Capital | 60M", "Bank Nifty Dashboard")
dash_content = dash_content.replace("NQ and ES", "Bank Nifty")
dash_content = dash_content.replace("NQ, ES", "Bank Nifty")

dash_content = dash_content.replace('<button class="asset-badge" id="btnGlobalAsset">NQ | ES</button>', '<button class="asset-badge" id="btnGlobalAsset">BANK NIFTY</button>')

# Headers
dash_content = dash_content.replace('<th class="r">NQ %</th><th class="r">ES %</th><th class="r">Avg</th><th class="r">Δ</th>', '<th class="r">BNF %</th>')
dash_content = dash_content.replace('<th class="r">Opposite Break NQ %</th><th class="r">Opposite Break ES %</th><th class="r">Opp Break (Close) %</th><th class="r">Avg</th><th class="r">Δ</th>', '<th class="r">BNF H-First L-Break %</th><th class="r">BNF L-First H-Break %</th>')

dash_content = dash_content.replace('Median Extension (NQ)', 'Median Extension (BNF)')

# Remove leader lagger buttons
dash_content = re.sub(r'<button data-v="corr">Leader/Lagger</button>', '', dash_content)

with open(os.path.join(dir_path, "dashboard.html"), "w", encoding="utf-8") as f:
    f.write(dash_content)


# 3. Adapt main.js
with open(os.path.join(dir_path, "main.js"), "r", encoding="utf-8") as f:
    js = f.read()

# Replace globalAsset logic
js = js.replace("let globalAsset = localStorage.getItem('prsh_global_asset') || 'both';", "let globalAsset = 'bnf';")
js = js.replace("const assets = globalAsset === 'both' ? ['nq', 'es'] : [globalAsset];", "const assets = ['bnf'];")

# Replace probabilities logic
js = js.replace("d.NQ_DB_Prob", "d.BNF_DB_Prob")
js = js.replace("d.ES_DB_Prob", "d.BNF_DB_Prob")
js = js.replace("pf.NQ_", "pf.BNF_")
js = js.replace("pf.ES_", "pf.BNF_")

# Remove dual lines logic from charts
js = re.sub(r"seriesProb\.push\(\{ name: 'NQ'.*?\}\);", "seriesProb.push({ name: 'BNF', type: 'line', data: nq, smooth: 0.3, symbolSize: 6, itemStyle: { color: '#6366f1' }, lineStyle: { width: 3 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0, color:'rgba(99,102,241,0.2)'},{offset:1, color:'rgba(99,102,241,0)'}]) } });", js)
js = re.sub(r"if \(globalAsset === 'both' \|\| globalAsset === 'es'\).*?seriesProb\.push\(\{ name: 'ES'.*?\}\);", "", js, flags=re.DOTALL)

# Same for chartMedExt (remove ES)
js = re.sub(r"if \(globalAsset === 'both' \|\| globalAsset === 'es'\) \{.*?seriesExt\.push\(\{ name: 'ES'.*?\}\);.*?\}", "", js, flags=re.DOTALL)
js = js.replace("name: 'NQ'", "name: 'BNF'")

# And in chartHlFirst
js = re.sub(r"if \(globalAsset === 'both' \|\| globalAsset === 'es'\) \{.*?seriesHl\.push\(\{ name: 'ES'.*?\}\);.*?\}", "", js, flags=re.DOTALL)

# For table Prob
js = re.sub(r"const e = d\.ES_DB_Prob;", "const e = d.BNF_DB_Prob;", js) # Just so it doesn't crash
js = re.sub(r"return \{ Window: d\.Window, nq: n, es: e, avg: n&&e\?\(n\+e\)/2:0, delta: n&&e\?\(n-e\):0 \};", "return { Window: d.Window, nq: n, es: e, avg: n, delta: 0 };", js)
js = js.replace("`<td class=\"r\">${d.nq.toFixed(1)}</td><td class=\"r\">${d.es.toFixed(1)}</td><td class=\"r\">${d.avg.toFixed(1)}</td><td class=\"r\">${d.delta>0?'+':''}${d.delta.toFixed(1)}</td>`", "`<td class=\"r\">${d.nq.toFixed(1)}</td>`")

# For tblHlFirst
js = js.replace("`<td class=\"r\">${d.nqOpp.toFixed(1)}</td><td class=\"r\">${d.esOpp.toFixed(1)}</td><td class=\"r\">${d.closeOpp.toFixed(1)}</td><td class=\"r\">${d.avg.toFixed(1)}</td><td class=\"r\">${d.delta>0?'+':''}${d.delta.toFixed(1)}</td>`", "`<td class=\"r\">${d.nqOpp.toFixed(1)}</td><td class=\"r\">${d.closeOpp.toFixed(1)}</td>`")
js = js.replace("const valNQ = d.NQ_H_First_L_Break_Prob;", "const valNQ = d.BNF_H_First_L_Break_Prob; const valES = d.BNF_L_First_H_Break_Prob;")
js = js.replace("const valES = d.ES_H_First_L_Break_Prob;", "")
js = js.replace("const valClose = d.NQ_Comb_Cond_Prob;", "const valClose = d.BNF_L_First_H_Break_Prob;")
js = js.replace("let valNQ, valES, valClose;", "let valNQ, valES, valClose;")

# For chartProbFull
js = re.sub(r"if \(globalAsset === 'both' \|\| globalAsset === 'es'\) \{.*?seriesProbFull\.push\(\{ name: 'ES'.*?\}\);.*?\}", "", js, flags=re.DOTALL)

with open(os.path.join(dir_path, "main.js"), "w", encoding="utf-8") as f:
    f.write(js)

print("UI adapted successfully.")
