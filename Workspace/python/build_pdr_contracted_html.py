"""Builds pdr_contracted_analysis.html from pdr_multi_analysis.json"""
import json, os

DATA_PATH = r"d:\Antigravity\Results\pdr_multi_analysis.json"
OUT_PATH  = r"d:\Antigravity\imobile ib dashboard\pdr_contracted_analysis.html"

with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

DATA_STR = json.dumps(data, separators=(',', ':'))

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Prsh Capital | PDR Contracted Level Analysis</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
.section-header { margin-top:24px; margin-bottom:16px; padding-bottom:8px; border-bottom:1px solid var(--border); font-size:16px; font-weight:600; color:var(--text-1); display:flex; align-items:center; gap:8px; }
.val-hl { color:var(--text-1); font-weight:500; font-family:'IBM Plex Mono',monospace; }
.echart { width:100%; height:250px; }
.echart-large { width:100%; height:340px; }
.sortable-th { cursor:pointer; user-select:none; }
.sortable-th:hover { color:#fff; }
.badge-row { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px; }
.stat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; }
.stat-box { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px 12px; }
.stat-box .val { font-family:'IBM Plex Mono',monospace; font-size:22px; font-weight:600; color:var(--text-1); }
.stat-box .lbl { font-size:11px; color:var(--text-2); margin-top:4px; }
.stat-box .sub { font-size:12px; color:var(--text-3); margin-top:2px; }
.delta-pos { color:var(--up); }
.delta-neg { color:var(--dn); }
.open-bar { display:flex; border-radius:6px; overflow:hidden; height:18px; margin-top:6px; }
.open-bar .seg { height:100%; }
</style>
<script>
(function(){
  var t=localStorage.getItem("theme");
  if(t==="light") document.documentElement.setAttribute("data-theme","light");
})();
</script>
</head>
<body>

<header class="app-bar">
  <div style="display:flex;align-items:center;">
    <a href="index.html" class="brand" style="margin-right:0;">
      <svg class="prsh-logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke-width="2"></path>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke-width="2"></polyline>
        <line x1="12" y1="22.08" x2="12" y2="12" stroke-width="2"></line>
      </svg>
      Prsh <span style="font-weight:400;color:var(--text-3);margin-left:4px;">Capital</span>
    </a>
    <div style="display:flex;gap:6px;margin-left:12px;">
      <button id="themeToggleBtn" style="background:transparent;border:none;cursor:pointer;color:var(--text-2);margin-right:8px;display:flex;align-items:center;justify-content:center;padding:4px;transition:color 0.2s;" onmouseover="this.style.color='var(--text-1)'" onmouseout="this.style.color='var(--text-2)'" title="Toggle Theme">
        <svg id="themeIconSun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;display:none;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        <svg id="themeIconMoon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;display:none;"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
      </button>
      <button class="time-badge">PDR</button>
      <button class="asset-badge">CONTRACTED</button>
    </div>
  </div>
</header>

