
let probData = [];
let corrData = [];
let EXT = {};

window.loadTimeframeData = async function(tf) {
  try {
    const res = await fetch(`data/${tf}.json`);
    const _D = await res.json();
    probData = _D.prob || [];
    corrData = _D.corr || [];
    EXT = _D.ext || {};
    
    const labelMatch = tf.match(/time_range_(.+)/);
    if (labelMatch && $('timeBadgeBtn')) {
       let lbl = labelMatch[1].toUpperCase().replace(/_1M_STEP/g, ' / 1M STEP').replace(/_15M_STEP/g, ' / 15M STEP');
       $('timeBadgeBtn').innerText = lbl;
       document.title = 'Prsh Capital | ' + lbl;
    }
    
    if (typeof updateAllDashboards === 'function') {
        updateAllDashboards();
    }
    const menu = $('timeMenu');
    if (menu) menu.classList.remove('open');
  } catch (e) {
    console.error("Failed to load data for", tf, e);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tf = btn.getAttribute('data-tf');
      if (tf) {
        window.history.pushState({tf: tf}, '', `dashboard.html?tf=${tf}`);
        loadTimeframeData(tf);
        document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }
    });
  });
  
  if (document.querySelectorAll('.tf-btn').length > 0) {
      const urlParams = new URLSearchParams(window.location.search);
      const tf = urlParams.get('tf') || 'time_range_60m';
      
      const btn = document.querySelector(`.tf-btn[data-tf="${tf}"]`);
      if (btn) btn.classList.add('active');
      
      loadTimeframeData(tf);
  }
});

