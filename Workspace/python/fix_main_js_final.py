import re

main_js = r"d:\Antigravity\banknifty_dashboard\main.js"

with open(main_js, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Fix updateProb and updateHlFirst visibility
js = re.sub(r"const showNq = globalAsset === 'both' \|\| globalAsset === 'nq';\s*const showEs = globalAsset === 'both' \|\| globalAsset === 'es';\s*const showAvg = globalAsset === 'both';",
            r"const showNq = true;\n  const showEs = false;\n  const showAvg = false;", js)

# 2. Fix NQ % to BNF % headers
js = js.replace("'NQ %'", "'BNF %'")

# 3. Fix updateHlFirst data mapping
mapping_old = r"""      if \(dir === 'high_first'\) \{
          n = d\.NQ_H_First_L_Break_Prob;
          e = d\.ES_H_First_L_Break_Prob;
          n_cond = d\.NQ_H_First_CBM_Prob;
          e_cond = d\.ES_H_First_CBM_Prob;
      \} else if \(dir === 'low_first'\) \{
          n = d\.NQ_L_First_H_Break_Prob;
          e = d\.ES_L_First_H_Break_Prob;
          n_cond = d\.NQ_L_First_CAM_Prob;
          e_cond = d\.ES_L_First_CAM_Prob;
      \} else \{
          n = d\.NQ_Comb_Opp_Prob;
          e = d\.ES_Comb_Opp_Prob;
          n_cond = d\.NQ_Comb_Cond_Prob;
          e_cond = d\.ES_Comb_Cond_Prob;
      \}"""

mapping_new = r"""      if (dir === 'high_first') {
          n = d.BNF_H_First_L_Break_Prob;
          e = n;
          n_cond = d.BNF_H_First_CBM_Prob;
          e_cond = n_cond;
      } else if (dir === 'low_first') {
          n = d.BNF_L_First_H_Break_Prob;
          e = n;
          n_cond = d.BNF_L_First_CAM_Prob;
          e_cond = n_cond;
      } else {
          n = d.BNF_Comb_Opp_Prob;
          e = n;
          n_cond = d.BNF_Comb_Cond_Prob;
          e_cond = n_cond;
      }"""

js = re.sub(mapping_old, mapping_new, js)

# 4. Fix updateHeatmap
heatmap_old = r"""    windows\.forEach\(\(w, yi\) => \{
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
    \}\);"""

heatmap_new = r"""    windows.forEach((w, yi) => {
      let rBnf = EXT['bnf']?.[btype]?.[dir]?.find(x => x.Window === w);
      PCT.forEach((p, xi) => {
        let v = rBnf ? rBnf[p] : 0;
        if (p !== '100%' && v > maxV) maxV = v;
        data.push([xi, yi, typeof v === 'number' ? +v.toFixed(2) : 0]);
      });
    });"""

js = re.sub(heatmap_old, heatmap_new, js)

# Also fix the probability heatmap sorting and mapping
prob_heatmap_old = r"""      if \(globalAsset === 'both'\) \{
        const lblNQ = 'NQ' \+ sortIndic\('NQ'\);
        const lblES = 'ES' \+ sortIndic\('ES'\);
        sortedProb\.forEach\(\(d, yi\) => \{ data\.push\(\[0, yi, \+d\.BNF_DB_Prob\.toFixed\(1\)\]\); data\.push\(\[1, yi, \+d\.BNF_DB_Prob\.toFixed\(1\)\]\); \}\);
        c\.setOption\(\{
          tooltip: TT, xAxis: \{ type: 'category', data: \[lblNQ, lblES\], position: 'top', axisLine: \{ show: false \}, axisTick: \{ show: false \}, axisLabel: \{ color: '#a1a1aa', fontSize: 13, fontWeight: 'bold' \}, triggerEvent: true \},
          yAxis: \{ type: 'category', data: windows, inverse: true, axisLine: \{ show: false \}, axisTick: \{ show: false \}, axisLabel: \{ color: '#71717a', fontSize: 10, fontFamily: 'IBM Plex Mono' \} \},
          grid: \{ top: 30, right: 10, bottom: 10, left: 85 \},
          visualMap: \{ show: false, min: 20, max: 80, inRange: \{ color: \['#2e1065', '#4c1d95', '#5b21b6', '#6d28d9', '#7c3aed', '#8b5cf6'\] \} \},
          series: \[\{ type: 'heatmap', data: data, label: \{ show: true, color: '#fff', fontSize: 11, textShadowColor: 'rgba\(0,0,0,0\.8\)', textShadowBlur: 2, formatter: p=>p\.value\[2\]\+'%' \} \}\]
        \}, \{replaceMerge: \["series"\]\}\);
      \} else \{
        const lbl = globalAsset\.toUpperCase\(\) \+ sortIndic\(globalAsset\.toUpperCase\(\)\);
        sortedProb\.forEach\(\(d, yi\) => \{
          let v = globalAsset === 'nq' \? d\.BNF_DB_Prob : d\.BNF_DB_Prob;
          data\.push\(\[0, yi, \+v\.toFixed\(1\)\]\);
        \}\);"""

prob_heatmap_new = r"""        const lbl = "BNF" + sortIndic("BNF");
        sortedProb.forEach((d, yi) => {
          let v = d.BNF_DB_Prob;
          data.push([0, yi, +v.toFixed(1)]);
        });"""

js = re.sub(prob_heatmap_old, prob_heatmap_new, js)

with open(main_js, 'w', encoding='utf-8') as f:
    f.write(js)

print("Done fixing main.js")