<div class="container" style="padding-top:24px;max-width:940px;padding-bottom:100px;">

  <!-- ═══ SECTION 1: GAP OPEN STATS ═══ -->
  <div class="section-header">
    <div class="dot" style="background:var(--warm)"></div> Open Position Stats
    <span style="font-size:12px;color:var(--text-2);font-weight:400;margin-left:4px;">How often does next day open inside / outside the PDR?</span>
  </div>

  <div class="card" style="margin-bottom:16px;">
    <div class="card-header"><div class="card-title">Day Open Position (Both NQ &amp; ES)</div></div>
    <div class="card-body">
      <div id="openStatsBar" style="margin-bottom:16px;"></div>
      <div class="card-body dense table-wrap" style="margin-top:0;padding:0;">
        <table>
          <thead><tr>
            <th>Scenario</th>
            <th class="r">N</th>
            <th class="r">In Orig PDR</th>
            <th class="r">In Contracted</th>
            <th class="r">Gap Open</th>
            <th class="r">Gap %</th>
          </tr></thead>
          <tbody id="openStatsTbody"></tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <div style="font-size:12px;color:var(--text-2);margin-bottom:8px;font-weight:500;">Gap Open % by Weekday</div>
        <div id="gapByWdChart" class="echart"></div>
      </div>
    </div>
  </div>

  <!-- ═══ SECTION 2: SCENARIO SELECTOR ═══ -->
  <div class="section-header" style="margin-top:32px;">
    <div class="dot" style="background:var(--accent)"></div> Break Probabilities &amp; Extensions
  </div>

  <div class="card" style="margin-bottom:16px;">
    <div class="card-header">
      <div class="card-title">Scenario</div>
      <div class="segments-scroll"><div class="segments" id="segOffset">
        <button class="active" data-v="off0">0% (Original)</button>
        <button data-v="off10">10% Contracted</button>
        <button data-v="off20">20% Contracted</button>
      </div></div>
      <div class="segments-scroll" style="margin-top:6px;"><div class="segments" id="segOpen">
        <button class="active" data-v="all">All Sessions</button>
        <button data-v="open_in_orig">Open in PDR</button>
        <button data-v="open_in_cont">Open in Contracted</button>
        <button data-v="open_out_orig">Gap Open</button>
      </div></div>
    </div>
    <div class="card-body">
      <div id="scenarioLabel" style="font-size:12px;color:var(--text-2);margin-bottom:12px;"></div>
      <div class="stat-grid" id="statGrid"></div>
    </div>
  </div>

  <!-- ═══ SECTION 3: PROB CHART + TABLE ═══ -->
  <div class="grid grid-2">
    <div class="card" style="grid-column:1/-1;">
      <div class="card-header"><div class="card-title">Break Outcomes</div></div>
      <div class="card-body dense table-wrap" style="display:flex;gap:24px;flex-wrap:wrap;">
        <div id="chartProb" class="echart" style="flex:1;min-width:280px;"></div>
        <div style="flex:1;min-width:280px;display:flex;align-items:center;">
          <table style="margin-top:0;width:100%;">
            <thead><tr><th>Outcome</th><th class="r">NQ</th><th class="r">ES</th></tr></thead>
            <tbody id="probBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══ SECTION 4: EXTENSION CDF + TABLE ═══ -->
  <div class="section-header" style="margin-top:32px;">
    <div class="dot" style="background:var(--up)"></div> R-Multiple Extension Matrix
    <span style="font-size:12px;color:var(--text-2);font-weight:400;margin-left:4px;">(in contracted PDR units)</span>
  </div>

  <div class="grid">
    <div class="card" style="grid-column:1/-1;">
      <div class="card-header">
        <div class="card-title">Extension CDF Curve</div>
        <div class="segments-scroll"><div class="segments" id="segBreak">
          <button class="active" data-v="all_breaks">All Breaks</button>
          <button data-v="single_break">Single Break</button>
          <button data-v="double_break">Double Break</button>
        </div></div>
        <div class="segments-scroll"><div class="segments" id="segDay">
          <button class="active" data-v="All">All Days</button>
          <button data-v="Monday">Mon</button>
          <button data-v="Tuesday">Tue</button>
          <button data-v="Wednesday">Wed</button>
          <button data-v="Thursday">Thu</button>
          <button data-v="Friday">Fri</button>
        </div></div>
        <div class="segments-scroll"><div class="segments" id="segDir">
          <button class="active" data-v="Combined">Combined</button>
          <button data-v="Up">Upside</button>
          <button data-v="Down">Downside</button>
        </div></div>
      </div>
      <div class="card-body">
        <div id="chartCurve" class="echart-large"></div>
      </div>
    </div>

    <div class="card" style="grid-column:1/-1;">
      <div class="card-header" style="padding-bottom:0;">
        <div class="card-title">Extension Percentiles Table</div>
        <div style="font-size:11px;color:var(--text-2);font-weight:500;margin-top:4px;">Click column header to sort</div>
      </div>
      <div class="card-body dense table-wrap" style="margin-top:8px;">
        <table>
          <thead>
            <tr>
              <th class="sortable-th" data-sort="day">Asset / Slice</th>
              <th class="r sortable-th" data-sort="p10">10%</th>
              <th class="r sortable-th" data-sort="p25">25%</th>
              <th class="r sortable-th" data-sort="p50">50%</th>
              <th class="r sortable-th" data-sort="p75">75%</th>
              <th class="r sortable-th" data-sort="p90">90%</th>
              <th class="r sortable-th" data-sort="max">Max</th>
            </tr>
          </thead>
          <tbody id="extTBody"></tbody>
        </table>
      </div>
    </div>
  </div>

</div><!-- /container -->

<script>
const _D = DATA_PLACEHOLDER;