window.addEventListener('popstate', (e) => {
  if (e.state && e.state.tf) {
    loadTimeframeData(e.state.tf);
    document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.tf-btn[data-tf="${e.state.tf}"]`);
    if (btn) btn.classList.add('active');
  }
});

const PCT = ['5%','10%','15%','20%','25%','30%','35%','40%','45%','50%','55%','60%','65%','70%','75%','80%','85%','90%','95%','100%'];
function pctLabel(p) { return p === '100%' ? 'MAX' : (100 - parseInt(p)) + '%'; }
const extLabels = PCT.map(pctLabel);

const $ = id => document.getElementById(id);
const $$ = (s, c) => (c || document).querySelectorAll(s);

function initSeg(id, cb) {
  const el = $(id); if (!el) return;
  el.querySelectorAll('button').forEach(b => {
    b.addEventListener('click', () => { el.querySelectorAll('button').forEach(x => x.classList.remove('active')); b.classList.add('active'); if (cb) cb(b.dataset.v); });
  });
}
function segVal(id) { const a = $(id)?.querySelector('button.active'); return a ? a.dataset.v : ''; }

const charts = {};
const ro = new ResizeObserver(entries => { requestAnimationFrame(() => { entries.forEach(entry => { const id = entry.target.id; if (charts[id]) charts[id].resize(); }); }); });
function ec(id) {
  if (!charts[id]) { charts[id] = echarts.init($(id), null, { renderer: 'canvas' }); ro.observe($(id)); }
  return charts[id];
}
function resizeAll() { Object.values(charts).forEach(c => c.resize()); }

const TT = { backgroundColor: '#18181b', borderColor: '#3f3f46', textStyle: { fontFamily: 'IBM Plex Mono', fontSize: 12, color: '#fafafa' }, padding: [12, 16], extraCssText: 'border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);' };
const AXIS_STYLE = { axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }, axisTick: { show: false }, axisLabel: { fontFamily: 'IBM Plex Mono', fontSize: 10, color: '#71717a' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } };

function goTo(name) {
  localStorage.setItem('prsh_active_tab', name);
  $$('.nav-btn').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); b.setAttribute('tabindex', '-1'); });
  $$('#desktopNav button').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); b.setAttribute('tabindex', '-1'); });
  $$('.page').forEach(p => p.classList.remove('active'));
  const mb = document.querySelector(`.nav-btn[data-p="${name}"]`);
  const db = document.querySelector(`#desktopNav button[data-p="${name}"]`);
  if (mb) { mb.classList.add('active'); mb.setAttribute('aria-selected', 'true'); mb.setAttribute('tabindex', '0'); mb.focus(); }
  if (db) { db.classList.add('active'); db.setAttribute('aria-selected', 'true'); db.setAttribute('tabindex', '0'); db.focus(); }
  const pg = $('page-' + name);
  if (pg) { 
      pg.classList.add('active'); 
      updateAllDashboards(); 
      setTimeout(resizeAll, 50); 
  }
  if ($('spotlight') && $('spotlight').classList.contains('open')) { $('search').dispatchEvent(new Event('input')); }
}
$$('.nav-btn').forEach(b => b.addEventListener('click', () => goTo(b.dataset.p)));
$$('#desktopNav button').forEach(b => b.addEventListener('click', () => goTo(b.dataset.p)));

function handleTabKeydown(e, tablistId) {
    const tabs = Array.from($$('#' + tablistId + ' button'));
    const currentIndex = tabs.findIndex(t => t === document.activeElement);
    if (currentIndex === -1) return;
    let nextIndex = currentIndex;
    if (e.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length;
    else if (e.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    if (nextIndex !== currentIndex) {
        e.preventDefault();
        goTo(tabs[nextIndex].dataset.p);
    }
}
$('desktopNav').addEventListener('keydown', e => handleTabKeydown(e, 'desktopNav'));
$('bottomNav').addEventListener('keydown', e => handleTabKeydown(e, 'bottomNav'));

$('search').addEventListener('input', function() {
  const q = this.value.trim().toLowerCase().replace(/:/g, ''); const spot = $('spotlight');
  if (!q) { spot.classList.remove('open'); return; }
  const matchWin = probData.find(d => d.Window.toLowerCase().replace(/:/g, '').startsWith(q));
  if (matchWin) { spot.classList.add('open'); showSpotlight(matchWin.Window); } else { spot.classList.remove('open'); }
});
$('spotClose').addEventListener('click', () => { $('spotlight').classList.remove('open'); $('search').value = ''; });

function showSpotlight(win) {
  $('spotTitle').innerHTML = `Window: ${win}`;
  const p = probData.find(d => d.Window === win);
  const pf = (typeof _D !== 'undefined' && _D.prob_first) ? _D.prob_first.find(d => d.Window === win) : null;
  const currentView = document.querySelector('.page.active')?.id || 'page-overview';
  let html = '';
  
  const showProb = currentView === 'page-overview' || currentView === 'page-probability';
  const showExt = currentView === 'page-overview' || currentView === 'page-extensions';
  const showHlFirst = currentView === 'page-overview' || currentView === 'page-hl_first';

  const assets = globalAsset === 'both' ? ['nq', 'es'] : [globalAsset];

  if (showProb && p) {
    let innerCombined = '';
    if (assets.includes('nq')) innerCombined += `<div class="spot-row"><span class="lbl">NQ</span><span class="val c-dn">${p.NQ_DB_Prob.toFixed(1)}%</span></div>`;
    if (assets.includes('es')) innerCombined += `<div class="spot-row"><span class="lbl">ES</span><span class="val c-dn">${p.ES_DB_Prob.toFixed(1)}%</span></div>`;
    html += `<div class="spot-card"><div class="spot-card-title">Double Break % (Combined)</div>${innerCombined}</div>`;
    
    if (currentView === 'page-probability' && pf) {
        let innerHigh = '';
        if (assets.includes('nq')) innerHigh += `<div class="spot-row"><span class="lbl">NQ</span><span class="val c-dn">${pf.NQ_H_First_DB_Prob?.toFixed(1) || '—'}%</span></div>`;
        if (assets.includes('es')) innerHigh += `<div class="spot-row"><span class="lbl">ES</span><span class="val c-dn">${pf.ES_H_First_DB_Prob?.toFixed(1) || '—'}%</span></div>`;
        html += `<div class="spot-card"><div class="spot-card-title">Double Break % (High First)</div>${innerHigh}</div>`;
        
        let innerLow = '';
        if (assets.includes('nq')) innerLow += `<div class="spot-row"><span class="lbl">NQ</span><span class="val c-dn">${pf.NQ_L_First_DB_Prob?.toFixed(1) || '—'}%</span></div>`;
        if (assets.includes('es')) innerLow += `<div class="spot-row"><span class="lbl">ES</span><span class="val c-dn">${pf.ES_L_First_DB_Prob?.toFixed(1) || '—'}%</span></div>`;
        html += `<div class="spot-card"><div class="spot-card-title">Double Break % (Low First)</div>${innerLow}</div>`;
    }
  }

  if (showExt) {
    if (currentView === 'page-overview') {
      for (const asset of assets) {
        for (const brk of ['double_break','single_break']) {
          const d = EXT[asset]?.[brk]?.combined; if (!d) continue;
          const row = d.find(r => r.Window === win); if (!row) continue;
          const lbl = `${asset.toUpperCase()} ${brk==='double_break'?'DB':'SB'}`;
          html += `<div class="spot-card"><div class="spot-card-title">${lbl} (Combined)</div><div class="spot-row"><span class="lbl">Median</span><span class="val" style="color:var(--warm)">${row['50%']?.toFixed(2)||'—'}R</span></div><div class="spot-row"><span class="lbl">90th pctl</span><span class="val" style="color:var(--accent)">${row['90%']?.toFixed(2)||'—'}R</span></div></div>`;
        }
      }
    } else if (currentView === 'page-extensions') {
      for (const asset of assets) {
        for (const direction of ['combined', 'high_first', 'low_first']) {
          const d = EXT[asset]?.['all_breaks']?.[direction]; if (!d) continue;
          const row = d.find(r => r.Window === win); if (!row) continue;
          const lbl = `${asset.toUpperCase()} All Breaks`;
          const dirLbl = direction === 'combined' ? 'Combined' : (direction === 'high_first' ? 'High First' : 'Low First');
          html += `<div class="spot-card"><div class="spot-card-title">${lbl} (${dirLbl})</div>`;
          html += `<div class="spot-row"><span class="lbl">99% Hit Rate</span><span class="val" style="color:var(--text-3)">${row['1%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">95% Hit Rate</span><span class="val" style="color:var(--text-2)">${row['5%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">75% Hit Rate</span><span class="val" style="color:var(--text-1)">${row['25%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">Median (50%)</span><span class="val" style="color:var(--warm)">${row['50%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">25% Hit Rate</span><span class="val" style="color:var(--up)">${row['75%']?.toFixed(2)||'—'}R</span></div>`;
          html += `<div class="spot-row"><span class="lbl">10% Hit Rate</span><span class="val" style="color:var(--accent)">${row['90%']?.toFixed(2)||'—'}R</span></div>`;
          html += `</div>`;
        }
      }
    }
  }
  
  if (showHlFirst && pf) {
    if (currentView === 'page-hl_first') {
      for (const dir of ['High First', 'Low First', 'Combined']) {
        let inner = '';
        for (const asset of assets) {
          const u = asset.toUpperCase();
          let opp, cond;
          if (dir === 'High First') {
              opp = pf[`${u}_H_First_L_Break_Prob`];
              cond = pf[`${u}_H_First_CBM_Prob`];
          } else if (dir === 'Low First') {
              opp = pf[`${u}_L_First_H_Break_Prob`];
              cond = pf[`${u}_L_First_CAM_Prob`];
          } else {
              opp = pf[`${u}_Comb_Opp_Prob`];
              cond = pf[`${u}_Comb_Cond_Prob`];
          }
          inner += `<div class="spot-row"><span class="lbl">${u} Opp Break</span><span class="val c-mono">${opp?.toFixed(1) || '—'}%</span></div>`;
          inner += `<div class="spot-row"><span class="lbl">${u} Cond Opp Break</span><span class="val c-mono" style="color:var(--accent)">${cond?.toFixed(1) || '—'}%</span></div>`;
        }
        html += `<div class="spot-card"><div class="spot-card-title">H/L First (${dir})</div>${inner}</div>`;
      }
    } else if (currentView === 'page-overview') {
        let inner = '';
        for (const asset of assets) {
          const u = asset.toUpperCase();
          const opp = pf[`${u}_Comb_Opp_Prob`];
          const cond = pf[`${u}_Comb_Cond_Prob`];
          inner += `<div class="spot-row"><span class="lbl">${u} Opp Break</span><span class="val c-mono">${opp?.toFixed(1) || '—'}%</span></div>`;
          inner += `<div class="spot-row"><span class="lbl">${u} Cond Opp Break</span><span class="val c-mono" style="color:var(--accent)">${cond?.toFixed(1) || '—'}%</span></div>`;
        }
        html += `<div class="spot-card"><div class="spot-card-title">H/L First (Combined)</div>${inner}</div>`;
    }
  }
  
  $('spotGrid').innerHTML = html;
}

// Global UI State
let globalAsset = localStorage.getItem('prsh_global_asset') || 'both'; // 'both', 'nq', 'es'
const btnGlobalAsset = $('btnGlobalAsset');
const timeBadgeBtn = $('timeBadgeBtn');

// Initialize button text on load
btnGlobalAsset.innerHTML = globalAsset === 'both' ? 'NQ | ES' : globalAsset.toUpperCase();

btnGlobalAsset.addEventListener('click', () => {
  if (globalAsset === 'both') globalAsset = 'nq';
  else if (globalAsset === 'nq') globalAsset = 'es';
  else globalAsset = 'both';
  
  localStorage.setItem('prsh_global_asset', globalAsset);
  btnGlobalAsset.innerHTML = globalAsset === 'both' ? 'NQ | ES' : globalAsset.toUpperCase();
  updateAllDashboards();
});

const timeframes = [
  'time_range_7m.html', 'time_range_7m_1m_step.html', 'time_range_10m.html', 
  'time_range_15m.html', 'time_range_15m_step.html', 'time_range_30m.html', 
  'time_range_30m_15m_step.html', 'time_range_45m.html', 'time_range_60m.html', 'time_range_120m.html'
];
timeBadgeBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  const current = window.location.pathname.split('/').pop() || 'time_range_60m.html';
  let idx = timeframes.indexOf(current);
  if (idx === -1) idx = 0;
  const nextIdx = (idx + 1) % timeframes.length;
  const nextFile = timeframes[nextIdx];
  
  try {
      const res = await fetch(nextFile);
      const text = await res.text();
      const match = text.match(/const _D = (\{.*?\});/);
      if (match) {
          const newD = JSON.parse(match[1]);
          // We can't reassign a const _D, but we can assign its properties if we change _D to var or let.
          // Wait, _D is const in the HTML script tag.
          // This fetch update without reload won't work perfectly if _D is const, BUT:
          // The old logic was designed to work around this. Let's just reload the page on click.
          window.location.href = nextFile;
      } else {
          window.location.href = nextFile;
      }
  } catch(err) {
      window.location.href = nextFile;
  }
});

window.addEventListener('popstate', () => {
    window.location.reload();
});

function updateAllDashboards() {
  updateKPIs();
  
  const currentView = document.querySelector('.page.active')?.id || 'page-overview';
  
  setTimeout(() => {
    if (currentView === 'page-overview') {
        updateOverviewCharts();
    } else if (currentView === 'page-probability') {
        updateProb();
    } else if (currentView === 'page-hl_first') {
        updateHlFirst();
    } else if (currentView === 'page-extensions') {
        updateExt();
    } else if (currentView === 'page-heatmap') {
        updateHeatmap();
    }
  }, 10);
  
  if ($('spotlight') && $('spotlight').classList.contains('open')) {
      $('search').dispatchEvent(new Event('input'));
  }
}

function updateKPIs() {
  let minP=100, maxP=0, minW='', maxW='', sumP=0, validCount=0;
  probData.forEach(d => {
    let a;
    if (globalAsset === 'both') a = (d.NQ_DB_Prob + d.ES_DB_Prob) / 2;
    else if (globalAsset === 'nq') a = d.NQ_DB_Prob;
    else a = d.ES_DB_Prob;
    
    if (a !== undefined && !isNaN(a)) {
      if (a < minP) { minP = a; minW = d.Window; }
      if (a > maxP) { maxP = a; maxW = d.Window; }
      sumP += a;
      validCount++;
    }
  });
  const avgP = validCount > 0 ? (sumP / validCount) : 0;
  
  $('kpiStrip').innerHTML = `
    <div class="kpi-card"><div class="kpi-label">Windows</div><div class="kpi-value">${probData.length}</div><div class="kpi-sub">Total Analyzed</div></div>
    <div class="kpi-card"><div class="kpi-label" style="color:var(--up)">Lowest Chop</div><div class="kpi-value">${minP.toFixed(1)}%</div><div class="kpi-sub">${minW}</div></div>
    <div class="kpi-card"><div class="kpi-label" style="color:var(--dn)">Max Fakeout</div><div class="kpi-value">${maxP.toFixed(1)}%</div><div class="kpi-sub">${maxW}</div></div>
    <div class="kpi-card"><div class="kpi-label" style="color:var(--accent)">Avg Prob</div><div class="kpi-value">${avgP.toFixed(1)}%</div><div class="kpi-sub">Overall Baseline</div></div>
  `;
}

function updateOverviewCharts() {
  const labels = probData.map(d => d.Window);
  const nq = probData.map(d => d.NQ_DB_Prob);
  const es = probData.map(d => d.ES_DB_Prob);
  
  const seriesProb = [];
  if (globalAsset === 'both' || globalAsset === 'nq') {
    seriesProb.push({ name: 'NQ', type: 'line', data: nq, smooth: 0.4, symbol: 'none', lineStyle: { width: 3, color: '#6366f1' }, areaStyle: { color: 'rgba(99,102,241,0.1)' } });
  }
  if (globalAsset === 'both' || globalAsset === 'es') {
    seriesProb.push({ name: 'ES', type: 'line', data: es, smooth: 0.4, symbol: 'none', lineStyle: { width: 3, color: '#38bdf8' } });
  }

  ec('chartProb').setOption({
    tooltip: { ...TT, trigger: 'axis' }, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' }, icon: 'circle' },
    grid: { top: 30, right: 10, bottom: 70, left: 35 },
    xAxis: { ...AXIS_STYLE, type: 'category', data: labels, axisLabel: { ...AXIS_STYLE.axisLabel, rotate: 45 } },
    yAxis: { ...AXIS_STYLE, type: 'value', min: 20 },
    series: seriesProb
  }, {replaceMerge: ["series"]});

  const seriesExt = [];
  let extLabels = [];
  
  if (globalAsset === 'both' || globalAsset === 'nq') {
    const nqDB = EXT.nq?.double_break?.combined || [];
    const nqSB = EXT.nq?.single_break?.combined || [];
    extLabels = nqDB.map(d=>d.Window);
    seriesExt.push({ name: 'NQ Double', type: 'bar', data: nqDB.map(d=>d['50%']), itemStyle: { color: '#ef4444', borderRadius: [4,4,0,0] } });
    seriesExt.push({ name: 'NQ Single', type: 'bar', data: nqSB.map(d=>d['50%']), itemStyle: { color: '#10b981', borderRadius: [4,4,0,0] } });
  }
  if (globalAsset === 'both' || globalAsset === 'es') {
    const esDB = EXT.es?.double_break?.combined || [];
    const esSB = EXT.es?.single_break?.combined || [];
    if (!extLabels.length) extLabels = esDB.map(d=>d.Window);
    seriesExt.push({ name: 'ES Double', type: 'bar', data: esDB.map(d=>d['50%']), itemStyle: { color: '#fca5a5', borderRadius: [4,4,0,0] } });
    seriesExt.push({ name: 'ES Single', type: 'bar', data: esSB.map(d=>d['50%']), itemStyle: { color: '#6ee7b7', borderRadius: [4,4,0,0] } });
  }

  ec('chartMedExt').setOption({
    tooltip: { ...TT, trigger: 'axis' }, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' }, icon: 'roundRect' },
    grid: { top: 30, right: 10, bottom: 70, left: 35 },
    xAxis: { ...AXIS_STYLE, type: 'category', data: extLabels, axisLabel: { ...AXIS_STYLE.axisLabel, rotate: 45 } },
    yAxis: { ...AXIS_STYLE, type: 'value' },
    series: seriesExt
  }, {replaceMerge: ["series"]});
}

(function() {
  const activeTab = localStorage.getItem('prsh_active_tab') || 'overview';
  goTo(activeTab);
})();

let probSortCol = 'Window', probSortDir = 0;

function updateProb() {
  const data = probData;
  if (!data || !data.length) return;
  
  let mappedData = data.map(d => {
    const n = d.NQ_DB_Prob;
    const e = d.ES_DB_Prob;
    return { Window: d.Window, nq: n, es: e, avg: n&&e?(n+e)/2:0, delta: n&&e?(n-e):0 };
  }).filter(d => d.nq !== undefined && d.es !== undefined);
  
  if (probSortDir !== 0) {
    mappedData.sort((a, b) => {
      let vA = a[probSortCol], vB = b[probSortCol];
      if (probSortCol === 'Window') return vA.localeCompare(vB) * probSortDir;
      return (vA - vB) * probSortDir;
    });
  }

  const labels = mappedData.map(d=>d.Window);
  const nqVals = mappedData.map(d=>d.nq);
  const esVals = mappedData.map(d=>d.es);
  
  const series = [];
  if (globalAsset === 'both' || globalAsset === 'nq') series.push({ name: 'NQ', type: 'line', data: nqVals, smooth: 0.3, symbolSize: 6, lineStyle: { width: 3, color: '#6366f1' }, itemStyle: { color: '#6366f1' } });
  if (globalAsset === 'both' || globalAsset === 'es') series.push({ name: 'ES', type: 'line', data: esVals, smooth: 0.3, symbolSize: 6, lineStyle: { width: 3, color: '#38bdf8' }, itemStyle: { color: '#38bdf8' } });

  ec('chartProbFull').setOption({
    tooltip: { ...TT, trigger: 'axis' }, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' }, icon: 'circle' },
    grid: { top: 30, right: 10, bottom: 70, left: 35 }, dataZoom: [{ type: 'inside' }],
    xAxis: { ...AXIS_STYLE, type: 'category', data: labels, axisLabel: { ...AXIS_STYLE.axisLabel, rotate: 45 } },
    yAxis: { ...AXIS_STYLE, type: 'value', min: 0, max: 100 },
    series: series
  }, {replaceMerge: ["series"]});
  
  const showNq = globalAsset === 'both' || globalAsset === 'nq';
  const showEs = globalAsset === 'both' || globalAsset === 'es';
  const showAvg = globalAsset === 'both';
  
  function thHtml(colId, label, cls) {
    const isAct = probSortCol === colId && probSortDir !== 0 ? 'color:var(--text-1); background:var(--bg-hover); border-bottom: 2px solid var(--accent);' : 'cursor:pointer;';
    let sortInd = ''; if (probSortCol === colId && probSortDir !== 0) { sortInd = probSortDir === -1 ? ' ↓' : ' ↑'; }
    return `<th class="${cls} prob-sort-btn" data-c="${colId}" style="${isAct}">${label}${sortInd}</th>`;
  }
  
  let th = '<tr>' + thHtml('Window', 'Window', '');
  if (showNq) th += thHtml('nq', 'NQ %', 'r');
  if (showEs) th += thHtml('es', 'ES %', 'r');
  if (showAvg) { th += thHtml('avg', 'Avg', 'r') + thHtml('delta', 'Δ', 'r'); }
  th += '</tr>';
  $('tblProb').previousElementSibling.innerHTML = th;
  
  $$('.prob-sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const c = btn.dataset.c;
      if (probSortCol === c) {
        if (probSortDir === -1) probSortDir = 1; else if (probSortDir === 1) probSortDir = 0; else probSortDir = -1;
      } else { probSortCol = c; probSortDir = -1; }
      updateProb();
    });
  });
  
  let h = '';
  mappedData.forEach(d => {
    const avg = d.avg; const delta = d.delta; const dc = delta > 0 ? 'c-dn' : 'c-up'; const bg = avg > 75 ? 'hl' : '';
    
    h += `<tr class="${bg}"><td class="c-mono">${d.Window}</td>`;
    if (showNq) h += `<td class="r c-mono">${d.nq.toFixed(1)}</td>`;
    if (showEs) h += `<td class="r c-mono">${d.es.toFixed(1)}</td>`;
    if (showAvg) h += `<td class="r c-mono">${avg.toFixed(1)}</td><td class="r c-mono ${dc}">${delta>0?'+':''}${delta.toFixed(1)}</td>`;
    h += `</tr>`;
  });
  $('tblProb').innerHTML = h;
}
updateProb();

