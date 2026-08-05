import re

main_js = r"d:\Antigravity\banknifty_dashboard\main.js"

with open(main_js, 'r', encoding='utf-8') as f:
    js = f.read()

# Fix updateProb series building
js = re.sub(
    r"const series = \[\];.*?ec\('chartProbFull'\)\.setOption",
    r"const series = [{ name: 'BNF DB %', type: 'line', data: nqVals, smooth: 0.25, symbolSize: 4, itemStyle: { color: '#6366f1' }, lineStyle: { width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0, color:\\'rgba(99,102,241,0.1)\\'},{offset:1, color:\\'rgba(99,102,241,0)\\'}]) } }, { name: '50%', type: 'line', data: labels.map(()=>50), lineStyle: { width: 1, color: '#3f3f46', type: 'dashed' }, symbol: 'none', silent: true }];\n    ec('chartProbFull').setOption",
    js, flags=re.DOTALL
)

# Fix updateHlFirst series building
js = re.sub(
    r"const series = \[\];.*?if \(globalAsset === 'both' \|\| globalAsset === 'es'\) series\.push\(.*?\}\);",
    r"const series = [{ name: 'BNF', type: 'line', data: nqVals, smooth: 0.3, symbolSize: 6, lineStyle: { width: 3, color: '#10b981' }, itemStyle: { color: '#10b981' } }];",
    js, flags=re.DOTALL
)

# Fix updateHeatmap data extraction loop
heatmap_data_loop = r'''      windows.forEach\(\(w, yi\) => \{
        let rNq, rEs;
        if \(globalAsset === 'both' \|\| globalAsset === 'nq'\) rNq = EXT\['bnf'\]\?\.\[btype\]\?\.\[dir\]\?\.find\(x => x\.Window === w\);
        if \(globalAsset === 'both' \|\| globalAsset === 'es'\) rEs = EXT\['bnf'\]\?\.\[btype\]\?\.\[dir\]\?\.find\(x => x\.Window === w\);
        
        PCT\.forEach\(\(p, xi\) => \{
          let v;
          if \(globalAsset === 'both'\) \{
            const vNq = rNq \? rNq\[p\] : 0;
            const vEs = rEs \? rEs\[p\] : 0;
            v = \(typeof vNq === 'number' && typeof vEs === 'number'\) \? \(vNq \+ vEs\) / 2 : 0;
          \} else if \(globalAsset === 'nq'\) \{
            v = rNq \? rNq\[p\] : 0;
          \} else \{
            v = rEs \? rEs\[p\] : 0;
          \}
          if \(p !== '100%' && v > maxV\) maxV = v;
          data\.push\(\[xi, yi, typeof v === 'number' \? \+v\.toFixed\(2\) : 0\]\);
        \}\);
      \}\);'''

replacement_loop = r'''      windows.forEach((w, yi) => {
        let rBnf = EXT['bnf']?.[btype]?.[dir]?.find(x => x.Window === w);
        PCT.forEach((p, xi) => {
          let v = rBnf ? rBnf[p] : 0;
          if (p !== '100%' && v > maxV) maxV = v;
          data.push([xi, yi, typeof v === 'number' ? +v.toFixed(2) : 0]);
        });
      });'''

js = re.sub(heatmap_data_loop, replacement_loop, js)

with open(main_js, 'w', encoding='utf-8') as f:
    f.write(js)

print("Charts fixed!")