// ── helpers ──────────────────────────────────────────────────────────
const themeColors = {nq:'#6366f1', es:'#10b981', text:'#888', grid:'#1f1f1f'};
const commonOpts = {
  backgroundColor:'transparent',
  tooltip:{trigger:'axis', backgroundColor:'#141414', borderColor:'#333', textStyle:{color:'#fff'}},
  legend:{textStyle:{color:themeColors.text}, bottom:0},
  grid:{left:'4%', right:'5%', bottom:'10%', top:'15%', containLabel:true}
};

// ── state ─────────────────────────────────────────────────────────────
let curOffset = 'off0';
let curOpen   = 'all';
let curBreak  = 'all_breaks';
let curDay    = 'All';
let curDir    = 'Combined';
let sortCol   = 'day';
let sortDesc  = false;

function scenarioKey() { return `${curOffset}_${curOpen}`; }
function getScenario() { return _D.scenarios[scenarioKey()]; }

// ── Open Stats Section ────────────────────────────────────────────────
function renderOpenStats() {
  const offKeys = ['off0','off10','off20'];
  const offLabels = ['0% (Original)','10% Contracted','20% Contracted'];
  const colors = {in_orig:'#6366f1', in_cont:'#10b981', gap:'#f59e0b'};

  // Table
  let html = '';
  offKeys.forEach((k, i) => {
    const s = _D.open_stats[k];
    const gapCls = s.gap_open_pct > 50 ? 'val-hl' : '';
    html += `<tr>
      <td><b>${offLabels[i]}</b></td>
      <td class="r">${s.total.toLocaleString()}</td>
      <td class="r val-hl" style="color:var(--accent)">${s.in_orig.toLocaleString()} (${s.in_orig_pct}%)</td>
      <td class="r val-hl" style="color:var(--up)">${s.in_cont.toLocaleString()} (${s.in_cont_pct}%)</td>
      <td class="r val-hl" style="color:var(--warm)">${s.gap_open.toLocaleString()} (${s.gap_open_pct}%)</td>
      <td class="r ${gapCls}">${s.gap_open_pct}%</td>
    </tr>`;
  });
  document.getElementById('openStatsTbody').innerHTML = html;

  // Gap by weekday bar chart
  const wds = ['Monday','Tuesday','Wednesday','Thursday','Friday'];
  const wdShort = ['Mon','Tue','Wed','Thu','Fri'];
  const chart = echarts.init(document.getElementById('gapByWdChart'));
  const series = offKeys.map((k, ki) => ({
    name: offLabels[ki],
    type: 'bar',
    barGap: '5%',
    itemStyle: {color: [themeColors.nq, themeColors.es, '#f59e0b'][ki], borderRadius:[3,3,0,0]},
    data: wds.map(wd => _D.open_stats[k].by_weekday[wd].gap_pct)
  }));
  chart.setOption({
    ...commonOpts,
    xAxis:{type:'category', data:wdShort, axisLabel:{color:themeColors.text}},
    yAxis:{type:'value', axisLabel:{color:themeColors.text, formatter:'{value}%'}, splitLine:{lineStyle:{color:themeColors.grid}}, max:80},
    series
  });
}

// ── Stat Grid ─────────────────────────────────────────────────────────
function renderStatGrid() {
  const sc = getScenario();
  if(!sc) return;
  const p = sc.prob['All'];
  if(!p || !p.nq) return;
  const off = curOffset==='off0'?'0%':curOffset==='off10'?'10%':'20%';
  const openLbl = {all:'All Sessions',open_in_orig:'Open in PDR',open_in_cont:'Open in Contracted',open_out_orig:'Gap Open'}[curOpen];
  document.getElementById('scenarioLabel').textContent =
    `Contraction: ${off} each side  |  Filter: ${openLbl}  |  N = ${p.n.toLocaleString()} sessions`;

  const items = [
    {lbl:'NQ Break %',   val:p.nq.atleast_one+'%', sub:`Single ${p.nq.single}%`, clr:'var(--accent)'},
    {lbl:'NQ Double %',  val:p.nq.double+'%',       sub:`Inside ${p.nq.inside}%`,  clr:'var(--dn)'},
    {lbl:'ES Break %',   val:p.es.atleast_one+'%', sub:`Single ${p.es.single}%`, clr:'var(--up)'},
    {lbl:'ES Double %',  val:p.es.double+'%',       sub:`Inside ${p.es.inside}%`,  clr:'var(--dn)'},
  ];
  // Add P50 extension
  const ext = sc.ext;
  const nqP50 = ext.nq.all_breaks['All'].Combined.table_vals.p50;
  const esP50 = ext.es.all_breaks['All'].Combined.table_vals.p50;
  items.push({lbl:'NQ P50 Ext', val:(nqP50||0)+'R', sub:'All breaks combined', clr:'var(--text-1)'});
  items.push({lbl:'ES P50 Ext', val:(esP50||0)+'R', sub:'All breaks combined', clr:'var(--text-1)'});

  document.getElementById('statGrid').innerHTML = items.map(it=>
    `<div class="stat-box">
      <div class="val" style="color:${it.clr}">${it.val}</div>
      <div class="lbl">${it.lbl}</div>
      <div class="sub">${it.sub}</div>
    </div>`
  ).join('');
}