let hlFirstSortCol = 'Window', hlFirstSortDir = 0;

function updateHlFirst() {
  const dir = segVal('segHlFirstDir') || 'high_first';
  const data = typeof _D !== 'undefined' ? _D.prob_first : [];
  if (!data || !data.length) return;
  
  let mappedData = data.map(d => {
    let n, e, n_cond, e_cond;
    if (dir === 'high_first') {
        n = d.NQ_H_First_L_Break_Prob;
        e = d.ES_H_First_L_Break_Prob;
        n_cond = d.NQ_H_First_CBM_Prob;
        e_cond = d.ES_H_First_CBM_Prob;
    } else if (dir === 'low_first') {
        n = d.NQ_L_First_H_Break_Prob;
        e = d.ES_L_First_H_Break_Prob;
        n_cond = d.NQ_L_First_CAM_Prob;
        e_cond = d.ES_L_First_CAM_Prob;
    } else {
        n = d.NQ_Comb_Opp_Prob;
        e = d.ES_Comb_Opp_Prob;
        n_cond = d.NQ_Comb_Cond_Prob;
        e_cond = d.ES_Comb_Cond_Prob;
    }
    return { Window: d.Window, nq: n, es: e, avg: n&&e?(n+e)/2:0, delta: n&&e?(n-e):0, nq_cond: n_cond, es_cond: e_cond, cond_avg: n_cond&&e_cond?(n_cond+e_cond)/2:0 };
  }).filter(d => d.nq !== undefined && d.es !== undefined);
  
  if (hlFirstSortDir !== 0) {
    mappedData.sort((a, b) => {
      let vA = a[hlFirstSortCol], vB = b[hlFirstSortCol];
      if (hlFirstSortCol === 'Window') return vA.localeCompare(vB) * hlFirstSortDir;
      return (vA - vB) * hlFirstSortDir;
    });
  }

  const labels = mappedData.map(d=>d.Window);
  const nqVals = mappedData.map(d=>d.nq);
  const esVals = mappedData.map(d=>d.es);
  
  const series = [];
  if (globalAsset === 'both' || globalAsset === 'nq') series.push({ name: 'NQ', type: 'line', data: nqVals, smooth: 0.3, symbolSize: 6, lineStyle: { width: 3, color: '#6366f1' }, itemStyle: { color: '#6366f1' } });
  if (globalAsset === 'both' || globalAsset === 'es') series.push({ name: 'ES', type: 'line', data: esVals, smooth: 0.3, symbolSize: 6, lineStyle: { width: 3, color: '#38bdf8' }, itemStyle: { color: '#38bdf8' } });

  ec('chartHlFirst').setOption({
    tooltip: { ...TT, trigger: 'axis' }, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' }, icon: 'circle' },
    grid: { top: 30, right: 10, bottom: 70, left: 35 }, dataZoom: [{ type: 'inside' }],
    xAxis: { ...AXIS_STYLE, type: 'category', data: labels, axisLabel: { ...AXIS_STYLE.axisLabel, rotate: 45 } },
    yAxis: { ...AXIS_STYLE, type: 'value', min: 0, max: 100 },
    series: series
  }, {replaceMerge: ["series"]});
  
  const showNq = globalAsset === 'both' || globalAsset === 'nq';
  const showEs = globalAsset === 'both' || globalAsset === 'es';
  const showAvg = globalAsset === 'both';
  
  function thHtml(colId, label, cls) {
    const isAct = hlFirstSortCol === colId && hlFirstSortDir !== 0 ? 'color:var(--text-1); background:var(--bg-hover); border-bottom: 2px solid var(--accent);' : 'cursor:pointer;';
    let sortInd = ''; if (hlFirstSortCol === colId && hlFirstSortDir !== 0) { sortInd = hlFirstSortDir === -1 ? ' ↓' : ' ↑'; }
    return `<th class="${cls} hlfirst-sort-btn" data-c="${colId}" style="${isAct}">${label}${sortInd}</th>`;
  }
  
  let th = '<tr>' + thHtml('Window', 'Window', '');
  if (showNq) {
      th += thHtml('nq', 'Opp Break NQ %', 'r');
      th += thHtml('nq_cond', 'Cond Opp Break NQ %', 'r');
  }
  if (showEs) {
      th += thHtml('es', 'Opp Break ES %', 'r');
      th += thHtml('es_cond', 'Cond Opp Break ES %', 'r');
  }
  if (showAvg) { th += thHtml('avg', 'Avg', 'r') + thHtml('cond_avg', 'Cond Avg', 'r') + thHtml('delta', 'Δ', 'r'); }
  th += '</tr>';
  $('tblHlFirst').previousElementSibling.innerHTML = th;
  
  $$('.hlfirst-sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const c = btn.dataset.c;
      if (hlFirstSortCol === c) {
        if (hlFirstSortDir === -1) hlFirstSortDir = 1; else if (hlFirstSortDir === 1) hlFirstSortDir = 0; else hlFirstSortDir = -1;
      } else { hlFirstSortCol = c; hlFirstSortDir = -1; }
      updateHlFirst();
    });
  });
  
  let h = '';
  mappedData.forEach(d => {
    const avg = d.avg; const delta = d.delta; const dc = delta > 0 ? 'c-dn' : 'c-up'; const bg = avg > 75 ? 'hl' : '';
    
    h += `<tr class="${bg}"><td class="c-mono">${d.Window}</td>`;
    if (showNq) {
        h += `<td class="r c-mono">${d.nq.toFixed(1)}</td>`;
        h += `<td class="r c-mono" style="color:var(--accent)">${d.nq_cond.toFixed(1)}</td>`;
    }
    if (showEs) {
        h += `<td class="r c-mono">${d.es.toFixed(1)}</td>`;
        h += `<td class="r c-mono" style="color:var(--accent)">${d.es_cond.toFixed(1)}</td>`;
    }
    if (showAvg) h += `<td class="r c-mono">${avg.toFixed(1)}</td><td class="r c-mono" style="color:var(--accent)">${d.cond_avg.toFixed(1)}</td><td class="r c-mono ${dc}">${delta>0?'+':''}${delta.toFixed(1)}</td>`;
    h += `</tr>`;
  });
  $('tblHlFirst').innerHTML = h;
}
initSeg('segHlFirstDir', updateHlFirst); updateHlFirst();

