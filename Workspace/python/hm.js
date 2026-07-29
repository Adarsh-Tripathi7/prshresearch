let hmSortCol = null, hmSortDir = 0;

function updateHeatmap() {
  const type = segVal('segHmType'); const dir = segVal('segHmDir');
  const c = ec('chartHeatmap'); const dom = c.getDom();
  
  if (!c._hasSort) {
    c.on('click', function(p) {
      if (p.componentType === 'xAxis') {
        if (hmSortCol === p.value) { hmSortDir = hmSortDir === 1 ? -1 : 1; }
        else { hmSortCol = p.value; hmSortDir = -1; }
        updateHeatmap();
      }
    });
    c._hasSort = true;
  }
  
  const sortIndic = val => {
      if (hmSortCol === val && hmSortDir !== 0) return hmSortDir === -1 ? ' ↓' : ' ↑';
      return '';
  };
  
  if (type === 'prob') {
    $('hmDirWrap').style.display = 'none';
    const titleAsset = globalAsset === 'both' ? 'Combined' : globalAsset.toUpperCase();
    $('hmTitle').innerHTML = `<div class="dot" style="background:var(--accent)"></div> DB Probability Heatmap (${titleAsset}) <span style="font-size:10px;color:var(--text-3)">(Click X-axis to sort)</span>`;
    
    let sortedProb = [...probData];
    if (hmSortDir !== 0 && hmSortCol) {
       sortedProb.sort((a,b) => {
           let vA = hmSortCol.includes('NQ') ? a.NQ_DB_Prob : (hmSortCol.includes('ES') ? a.ES_DB_Prob : 0);
           let vB = hmSortCol.includes('NQ') ? b.NQ_DB_Prob : (hmSortCol.includes('ES') ? b.ES_DB_Prob : 0);
           return (vA - vB) * hmSortDir;
       });
    }
    const windows = sortedProb.map(d => d.Window);
    const reqHeight = Math.max(400, windows.length * 30);
    dom.style.height = reqHeight + 'px'; c.resize();
    
    const data = [];
    if (globalAsset === 'both') {
      const lblNQ = 'NQ' + sortIndic('NQ');
      const lblES = 'ES' + sortIndic('ES');
      sortedProb.forEach((d, yi) => { data.push([0, yi, +d.NQ_DB_Prob.toFixed(1)]); data.push([1, yi, +d.ES_DB_Prob.toFixed(1)]); });
      c.setOption({
        tooltip: TT, xAxis: { type: 'category', data: [lblNQ, lblES], position: 'top', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#a1a1aa', fontSize: 13, fontWeight: 'bold' }, triggerEvent: true },
        yAxis: { type: 'category', data: windows, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#71717a', fontSize: 10, fontFamily: 'IBM Plex Mono' } },
        grid: { top: 40, right: 10, bottom: 10, left: 85 },
        visualMap: { show: false, min: 20, max: 90, inRange: { color: ['#0f172a', '#1e3a8a', '#2563eb', '#3b82f6', '#60a5fa'] } },
        series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 11, formatter: p=>p.value[2]+'%' }, emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 1 } } }]
      }, true);
    } else {
      const lblAsset = globalAsset.toUpperCase() + sortIndic(globalAsset.toUpperCase());
      sortedProb.forEach((d, yi) => { 
        const val = globalAsset === 'nq' ? d.NQ_DB_Prob : d.ES_DB_Prob;
        data.push([0, yi, +val.toFixed(1)]); 
      });
      c.setOption({
        tooltip: TT, xAxis: { type: 'category', data: [lblAsset], position: 'top', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#a1a1aa', fontSize: 13, fontWeight: 'bold' }, triggerEvent: true },
        yAxis: { type: 'category', data: windows, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#71717a', fontSize: 10, fontFamily: 'IBM Plex Mono' } },
        grid: { top: 40, right: 10, bottom: 10, left: 85 },
        visualMap: { show: false, min: 20, max: 90, inRange: { color: ['#0f172a', '#1e3a8a', '#2563eb', '#3b82f6', '#60a5fa'] } },
        series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 11, formatter: p=>p.value[2]+'%' }, emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 1 } } }]
      }, true);
    }
  } else if (type === 'corr') {
    $('hmDirWrap').style.display = 'none';
    $('hmTitle').innerHTML = '<div class="dot" style="background:var(--warm)"></div> Leader/Lagger Correlation <span style="font-size:10px;color:var(--text-3)">(Click X-axis to sort)</span>';
    if (!corrData || !corrData.length) { c.clear(); return; }
    
    let sortedCorr = [...corrData];
    const cols = [{key:'ES High Break (NQ Follows)', label:'ES Lead ↑'},{key:'ES Low Break (NQ Follows)', label:'ES Lead ↓'},{key:'NQ High Break (ES Follows)', label:'NQ Lead ↑'},{key:'NQ Low Break (ES Follows)', label:'NQ Lead ↓'}];
    if (hmSortDir !== 0 && hmSortCol) {
       const colKey = cols.find(x => hmSortCol.startsWith(x.label))?.key;
       if (colKey) sortedCorr.sort((a,b) => (a[colKey] - b[colKey]) * hmSortDir);
    }
    
    const windows = sortedCorr.map(d => d.Window);
    const reqHeight = Math.max(400, windows.length * 30);
    dom.style.height = reqHeight + 'px'; c.resize();
    
    const data = []; sortedCorr.forEach((d, yi) => cols.forEach((col, xi) => data.push([xi, yi, typeof d[col.key]==='number'?+d[col.key].toFixed(1):0])));
    c.setOption({
      tooltip: TT, xAxis: { type: 'category', data: cols.map(c=>c.label + sortIndic(c.label)), position: 'top', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#a1a1aa', fontSize: 10, rotate: 30 }, triggerEvent: true },
      yAxis: { type: 'category', data: windows, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#71717a', fontSize: 10, fontFamily: 'IBM Plex Mono' } },
      grid: { top: 50, right: 10, bottom: 10, left: 85 },
      visualMap: { show: false, min: 30, max: 90, inRange: { color: ['#170505', '#450a0a', '#9f1239', '#e11d48', '#fb7185'] } },
      series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 10, formatter: p=>p.value[2]+'%' } }]
    }, true);
  } else {
    $('hmDirWrap').style.display = 'inline-flex';
    const btype = type === 'ext_db' ? 'double_break' : type === 'ext_sb' ? 'single_break' : 'all_breaks';
    const titleAsset = globalAsset === 'both' ? 'Combined Avg' : globalAsset.toUpperCase();
    $('hmTitle').innerHTML = `<div class="dot" style="background:var(--accent)"></div> Extension Matrix (${titleAsset}) <span style="font-size:10px;color:var(--text-3)">(Click X-axis to sort)</span>`;
    
    const refData = EXT[globalAsset === 'es' ? 'es' : 'nq']?.[btype]?.[dir];
    if (!refData || !refData.length) { c.clear(); return; }
    
    let sortedRef = [...refData];
    if (hmSortDir !== 0 && hmSortCol) {
       const p = PCT.find(x => hmSortCol.startsWith(x));
       if (p) {
           sortedRef.sort((a, b) => {
               let rNqA = EXT['nq']?.[btype]?.[dir]?.find(x => x.Window === a.Window);
               let rEsA = EXT['es']?.[btype]?.[dir]?.find(x => x.Window === a.Window);
               let vA = 0, vB = 0;
               if (globalAsset === 'both') { vA = ((rNqA?.[p]||0) + (rEsA?.[p]||0))/2; }
               else if (globalAsset === 'nq') { vA = rNqA?.[p]||0; } else { vA = rEsA?.[p]||0; }
               
               let rNqB = EXT['nq']?.[btype]?.[dir]?.find(x => x.Window === b.Window);
               let rEsB = EXT['es']?.[btype]?.[dir]?.find(x => x.Window === b.Window);
               if (globalAsset === 'both') { vB = ((rNqB?.[p]||0) + (rEsB?.[p]||0))/2; }
               else if (globalAsset === 'nq') { vB = rNqB?.[p]||0; } else { vB = rEsB?.[p]||0; }
               return (vA - vB) * hmSortDir;
           });
       }
    }
    
    const windows = sortedRef.map(r => r.Window);
    const reqHeight = Math.max(400, windows.length * 30);
    dom.style.height = reqHeight + 'px'; c.resize();
    
    const data = []; let maxV = 0;
    
    windows.forEach((w, yi) => {
      let rNq, rEs;
      if (globalAsset === 'both' || globalAsset === 'nq') rNq = EXT['nq']?.[btype]?.[dir]?.find(x => x.Window === w);
      if (globalAsset === 'both' || globalAsset === 'es') rEs = EXT['es']?.[btype]?.[dir]?.find(x => x.Window === w);
      
      PCT.forEach((p, xi) => {
        let v;
        if (globalAsset === 'both') {
          const vNq = rNq ? rNq[p] : 0;
          const vEs = rEs ? rEs[p] : 0;
          v = (typeof vNq === 'number' && typeof vEs === 'number') ? (vNq + vEs) / 2 : 0;
        } else if (globalAsset === 'nq') {
          v = rNq ? rNq[p] : 0;
        } else {
          v = rEs ? rEs[p] : 0;
        }
        if (p !== '100%' && v > maxV) maxV = v;
        data.push([xi, yi, typeof v === 'number' ? +v.toFixed(2) : 0]);
      });
    });
    
    c.setOption({
      tooltip: TT, xAxis: { type: 'category', data: PCT.map(p => p + sortIndic(p)), position: 'top', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#a1a1aa', fontSize: 11 }, triggerEvent: true },
      yAxis: { type: 'category', data: windows, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#71717a', fontSize: 10, fontFamily: 'IBM Plex Mono' } },
      grid: { top: 40, right: 10, bottom: 10, left: 85 },
      visualMap: { show: false, min: 1, max: maxV || 5, inRange: { color: ['#022c22', '#064e3b', '#065f46', '#047857', '#059669', '#10b981', '#34d399', '#6ee7b7'] } },
      series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 10, formatter: p=>p.value[2].toFixed(1) }, emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 1 } } }]
    }, true);
  }
}