// ── Prob Chart ────────────────────────────────────────────────────────
const chartProb = echarts.init(document.getElementById('chartProb'));
function renderProb() {
  const sc = getScenario();
  if(!sc) return;
  const p = sc.prob['All'];
  if(!p) return;
  chartProb.setOption({
    ...commonOpts,
    tooltip:{trigger:'item', backgroundColor:'#141414', borderColor:'#333', textStyle:{color:'#fff'}, formatter:'{a}<br/>{b}: {c}%'},
    xAxis:{type:'category', data:['Atleast One','Single','Double','Inside'], axisLabel:{color:themeColors.text, fontSize:10, interval:0}},
    yAxis:{type:'value', splitLine:{lineStyle:{color:themeColors.grid}}, axisLabel:{color:themeColors.text, formatter:'{value}%'}, max:100},
    series:[
      {name:'NQ', type:'bar', itemStyle:{color:themeColors.nq, borderRadius:[4,4,0,0]}, data:[p.nq.atleast_one, p.nq.single, p.nq.double, p.nq.inside]},
      {name:'ES', type:'bar', itemStyle:{color:themeColors.es, borderRadius:[4,4,0,0]}, data:[p.es.atleast_one, p.es.single, p.es.double, p.es.inside]},
    ]
  });
  document.getElementById('probBody').innerHTML = `
    <tr><td>Atleast One Break</td><td class="r val-hl" style="color:var(--accent)">${p.nq.atleast_one}%</td><td class="r val-hl" style="color:var(--up)">${p.es.atleast_one}%</td></tr>
    <tr><td>Single Break</td><td class="r val-hl">${p.nq.single}%</td><td class="r val-hl">${p.es.single}%</td></tr>
    <tr><td>Double Break</td><td class="r val-hl" style="color:var(--dn)">${p.nq.double}%</td><td class="r val-hl" style="color:var(--dn)">${p.es.double}%</td></tr>
    <tr><td>Inside (No Break)</td><td class="r val-hl" style="color:var(--text-2)">${p.nq.inside}%</td><td class="r val-hl" style="color:var(--text-2)">${p.es.inside}%</td></tr>
  `;
}