let extWin = 0, extPct = '50%', extSortDir = 0;
function extData(asset) { return EXT[asset]?.[segVal('segBreak')]?.[segVal('segDir')] || [] }
function updateExt() {
  const assets = globalAsset === 'both' ? ['nq', 'es'] : [globalAsset];
  const lcMap = { 'nq': '#6366f1', 'es': '#38bdf8' }; // Custom colors for CDF lines if needed, or fallback to break type
  const breakColor = segVal('segBreak') === 'double_break' ? '#ef4444' : segVal('segBreak') === 'single_break' ? '#10b981' : '#38bdf8';

  const seriesCdf = [];
  const seriesBar = [];
  
  let primaryData = extData(assets[0]);
  if (!primaryData.length) return;
  
  let d = [...primaryData];
  if (extSortDir !== 0) {
    d.sort((a, b) => {
      const vA = a[extPct] || 0; const vB = b[extPct] || 0;
      return (vA - vB) * extSortDir;
    });
  }

  // Update Charts
  assets.forEach(asset => {
    const aData = extData(asset);
    if (!aData.length) return;
    
    // For sorting consistency in Bar chart, map using primaryData's sorted windows
    const sortedWindows = d.map(r => r.Window);
    const mappedBarVals = sortedWindows.map(w => {
        const r = aData.find(x => x.Window === w);
        return r ? r[extPct] : 0;
    });
    
    const color = assets.length > 1 ? lcMap[asset] : breakColor;
    
    // CDF Chart
    const targetWinRow = aData.find(r => r.Window === d[Math.min(extWin, d.length - 1)].Window);
    if (targetWinRow) {
      const vals = PCT.map(p => targetWinRow[p]);
      seriesCdf.push({ name: asset.toUpperCase(), type: 'line', data: vals, smooth: 0.3, symbolSize: 6, lineStyle: { width: 3, color: color }, itemStyle: { color: color }, areaStyle: { color: 'rgba(255,255,255,0.05)' } });
    }
    
    // Bar Chart
    seriesBar.push({ name: asset.toUpperCase(), type: 'bar', data: mappedBarVals, itemStyle: { color: color, borderRadius: [4,4,0,0] } });
  });

  ec('chartCdf').setOption({
    tooltip: { ...TT, trigger: 'axis' }, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' }, icon: 'circle', show: assets.length > 1 }, grid: { top: 30, right: 10, bottom: 20, left: 35 },
    xAxis: { ...AXIS_STYLE, type: 'category', data: extLabels }, yAxis: { ...AXIS_STYLE, type: 'value' },
    series: seriesCdf
  }, {replaceMerge: ["series"]});

  const barLabels = d.map(r => r.Window);
  ec('chartBar').setOption({
    tooltip: { ...TT, trigger: 'axis' }, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' }, icon: 'roundRect', show: assets.length > 1 }, grid: { top: 30, right: 10, bottom: 70, left: 35 }, dataZoom: [{ type: 'inside' }],
    xAxis: { ...AXIS_STYLE, type: 'category', data: barLabels, axisLabel: { ...AXIS_STYLE.axisLabel, rotate: 45 } },
    yAxis: { ...AXIS_STYLE, type: 'value' },
    series: seriesBar
  }, {replaceMerge: ["series"]});

  $('extBarHead').innerHTML = `<div class="dot" style="background:var(--up)"></div> ${pctLabel(extPct)} Hit Rate`;
  
  // Update Table Header
  let th = '<tr><th>Window</th>'; 
  if (assets.length > 1) th += '<th>Asset</th>';
  PCT.forEach(p => {
    const isAct = p === extPct ? 'color:var(--text-1); background:var(--bg-hover); border-bottom: 2px solid var(--accent);' : 'cursor:pointer;';
    let sortInd = ''; if (p === extPct && extSortDir !== 0) { sortInd = extSortDir === -1 ? ' ↓' : ' ↑'; }
    th += `<th class="r pct-btn" data-p="${p}" style="${isAct}">${pctLabel(p)}${sortInd}</th>`;
  });
  th += '</tr>'; $('extTHead').innerHTML = th;
  
  $$('#extTHead .pct-btn').forEach(btn => { 
    btn.addEventListener('click', () => { 
      const p = btn.dataset.p;
      if (extPct === p) {
        if (extSortDir === -1) extSortDir = 1; else if (extSortDir === 1) extSortDir = 0; else extSortDir = -1;
      } else {
        extPct = p; extSortDir = -1;
      }
      extWin = 0; updateExt(); 
    }); 
  });
  
  let maxV = 0; 
  assets.forEach(asset => {
    extData(asset).forEach(r => PCT.forEach(p => { if (p !== '100%' && r[p] > maxV) maxV = r[p]; }));
  });
  
  function cellBg(v) { const t = Math.min(1, v / (maxV || 5)); return `hsla(${155 - t * 135}, 50%, ${38 - t * 10}%, .18)`; }
  
  let tb = '';
  d.forEach((r, i) => {
    const cls = i === extWin ? ' class="hl clickable"' : ' class="clickable"';
    
    if (assets.length === 1) {
      tb += `<tr${cls} data-i="${i}"><td class="c-mono">${r.Window}</td>`;
      PCT.forEach(p => { const v = r[p]; tb += `<td class="r c-mono" style="background:${typeof v==='number' ? cellBg(v) : 'transparent'}">${typeof v==='number' ? v.toFixed(2) : v}</td>`; });
      tb += '</tr>';
    } else {
      // Both NQ and ES rows
      const nqRow = extData('nq').find(x => x.Window === r.Window);
      const esRow = extData('es').find(x => x.Window === r.Window);
      
      if (nqRow) {
        tb += `<tr${cls} data-i="${i}"><td class="c-mono">${r.Window}</td><td class="c-mono" style="color:#6366f1">NQ</td>`;
        PCT.forEach(p => { const v = nqRow[p]; tb += `<td class="r c-mono" style="background:${typeof v==='number' ? cellBg(v) : 'transparent'}">${typeof v==='number' ? v.toFixed(2) : v}</td>`; });
        tb += '</tr>';
      }
      if (esRow) {
        // Only trigger click event once per window group, apply styling to both
        tb += `<tr${cls} data-i="${i}"><td class="c-mono" style="border-top:none;color:transparent">${r.Window}</td><td class="c-mono" style="color:#38bdf8">ES</td>`;
        PCT.forEach(p => { const v = esRow[p]; tb += `<td class="r c-mono" style="background:${typeof v==='number' ? cellBg(v) : 'transparent'}">${typeof v==='number' ? v.toFixed(2) : v}</td>`; });
        tb += '</tr>';
      }
    }
  });
  
  $('extTBody').innerHTML = tb;
  $$('#extTBody tr.clickable').forEach(tr => tr.addEventListener('click', () => { extWin = parseInt(tr.dataset.i); updateExt(); }));
}
initSeg('segBreak', () => { extWin = 0; extSortDir = 0; updateExt(); });
initSeg('segDir', () => { extWin = 0; extSortDir = 0; updateExt(); });
updateExt();

