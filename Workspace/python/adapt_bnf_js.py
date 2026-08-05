import os
import re

dir_path = r"d:\Antigravity\banknifty_dashboard"
main_js = os.path.join(dir_path, "main.js")

with open(main_js, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Global asset
js = js.replace("let globalAsset = localStorage.getItem('prsh_global_asset') || 'both';", "let globalAsset = 'bnf';")
js = js.replace("const assets = globalAsset === 'both' ? ['nq', 'es'] : [globalAsset];", "const assets = ['bnf'];")

# 2. Variable renames for safety
js = js.replace("d.NQ_DB_Prob", "d.BNF_DB_Prob")
js = js.replace("d.ES_DB_Prob", "d.BNF_DB_Prob")
js = js.replace("pf.NQ_", "pf.BNF_")
js = js.replace("pf.ES_", "pf.BNF_")

# 3. Chart Series filtering.
js = re.sub(r"const seriesProb = \[\];.*?ec\('chartProb'\)\.setOption", "const seriesProb = [{ name: 'BNF', type: 'line', data: nq, smooth: 0.3, symbolSize: 6, itemStyle: { color: '#6366f1' }, lineStyle: { width: 3 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0, color:'rgba(99,102,241,0.2)'},{offset:1, color:'rgba(99,102,241,0)'}]) } }];\n    ec('chartProb').setOption", js, flags=re.DOTALL)

js = re.sub(r"const seriesExt = \[\];.*?ec\('chartMedExt'\)\.setOption", "const seriesExt = [{ name: 'BNF', type: 'bar', data: nqExt, itemStyle: { color: '#10b981', borderRadius: [4,4,0,0] }, barMaxWidth: 16 }];\n    ec('chartMedExt').setOption", js, flags=re.DOTALL)

js = re.sub(r"const seriesHl = \[\];.*?ec\('chartHlFirst'\)\.setOption", "const seriesHl = [{ name: 'BNF', type: 'line', data: nqHl, smooth: 0.3, symbolSize: 6, itemStyle: { color: '#6366f1' }, lineStyle: { width: 3 } }];\n    ec('chartHlFirst').setOption", js, flags=re.DOTALL)

js = re.sub(r"const seriesProbFull = \[\];.*?ec\('chartProbFull'\)\.setOption", "const seriesProbFull = [{ name: 'BNF DB %', type: 'line', data: nq, smooth: 0.25, symbolSize: 4, itemStyle: { color: '#6366f1' }, lineStyle: { width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0, color:'rgba(99,102,241,0.1)'},{offset:1, color:'rgba(99,102,241,0)'}]) } }, { name: '50%', type: 'line', data: labels.map(()=>50), lineStyle: { width: 1, color: '#3f3f46', type: 'dashed' }, symbol: 'none', silent: true }];\n    ec('chartProbFull').setOption", js, flags=re.DOTALL)

# Heatmap
js = js.replace("['NQ', 'ES']", "['BNF']")
js = js.replace("['NQ','ES']", "['BNF']")

# Tables
js = re.sub(r"return \{ Window: d\.Window, nq: n, es: e, avg: n&&e\?\(n\+e\)/2:0, delta: n&&e\?\(n-e\):0 \};", "return { Window: d.Window, nq: n, es: e, avg: n, delta: 0 };", js)
js = js.replace("`<td class=\"r\">${d.nq.toFixed(1)}</td><td class=\"r\">${d.es.toFixed(1)}</td><td class=\"r\">${d.avg.toFixed(1)}</td><td class=\"r\">${d.delta>0?'+':''}${d.delta.toFixed(1)}</td>`", "`<td class=\"r\">${(d.nq || 0).toFixed(1)}</td>`")

js = js.replace("const valNQ = d.BNF_H_First_L_Break_Prob;", "const valNQ = d.BNF_H_First_L_Break_Prob; const valES = d.BNF_L_First_H_Break_Prob;")
js = js.replace("const valES = d.BNF_H_First_L_Break_Prob;", "/* handled */")
js = js.replace("const valClose = d.BNF_Comb_Cond_Prob;", "const valClose = d.BNF_L_First_H_Break_Prob;")
js = js.replace("`<td class=\"r\">${d.nqOpp.toFixed(1)}</td><td class=\"r\">${d.esOpp.toFixed(1)}</td><td class=\"r\">${d.closeOpp.toFixed(1)}</td><td class=\"r\">${d.avg.toFixed(1)}</td><td class=\"r\">${d.delta>0?'+':''}${d.delta.toFixed(1)}</td>`", "`<td class=\"r\">${(d.nqOpp || 0).toFixed(1)}</td><td class=\"r\">${(d.closeOpp || 0).toFixed(1)}</td>`")

with open(main_js, 'w', encoding='utf-8') as f:
    f.write(js)