// ── CDF Curve ─────────────────────────────────────────────────────────
const chartCurve = echarts.init(document.getElementById('chartCurve'));
function renderCurve() {
  const sc = getScenario();
  if(!sc) return;
  const nqD = sc.ext.nq[curBreak]?.[curDay]?.[curDir] || {probs:[],vals:[]};
  const esD = sc.ext.es[curBreak]?.[curDay]?.[curDir] || {probs:[],vals:[]};
  chartCurve.setOption({
    ...commonOpts,
    tooltip:{trigger:'axis', formatter:function(params){
      let s=`P(reach): <b>${params[0].axisValue}</b><br/>`;
      params.forEach(p=>s+=`${p.marker}${p.seriesName}: ${p.value}R<br/>`);
      return s;
    }, backgroundColor:'#141414', borderColor:'#333', textStyle:{color:'#fff'}},
    xAxis:{type:'category', boundaryGap:false, data:nqD.probs.map(p=>p===0?'0%(Max)':p+'%'), axisLabel:{color:themeColors.text, fontSize:10}, name:'Probability (%)', nameLocation:'middle', nameGap:28},
    yAxis:{type:'value', name:'R-Multiple Extension', nameTextStyle:{color:themeColors.text, padding:[0,0,10,0]}, splitLine:{lineStyle:{color:themeColors.grid}}, axisLabel:{color:themeColors.text}},
    series:[
      {name:'NQ', type:'line', smooth:true, lineStyle:{width:3}, itemStyle:{color:themeColors.nq}, data:nqD.vals, areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(99,102,241,0.3)'},{offset:1,color:'rgba(99,102,241,0)'}])}},
      {name:'ES', type:'line', smooth:true, lineStyle:{width:3}, itemStyle:{color:themeColors.es}, data:esD.vals, areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(16,185,129,0.3)'},{offset:1,color:'rgba(16,185,129,0)'}])}},
    ]
  }, true);
  renderTable();
}

// ── Percentile Table ──────────────────────────────────────────────────
function renderTable() {
  const sc = getScenario();
  if(!sc) return;
  const days = ['All','Monday','Tuesday','Wednesday','Thursday','Friday'];
  let rows = [];
  days.forEach(d=>{
    ['nq','es'].forEach(asset=>{
      const t = sc.ext[asset]?.[curBreak]?.[d]?.[curDir]?.table_vals;
      if(t && Object.keys(t).length) rows.push({asset:asset.toUpperCase(), day:d, ...t});
    });
  });
  if(sortCol==='day'){
    rows.sort((a,b)=>{ let r=a.day.localeCompare(b.day)||a.asset.localeCompare(b.asset); return sortDesc?-r:r; });
  } else {
    rows.sort((a,b)=>{ let r=(a[sortCol]||0)-(b[sortCol]||0); return sortDesc?-r:r; });
  }
  let html='';
  rows.forEach(r=>{
    const nameHtml = r.day==='All'?`<b>${r.asset} (${r.day})</b>`:`${r.asset} (${r.day})`;
    const color = r.asset==='NQ'?themeColors.nq:themeColors.es;
    html+=`<tr>
      <td><span style="color:${color}">${nameHtml}</span></td>
      <td class="r">${r.p10!==undefined?r.p10+'R':'-'}</td>
      <td class="r">${r.p25!==undefined?r.p25+'R':'-'}</td>
      <td class="r val-hl">${r.p50!==undefined?r.p50+'R':'-'}</td>
      <td class="r">${r.p75!==undefined?r.p75+'R':'-'}</td>
      <td class="r">${r.p90!==undefined?r.p90+'R':'-'}</td>
      <td class="r" style="color:var(--text-3)">${r.max!==undefined?r.max+'R':'-'}</td>
    </tr>`;
  });
  document.getElementById('extTBody').innerHTML = html;
}

// ── Sortable headers ──────────────────────────────────────────────────
document.querySelectorAll('.sortable-th').forEach(th=>{
  th.addEventListener('click',()=>{
    const col=th.dataset.sort;
    if(sortCol===col){ sortDesc=!sortDesc; }
    else { sortCol=col; sortDesc=(col!=='day'); }
    renderTable();
  });
});

// ── Segment controls ──────────────────────────────────────────────────
function bindSeg(id, onchange) {
  document.querySelectorAll(`#${id} button`).forEach(b=>b.addEventListener('click',e=>{
    document.querySelectorAll(`#${id} button`).forEach(x=>x.classList.remove('active'));
    e.target.classList.add('active');
    onchange(e.target.dataset.v);
  }));
}
bindSeg('segOffset', v=>{ curOffset=v; renderAll(); });
bindSeg('segOpen',   v=>{ curOpen=v;   renderAll(); });
bindSeg('segBreak',  v=>{ curBreak=v;  renderCurve(); });
bindSeg('segDay',    v=>{ curDay=v;    renderCurve(); });
bindSeg('segDir',    v=>{ curDir=v;    renderCurve(); });

function renderAll() {
  renderStatGrid();
  renderProb();
  renderCurve();
}

// ── Init ──────────────────────────────────────────────────────────────
renderOpenStats();
renderAll();

window.addEventListener('resize',()=>{
  chartProb.resize();
  chartCurve.resize();
  echarts.getInstanceByDom(document.getElementById('gapByWdChart'))?.resize();
});
</script>
<script>
document.addEventListener("DOMContentLoaded",function(){
  var btn=document.getElementById("themeToggleBtn");
  if(btn){btn.addEventListener("click",function(){
    var isLight=document.documentElement.getAttribute("data-theme")==="light";
    if(isLight){document.documentElement.removeAttribute("data-theme");localStorage.setItem("theme","dark");}
    else{document.documentElement.setAttribute("data-theme","light");localStorage.setItem("theme","light");}
    if(window.echarts) location.reload();
  });}
});
</script>
</body>
</html>""".replace("DATA_PLACEHOLDER", DATA_STR)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"Written: {OUT_PATH}  ({len(HTML)//1024} KB)")