let hmSortCol = null, hmSortDir = 0;

function updateHeatmap() {
  const hmContainer = $('chartHeatmap');
  if (!hmContainer) return;
  const c = ec('chartHeatmap'); const dom = c.getDom();
  
  const type = segVal('segHmType'); const dir = segVal('segHmDir');
  if (type === 'prob') {
      dom.style.minWidth = '100%';
  } else if (type === 'corr') {
      dom.style.minWidth = '500px';
  } else {
      dom.style.minWidth = '1000px';
  }
  
  if (!c._hasSort) {
    c.on('click', function(p) {
      if (p.componentType === 'xAxis') {
        let cleanValue = p.value;
        const allLabels = [...extLabels, 'ES Lead ↑', 'ES Lead ↓', 'NQ Lead ↑', 'NQ Lead ↓', 'Combined Avg', 'NQ', 'ES'];
        allLabels.sort((a, b) => b.length - a.length);
        const match = allLabels.find(l => p.value.startsWith(l));
        if (match) cleanValue = match;
        
        if (hmSortCol === cleanValue) { hmSortDir = hmSortDir === 1 ? -1 : 1; }
        else { hmSortCol = cleanValue; hmSortDir = -1; }
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
        series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 11, textShadowColor: 'rgba(0,0,0,0.8)', textShadowBlur: 2, formatter: p=>p.value[2]+'%' }, emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 1 } } }]
      }, {replaceMerge: ["series"]});
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
        series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 11, textShadowColor: 'rgba(0,0,0,0.8)', textShadowBlur: 2, formatter: p=>p.value[2]+'%' }, emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 1 } } }]
      }, {replaceMerge: ["series"]});
    }
  } else if (type === 'corr') {
    $('hmDirWrap').style.display = 'none';
    $('hmTitle').innerHTML = '<div class="dot" style="background:var(--warm)"></div> Leader/Lagger Correlation <span style="font-size:10px;color:var(--text-3)">(Click X-axis to sort)</span>';
    if (!corrData || !corrData.length) { c.clear(); return; }
    
    let sortedCorr = [...corrData];
    const cols = [{key:'ES High Break (NQ Follows)', label:'ES Lead ↑'},{key:'ES Low Break (NQ Follows)', label:'ES Lead ↓'},{key:'NQ High Break (ES Follows)', label:'NQ Lead ↑'},{key:'NQ Low Break (ES Follows)', label:'NQ Lead ↓'}];
    if (hmSortDir !== 0 && hmSortCol) {
       const colKey = cols.find(x => x.label === hmSortCol)?.key;
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
      visualMap: { show: false, min: 65, max: 85, inRange: { color: ['#2e1065', '#4c1d95', '#5b21b6', '#6d28d9', '#7c3aed', '#8b5cf6'] } },
      series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 10, textShadowColor: 'rgba(0,0,0,0.8)', textShadowBlur: 2, formatter: p=>p.value[2]+'%' } }]
    }, {replaceMerge: ["series"]});
  } else {
    $('hmDirWrap').style.display = 'inline-flex';
    const btype = type === 'ext_db' ? 'double_break' : type === 'ext_sb' ? 'single_break' : 'all_breaks';
    const titleAsset = globalAsset === 'both' ? 'Combined Avg' : globalAsset.toUpperCase();
    $('hmTitle').innerHTML = `<div class="dot" style="background:var(--accent)"></div> Extension Matrix (${titleAsset}) <span style="font-size:10px;color:var(--text-3)">(Click X-axis to sort)</span>`;
    
    const refData = EXT[globalAsset === 'es' ? 'es' : 'nq']?.[btype]?.[dir];
    if (!refData || !refData.length) { c.clear(); return; }
    
    let sortedRef = [...refData];
    if (hmSortDir !== 0 && hmSortCol) {
       const idx = extLabels.indexOf(hmSortCol);
       const p = idx !== -1 ? PCT[idx] : null;
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
      tooltip: TT, xAxis: { type: 'category', data: extLabels.map(p => p + sortIndic(p)), position: 'top', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#a1a1aa', fontSize: 11 }, triggerEvent: true },
      yAxis: { type: 'category', data: windows, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#71717a', fontSize: 10, fontFamily: 'IBM Plex Mono' } },
      grid: { top: 40, right: 10, bottom: 10, left: 85 },
      visualMap: { show: false, min: 1, max: maxV || 5, inRange: { color: ['#022c22', '#064e3b', '#065f46', '#047857', '#059669', '#10b981', '#34d399', '#6ee7b7'] } },
      series: [{ type: 'heatmap', data: data, label: { show: true, color: '#fff', fontSize: 10, textShadowColor: 'rgba(0,0,0,0.8)', textShadowBlur: 2, formatter: p=>p.value[2].toFixed(2) }, emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 1 } } }]
    }, {replaceMerge: ["series"]});
  }
}

initSeg('segProbDir', () => updateAllDashboards());
initSeg('segExtType', () => updateAllDashboards()); initSeg('segExtDir', () => updateAllDashboards());
initSeg('segHmType', () => updateAllDashboards()); initSeg('segHmDir', () => updateAllDashboards());

updateAllDashboards();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(()=>{});
  });
}

setTimeout(resizeAll, 100);
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js');
  });
}
