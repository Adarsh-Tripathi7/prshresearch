"""
IB Analysis — Institutional Research Terminal v3
Exact color scheme from reference. Apache ECharts. Spotlight search.
"""
import os, csv, json

DATA_DIR = r"d:\Antigravity\Results"
OUT_PATH = r"d:\Antigravity\Dashboard\ib_interactive_dashboard_15m_step.html"

os.makedirs(r"d:\Antigravity\Dashboard", exist_ok=True)

def read_csv_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = []
        for r in reader:
            if not any(c.strip() for c in r): continue
            obj = {}
            for i, h in enumerate(headers):
                val = r[i].strip() if i < len(r) else ""
                try: obj[h] = float(val)
                except ValueError: obj[h] = val
            rows.append(obj)
    return rows

# Load all datasets
prob = read_csv_json("db_probability_by_rth_close_15m_step.csv")
prob_first = read_csv_json("db_probability_by_first_break_15m_step.csv")
corr = read_csv_json("ib_correlation_directional_15m_step.csv")

ext = {}
for asset in ["nq", "es"]:
    ext[asset] = {}
    for btype in ["double_break", "single_break", "all_breaks"]:
        ext[asset][btype] = {}
        for direction in ["combined", "high_first", "low_first"]:
            fname = f"{asset}_{btype}_{direction}_percentiles_15m_step.csv"
            ext[asset][btype][direction] = read_csv_json(fname)

# Serialize data
data_block = json.dumps({"prob": prob, "prob_first": prob_first, "ext": ext, "corr": corr}, separators=(',',':'))

# ── Build HTML ──
# We use __DATA_BLOCK__ as a placeholder and replace it
html_template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>IB Research Terminal (15m step) — NQ & ES</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}

:root {
  --bg: #09090b;
  --bg-raised: #18181b;
  --bg-surface: #27272a;
  --bg-hover: #27272a;
  --bg-active: #3f3f46;
  --border: #27272a;
  --border-strong: #3f3f46;
  --text-1: #fafafa;
  --text-2: #a1a1aa;
  --text-3: #71717a;
  --text-4: #52525b;
  --up: #34d399;
  --up-dim: rgba(52,211,153,0.12);
  --up-text: #6ee7b7;
  --dn: #f87171;
  --dn-dim: rgba(248,113,113,0.12);
  --dn-text: #fca5a5;
  --accent: #818cf8;
  --accent-dim: rgba(129,140,248,0.1);
  --warm: #fbbf24;
  --warm-dim: rgba(251,191,36,0.1);
  --cyan: #38bdf8;
  --cyan-dim: rgba(56,189,248,0.08);
  --font: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --mono: 'IBM Plex Mono', 'Consolas', monospace;
  --radius: 8px;
  --tr: 150ms ease;
}

html{font-size:14px;-webkit-font-smoothing:antialiased}
body{font-family:var(--font);background:var(--bg);color:var(--text-1);overflow-x:hidden;min-height:100vh}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--text-4);border-radius:10px}

/* ── TOPBAR ── */
.topbar{
  position:sticky;top:0;z-index:100;
  background:rgba(18,20,23,0.88);
  backdrop-filter:blur(16px) saturate(1.4);
  border-bottom:1px solid var(--border);
  padding:0 40px;height:52px;
  display:flex;align-items:center;justify-content:space-between;
}
.topbar-left{display:flex;align-items:center;gap:20px}
.brand{font-size:14px;font-weight:600;letter-spacing:-.3px;color:var(--text-1);display:flex;align-items:center;gap:8px}
.brand-dot{width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px rgba(129,140,248,0.4)}
.brand span{color:var(--text-3);font-weight:400}

.topbar-nav{display:flex;gap:2px;background:var(--bg-surface);border-radius:6px;padding:3px}
.topbar-nav button{
  font-family:var(--font);font-size:12px;font-weight:500;
  padding:5px 14px;border:none;border-radius:4px;
  background:transparent;color:var(--text-3);cursor:pointer;transition:var(--tr);
}
.topbar-nav button:hover{color:var(--text-2)}
.topbar-nav button.active{color:var(--text-1);background:var(--bg-hover)}
.topbar-nav button kbd{
  font-family:var(--mono);font-size:9px;color:var(--text-4);
  background:var(--bg);padding:1px 4px;border-radius:3px;margin-left:5px;border:1px solid var(--border);
}

.search-box{position:relative;width:260px}
.search-box input{
  width:100%;padding:6px 12px 6px 30px;
  background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;
  color:var(--text-1);font-family:var(--font);font-size:12px;outline:none;transition:var(--tr);
}
.search-box input:focus{border-color:rgba(129,140,248,0.4);background:var(--bg-raised)}
.search-box input::placeholder{color:var(--text-4)}
.search-box svg{position:absolute;left:9px;top:50%;transform:translateY(-50%);color:var(--text-4)}
.search-box kbd{
  position:absolute;right:8px;top:50%;transform:translateY(-50%);
  font-family:var(--mono);font-size:9px;color:var(--text-4);
  background:var(--bg);padding:1px 5px;border-radius:3px;border:1px solid var(--border);
}

/* ── LAYOUT ── */
.container{max-width:1480px;margin:0 auto;padding:24px 40px}

/* ── SPOTLIGHT ── */
.spotlight{
  display:none;background:var(--bg-raised);border:1px solid var(--border-strong);
  border-radius:var(--radius);padding:20px 24px;margin-bottom:24px;
  animation:slideIn .2s ease;
}
.spotlight.open{display:block}
@keyframes slideIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.spot-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.spot-title{font-size:17px;font-weight:600;letter-spacing:-.3px;display:flex;align-items:center;gap:10px}
.spot-close{
  width:26px;height:26px;display:flex;align-items:center;justify-content:center;
  border:1px solid var(--border);border-radius:5px;background:transparent;
  color:var(--text-3);cursor:pointer;font-size:14px;transition:var(--tr);
}
.spot-close:hover{background:var(--bg-active);color:var(--dn)}
.spot-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.spot-card{background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;padding:14px 16px}
.spot-card-title{font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:var(--text-3);margin-bottom:10px;font-weight:600}
.spot-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0}
.spot-row:not(:last-child){border-bottom:1px solid var(--border)}
.spot-row .lbl{font-size:12px;color:var(--text-2)}
.spot-row .val{font-family:var(--mono);font-size:12px;font-weight:500}

/* ── METRICS ── */
.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--border);border-radius:var(--radius);overflow:hidden;margin-bottom:28px}
.metric{background:var(--bg-raised);padding:18px 20px}
.metric:first-child{border-radius:var(--radius) 0 0 var(--radius)}
.metric:last-child{border-radius:0 var(--radius) var(--radius) 0}
.metric-label{font-size:11px;color:var(--text-3);text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}
.metric-value{font-family:var(--mono);font-size:22px;font-weight:600;letter-spacing:-.5px}
.metric-sub{font-size:11px;color:var(--text-3);margin-top:3px}

/* ── SECTION ── */
.section{margin-bottom:36px;scroll-margin-top:64px}
.section-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.section-title{font-size:14px;font-weight:600;letter-spacing:-.2px;color:var(--text-1);display:flex;align-items:center;gap:8px}
.section-title .count{font-family:var(--mono);font-size:10px;font-weight:500;color:var(--text-3);background:var(--bg-surface);padding:2px 7px;border-radius:4px}
.controls{display:flex;gap:6px;align-items:center}

/* ── SEGMENTS ── */
.seg-group{display:flex;border:1px solid var(--border);border-radius:6px;overflow:hidden}
.seg-group button{
  font-family:var(--font);font-size:11px;font-weight:500;
  padding:5px 12px;border:none;background:var(--bg-raised);
  color:var(--text-3);cursor:pointer;transition:var(--tr);
}
.seg-group button:not(:last-child){border-right:1px solid var(--border)}
.seg-group button:hover{color:var(--text-2);background:var(--bg-surface)}
.seg-group button.active{color:var(--text-1);background:var(--bg-active)}

/* ── TWO COL ── */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.three-col{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px}

/* ── CARD ── */
.card{background:var(--bg-raised);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.card-head{
  padding:10px 16px;border-bottom:1px solid var(--border);
  font-size:12px;font-weight:500;color:var(--text-2);
  display:flex;align-items:center;gap:6px;
}
.card-head .dot{width:5px;height:5px;border-radius:50%}
.card-body{padding:12px 16px}
.card-body.dense{padding:0}
.card-body.scroll{max-height:480px;overflow-y:auto}

/* ── TABLES ── */
.tbl-wrap{max-height:560px;overflow:auto}
table{width:100%;border-collapse:collapse}
thead th{
  position:sticky;top:0;z-index:5;background:var(--bg-surface);
  padding:8px 12px;font-size:10px;font-weight:600;
  text-transform:uppercase;letter-spacing:.5px;color:var(--text-4);
  text-align:left;border-bottom:1px solid var(--border-strong);
  white-space:nowrap;cursor:default;
}
thead th.r{text-align:right}
tbody tr{border-bottom:1px solid var(--border);transition:background var(--tr)}
tbody tr:hover{background:var(--bg-hover)}
tbody tr:last-child{border-bottom:none}
tbody td{padding:6px 12px;font-size:12px;white-space:nowrap}
tbody td.r{text-align:right}
tbody tr.hl{background:var(--accent-dim);box-shadow:inset 2px 0 0 var(--accent)}
tbody tr.clickable{cursor:pointer}
tbody tr.clickable:hover{background:rgba(129,140,248,0.06)}

.c-mono{font-family:var(--mono);font-size:11px}
.c-dim{color:var(--text-3)}
.c-up{color:var(--up-text)}
.c-dn{color:var(--dn-text)}
.c-accent{color:var(--accent)}
.c-warm{color:var(--warm)}

.tag{display:inline-block;font-size:9px;font-weight:600;letter-spacing:.4px;padding:2px 6px;border-radius:3px}
.tag-up{background:var(--up-dim);color:var(--up-text)}
.tag-dn{background:var(--dn-dim);color:var(--dn-text)}
.tag-accent{background:var(--accent-dim);color:var(--accent)}
.tag-cyan{background:var(--cyan-dim);color:var(--cyan)}

/* ── HBAR ── */
.hbar{display:flex;align-items:center;gap:8px;margin-bottom:5px}
.hbar-label{width:90px;flex-shrink:0;font-family:var(--mono);font-size:11px;color:var(--text-2);text-align:right}
.hbar-track{flex:1;height:20px;background:var(--bg-surface);border-radius:3px;overflow:hidden}
.hbar-fill{
  height:100%;border-radius:3px;display:flex;align-items:center;
  padding:0 8px;font-family:var(--mono);font-size:10px;font-weight:500;
  color:rgba(255,255,255,0.85);justify-content:flex-end;
  transition:width .5s cubic-bezier(.4,0,.2,1);
}
.hbar-fill.is-up{background:linear-gradient(90deg,rgba(52,211,153,0.15) 0%,rgba(52,211,153,0.55) 100%)}
.hbar-fill.is-dn{background:linear-gradient(90deg,rgba(248,113,113,0.15) 0%,rgba(248,113,113,0.55) 100%)}
.hbar-fill.is-accent{background:linear-gradient(90deg,rgba(129,140,248,0.15) 0%,rgba(129,140,248,0.55) 100%)}

/* ── CHART ── */
.echart{width:100%;min-height:280px}

/* ── PAGE VISIBILITY ── */
.page{display:none;animation:slideIn .25s ease}
.page.active{display:block}

/* ── RESPONSIVE ── */
@media(max-width:1100px){.two-col,.three-col{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(3,1fr)}}
@media(max-width:768px){.topbar{padding:0 16px}.container{padding:16px}.metrics{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>

<!-- TOPBAR -->
<header class="topbar">
  <div class="topbar-left">
    <div class="brand"><span class="brand-dot"></span>IB Research Terminal <span>&mdash; NQ &amp; ES</span></div>
    <nav class="topbar-nav" id="nav">
      <button class="active" data-p="overview">Overview<kbd>1</kbd></button>
      <button data-p="probability">DB Probability<kbd>2</kbd></button>
      <button data-p="extensions">R Extensions<kbd>3</kbd></button>
      <button data-p="heatmap">Heatmap<kbd>4</kbd></button>
    </nav>
  </div>
  <div class="search-box">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input type="text" id="search" placeholder="Search window... e.g. 09:30" autocomplete="off">
    <kbd>/</kbd>
  </div>
</header>

<!-- SPOTLIGHT -->
<div class="container" style="padding-bottom:0">
  <div class="spotlight" id="spotlight">
    <div class="spot-head">
      <div class="spot-title" id="spotTitle">&mdash;</div>
      <button class="spot-close" id="spotClose">&times;</button>
    </div>
    <div class="spot-grid" id="spotGrid"></div>
  </div>
</div>

<!-- PAGES -->
<div class="container" style="padding-top:0">

<!-- ═══ OVERVIEW ═══ -->
<div class="page active" id="page-overview">
  <div class="metrics" id="kpiStrip"></div>

  <div class="two-col">
    <div class="card">
      <div class="card-head"><span class="dot" style="background:var(--dn)"></span>Double Break Probability — All Windows</div>
      <div class="card-body"><div class="echart" id="chartProb" style="height:340px"></div></div>
    </div>
    <div class="card">
      <div class="card-head"><span class="dot" style="background:var(--up)"></span>Median Extension (50th pctl) — NQ Combined</div>
      <div class="card-body"><div class="echart" id="chartMedExt" style="height:340px"></div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-head">Key Structural Findings</div>
    <div class="card-body">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
        <div style="padding:12px;background:var(--accent-dim);border-radius:6px;border-left:3px solid var(--accent)">
          <div style="font-size:10px;font-weight:600;color:var(--accent);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px">RTH Open Shift</div>
          <div style="font-size:12px;color:var(--text-2);line-height:1.55">09:30–10:29 has <b style="color:var(--up-text)">lowest DB% (~22–28%)</b> — most reliable for breakout continuation.</div>
        </div>
        <div style="padding:12px;background:var(--dn-dim);border-radius:6px;border-left:3px solid var(--dn)">
          <div style="font-size:10px;font-weight:600;color:var(--dn);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px">Asian Fakeouts</div>
          <div style="font-size:12px;color:var(--text-2);line-height:1.55">22:30–00:29 shows <b style="color:var(--warm)">~85–89% DB%</b> — extreme liquidity sweep zone.</div>
        </div>
        <div style="padding:12px;background:var(--up-dim);border-radius:6px;border-left:3px solid var(--up)">
          <div style="font-size:10px;font-weight:600;color:var(--up);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px">Extension Sweet Spot</div>
          <div style="font-size:12px;color:var(--text-2);line-height:1.55">Single-break trends show <b style="color:var(--cyan)">median 4–6R</b> pre-market. Fakeouts rarely exceed 1R.</div>
        </div>
        <div style="padding:12px;background:var(--warm-dim);border-radius:6px;border-left:3px solid var(--warm)">
          <div style="font-size:10px;font-weight:600;color:var(--warm);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px">Directional Asymmetry</div>
          <div style="font-size:12px;color:var(--text-2);line-height:1.55">High-first breaks extend <b style="color:var(--cyan)">further</b> than low-first in Asian session — structural long bias.</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ═══ PROBABILITY ═══ -->
<div class="page" id="page-probability">
  <div class="section-head">
    <div class="section-title">Double Break Probability</div>
    <div class="controls">
      <div class="seg-group" id="segProbDir">
        <button class="active" data-v="combined">Combined</button>
        <button data-v="high_first">High First</button>
        <button data-v="low_first">Low First</button>
      </div>
    </div>
  </div>
  <div class="two-col">
    <div class="card" style="grid-column:1/2">
      <div class="card-head"><span class="dot" style="background:var(--accent)"></span>Double Break Probability by Window</div>
      <div class="card-body"><div class="echart" id="chartProbFull" style="height:440px"></div></div>
    </div>
    <div class="card">
      <div class="card-head">Raw Data</div>
      <div class="card-body dense scroll"><div class="tbl-wrap"><table><thead><tr>
        <th>Window</th><th class="r">NQ DB%</th><th class="r">ES DB%</th><th class="r">Avg</th><th class="r">Δ</th>
      </tr></thead><tbody id="tblProb"></tbody></table></div></div>
    </div>
  </div>
</div>

<!-- ═══ R EXTENSIONS ═══ -->
<div class="page" id="page-extensions">
  <div class="section-head">
    <div class="section-title">R-Multiple Extensions <span class="count" id="extCount">—</span></div>
    <div class="controls">
      <div class="seg-group" id="segAsset">
        <button class="active" data-v="nq">NQ</button>
        <button data-v="es">ES</button>
      </div>
      <div class="seg-group" id="segBreak">
        <button class="active" data-v="double_break">Double Break</button>
        <button data-v="single_break">Single Break</button>
        <button data-v="all_breaks">All Breaks</button>
      </div>
      <div class="seg-group" id="segDir">
        <button class="active" data-v="combined">Combined</button>
        <button data-v="high_first">High First</button>
        <button data-v="low_first">Low First</button>
      </div>
    </div>
  </div>

  <div class="two-col">
    <div class="card">
      <div class="card-head" id="extCdfHead"><span class="dot" style="background:var(--accent)"></span>CDF — Select a window</div>
      <div class="card-body"><div class="echart" id="chartCdf" style="height:300px"></div></div>
    </div>
    <div class="card">
      <div class="card-head" id="extBarHead"><span class="dot" style="background:var(--warm)"></span>50th Percentile — All Windows</div>
      <div class="card-body">
        <div style="display:flex;gap:6px;margin-bottom:10px;align-items:center">
          <span style="font-size:10px;font-weight:600;color:var(--text-3);text-transform:uppercase;letter-spacing:.4px">Percentile</span>
          <select id="selPct" style="font-family:var(--font);font-size:11px;background:var(--bg-surface);color:var(--text-1);border:1px solid var(--border);border-radius:5px;padding:4px 24px 4px 8px;cursor:pointer;appearance:none;background-image:url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2710%27 height=%2710%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%235e626e%27 stroke-width=%272%27%3E%3Cpath d=%27M6 9l6 6 6-6%27/%3E%3C/svg%3E');background-repeat:no-repeat;background-position:right 6px center;outline:none"></select>
        </div>
        <div class="echart" id="chartBar" style="height:260px"></div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-head" id="extTblHead">Full Percentile Matrix</div>
    <div class="card-body dense scroll" style="max-height:320px">
      <div class="tbl-wrap"><table><thead id="extTHead"></thead><tbody id="extTBody"></tbody></table></div>
    </div>
  </div>
</div>

<!-- ═══ HEATMAP ═══ -->
<div class="page" id="page-heatmap">
  <div class="section-head">
    <div class="section-title" id="hmTitle">Heatmap Explorer</div>
    <div class="controls">
      <div class="seg-group" id="segHmType">
        <button class="active" data-v="ext_ab">All Breaks Ext</button>
        <button data-v="corr">First Side Same Break Prob</button>
      </div>
      <div class="seg-group" id="segHmAsset">
        <button class="active" data-v="nq">NQ</button>
        <button data-v="es">ES</button>
      </div>
      <div class="seg-group" id="segHmDir">
        <button class="active" data-v="combined">Combined</button>
        <button data-v="high_first">High First</button>
        <button data-v="low_first">Low First</button>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-body"><div class="echart" id="chartHeatmap" style="height:620px"></div></div>
  </div>
</div>

</div><!-- container -->

<script>
// ═══════════════════════════════════════════
// DATA INJECTION
// ═══════════════════════════════════════════
const _D = __DATA_BLOCK__;
const probData = _D.prob;
const corrData = _D.corr;
const EXT = _D.ext;
const PCT = ['5%','10%','15%','20%','25%','30%','35%','40%','45%','50%','55%','60%','65%','70%','75%','80%','85%','90%','95%','100%'];

// ═══════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════
const $=id=>document.getElementById(id);
const $$=(s,c)=>(c||document).querySelectorAll(s);

function initSeg(id,cb){
  $(id).querySelectorAll('button').forEach(b=>{
    b.addEventListener('click',()=>{
      $(id).querySelectorAll('button').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      if(cb)cb(b.dataset.v);
    });
  });
}
function segVal(id){const a=$(id).querySelector('button.active');return a?a.dataset.v:''}

// ECharts factory
const charts={};
function ec(id){
  if(!charts[id]){charts[id]=echarts.init($(id),null,{renderer:'canvas'});window.addEventListener('resize',()=>charts[id].resize())}
  return charts[id];
}
function resizeAll(){Object.values(charts).forEach(c=>c.resize())}

// Shared tooltip style
const TT={backgroundColor:'#18181b',borderColor:'#3f3f46',textStyle:{fontFamily:'IBM Plex Mono',fontSize:11,color:'#fafafa'},padding:[8,12],extraCssText:'border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,.4)'};
const AXIS_STYLE={axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisTick:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisLabel:{fontFamily:'IBM Plex Mono',fontSize:10,color:'#5e626e'},splitLine:{lineStyle:{color:'rgba(255,255,255,0.04)',type:'dashed'}}};

// ═══════════════════════════════════════════
// NAV + KEYBOARD
// ═══════════════════════════════════════════
const pages=['overview','probability','extensions','heatmap'];
function goTo(name){
  $$('#nav button').forEach(b=>b.classList.remove('active'));
  $$('.page').forEach(p=>p.classList.remove('active'));
  const btn=document.querySelector(`#nav button[data-p="${name}"]`);
  if(btn)btn.classList.add('active');
  const pg=$('page-'+name);
  if(pg){pg.classList.add('active');setTimeout(resizeAll,80)}
}
$$('#nav button').forEach(b=>b.addEventListener('click',()=>goTo(b.dataset.p)));
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT')return;
  const n=parseInt(e.key);
  if(n>=1&&n<=pages.length){e.preventDefault();goTo(pages[n-1])}
  if(e.key==='/'){e.preventDefault();$('search').focus()}
});

// ═══════════════════════════════════════════
// SEARCH + SPOTLIGHT
// ═══════════════════════════════════════════
$('search').addEventListener('input',function(){
  const q=this.value.trim().toLowerCase().replace(/:/g, '');
  const spot=$('spotlight');
  if(!q){spot.classList.remove('open');$$('tbody tr.hl').forEach(r=>r.classList.remove('hl'));return}
  // Highlight matching rows
  $$('tbody tr').forEach(r=>{
    const td=r.querySelector('td');
    if(td&&td.textContent.toLowerCase().replace(/:/g, '').includes(q))r.classList.add('hl');
    else r.classList.remove('hl');
  });
  // Show spotlight for exact window match
  const matchWin=probData.find(d=>d.Window.toLowerCase().replace(/:/g, '').includes(q));
  if(matchWin){
    spot.classList.add('open');
    showSpotlight(matchWin.Window);
  }else{spot.classList.remove('open')}
});
$('search').addEventListener('keydown',e=>{if(e.key==='Escape'){$('search').value='';$('search').blur();$('spotlight').classList.remove('open');$$('tbody tr.hl').forEach(r=>r.classList.remove('hl'))}});
$('spotClose').addEventListener('click',()=>{$('spotlight').classList.remove('open');$('search').value='';$$('tbody tr.hl').forEach(r=>r.classList.remove('hl'))});

function showSpotlight(win){
  $('spotTitle').innerHTML=`<span style="color:var(--accent)">⏱</span> ${win}`;
  const p=probData.find(d=>d.Window===win);
  let html='';

  // DB probability card
  if(p){
    html+=`<div class="spot-card"><div class="spot-card-title">Double Break Probability</div>
      <div class="spot-row"><span class="lbl">NQ DB%</span><span class="val c-dn">${p.NQ_DB_Prob.toFixed(1)}%</span></div>
      <div class="spot-row"><span class="lbl">ES DB%</span><span class="val c-dn">${p.ES_DB_Prob.toFixed(1)}%</span></div>
      <div class="spot-row"><span class="lbl">Average</span><span class="val c-accent">${((p.NQ_DB_Prob+p.ES_DB_Prob)/2).toFixed(1)}%</span></div>
    </div>`;
  }

  // Extension cards for NQ combined
  for(const asset of ['nq','es']){
    for(const brk of ['double_break','single_break','all_breaks']){
      const d=EXT[asset]?.[brk]?.combined;
      if(!d)continue;
      const row=d.find(r=>r.Window===win);
      if(!row)continue;
      const label=`${asset.toUpperCase()} ${brk==='double_break'?'DB':'SB'} Extension (Combined)`;
      html+=`<div class="spot-card"><div class="spot-card-title">${label}</div>
        <div class="spot-row"><span class="lbl">25th pctl</span><span class="val" style="color:var(--up-text)">${row['25%']?.toFixed(2)||'—'}R</span></div>
        <div class="spot-row"><span class="lbl">Median</span><span class="val" style="color:var(--warm)">${row['50%']?.toFixed(2)||'—'}R</span></div>
        <div class="spot-row"><span class="lbl">75th pctl</span><span class="val" style="color:var(--dn-text)">${row['75%']?.toFixed(2)||'—'}R</span></div>
        <div class="spot-row"><span class="lbl">90th pctl</span><span class="val" style="color:var(--accent)">${row['90%']?.toFixed(2)||'—'}R</span></div>
      </div>`;
    }
  }

  // Direction-specific
  for(const dir of ['high_first','low_first']){
    const d=EXT.nq?.double_break?.[dir];
    if(!d)continue;
    const row=d.find(r=>r.Window===win);
    if(!row)continue;
    const label=`NQ DB ${dir==='high_first'?'↑ High First':'↓ Low First'}`;
    html+=`<div class="spot-card"><div class="spot-card-title">${label}</div>
      <div class="spot-row"><span class="lbl">Median</span><span class="val" style="color:var(--warm)">${row['50%']?.toFixed(2)||'—'}R</span></div>
      <div class="spot-row"><span class="lbl">75th pctl</span><span class="val" style="color:var(--dn-text)">${row['75%']?.toFixed(2)||'—'}R</span></div>
      <div class="spot-row"><span class="lbl">90th pctl</span><span class="val" style="color:var(--accent)">${row['90%']?.toFixed(2)||'—'}R</span></div>
    </div>`;
  }

  $('spotGrid').innerHTML=html;
}

// ═══════════════════════════════════════════
// OVERVIEW
// ═══════════════════════════════════════════
(function(){
  const labels=probData.map(d=>d.Window);
  const nq=probData.map(d=>d.NQ_DB_Prob);
  const es=probData.map(d=>d.ES_DB_Prob);
  let minP=100,maxP=0,minW='',maxW='';
  probData.forEach(d=>{const a=(d.NQ_DB_Prob+d.ES_DB_Prob)/2;if(a<minP){minP=a;minW=d.Window}if(a>maxP){maxP=a;maxW=d.Window}});

  $('kpiStrip').innerHTML=`
    <div class="metric"><div class="metric-label">Windows Analyzed</div><div class="metric-value" style="color:var(--text-1)">81</div><div class="metric-sub">15m rolling | 15m step</div></div>
    <div class="metric"><div class="metric-label">Lowest DB%</div><div class="metric-value" style="color:var(--up)">${minP.toFixed(1)}%</div><div class="metric-sub">${minW}</div></div>
    <div class="metric"><div class="metric-label">Highest DB%</div><div class="metric-value" style="color:var(--dn)">${maxP.toFixed(1)}%</div><div class="metric-sub">${maxW}</div></div>
    <div class="metric"><div class="metric-label">DB% Spread</div><div class="metric-value" style="color:var(--warm)">${(maxP-minP).toFixed(1)}pp</div><div class="metric-sub">Range across all windows</div></div>
    <div class="metric"><div class="metric-label">Total Datasets</div><div class="metric-value" style="color:var(--accent)">12</div><div class="metric-sub">2 assets × 2 types × 3 dirs</div></div>
  `;

  // Prob chart
  ec('chartProb').setOption({
    tooltip:{...TT,trigger:'axis',formatter:ps=>{let s=`<b style="color:#ececef">${ps[0].axisValue}</b><br>`;ps.forEach(p=>s+=`<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(1)}%</b><br>`);return s}},
    legend:{top:6,right:10,textStyle:{fontFamily:'DM Sans',fontSize:11,color:'#5e626e'},itemWidth:14,itemHeight:3},
    grid:{top:36,right:12,bottom:32,left:48},
    xAxis:{...AXIS_STYLE,type:'category',data:labels,axisLabel:{...AXIS_STYLE.axisLabel,rotate:45}},
    yAxis:{...AXIS_STYLE,type:'value',name:'DB%',nameTextStyle:{fontSize:10,color:'#5e626e'}},
    series:[
      {name:'NQ',type:'line',data:nq,smooth:.3,symbol:'none',lineStyle:{width:2,color:'#818cf8'},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(129,140,248,.15)'},{offset:1,color:'rgba(129,140,248,0)'}]}}},
      {name:'ES',type:'line',data:es,smooth:.3,symbol:'none',lineStyle:{width:2,color:'#38bdf8'},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(56,189,248,.12)'},{offset:1,color:'rgba(56,189,248,0)'}]}}}
    ]
  });

  // Med extension
  const nqDB=EXT.nq.double_break.combined;
  const nqSB=EXT.nq.single_break.combined;
  ec('chartMedExt').setOption({
    tooltip:{...TT,trigger:'axis',formatter:ps=>ps.map(p=>`<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)}R</b>`).join('<br>')},
    legend:{top:6,right:10,textStyle:{fontFamily:'DM Sans',fontSize:11,color:'#5e626e'},itemWidth:14,itemHeight:10},
    grid:{top:36,right:12,bottom:32,left:48},
    xAxis:{...AXIS_STYLE,type:'category',data:nqDB.map(d=>d.Window),axisLabel:{...AXIS_STYLE.axisLabel,rotate:45}},
    yAxis:{...AXIS_STYLE,type:'value',name:'R'},
    series:[
      {name:'Double Break',type:'bar',data:nqDB.map(d=>d['50%']),itemStyle:{color:'rgba(248,113,113,.5)',borderRadius:[3,3,0,0]},barMaxWidth:10},
      {name:'Single Break',type:'bar',data:nqSB.map(d=>d['50%']),itemStyle:{color:'rgba(52,211,153,.5)',borderRadius:[3,3,0,0]},barMaxWidth:10}
    ]
  });
})();

// ═══════════════════════════════════════════
// PROBABILITY
// ═══════════════════════════════════════════
function updateProb() {
  const dir = segVal('segProbDir') || 'combined';
  const data = dir === 'combined' ? probData : _D.prob_first;
  if (!data || !data.length) return;
  const labels = data.map(d=>d.Window);
  let nq, es;
  if (dir === 'combined') {
    nq = data.map(d=>d.NQ_DB_Prob);
    es = data.map(d=>d.ES_DB_Prob);
  } else if (dir === 'high_first') {
    nq = data.map(d=>d.NQ_H_First_DB_Prob);
    es = data.map(d=>d.ES_H_First_DB_Prob);
  } else {
    nq = data.map(d=>d.NQ_L_First_DB_Prob);
    es = data.map(d=>d.ES_L_First_DB_Prob);
  }
  ec('chartProbFull').setOption({
    tooltip:{...TT,trigger:'axis',formatter:ps=>{let s=`<b style="color:#ececef">${ps[0].axisValue}</b><br>`;ps.forEach(p=>{if(p.seriesName!=='50%')s+=`<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(1)}%</b><br>`});return s}},
    legend:{top:6,right:10,textStyle:{fontFamily:'DM Sans',fontSize:11,color:'#5e626e'},itemWidth:14,itemHeight:3},
    grid:{top:36,right:12,bottom:32,left:48},
    dataZoom:[{type:'inside'}],
    xAxis:{...AXIS_STYLE,type:'category',data:labels,axisLabel:{...AXIS_STYLE.axisLabel,rotate:45,fontSize:11}},
    yAxis:{...AXIS_STYLE,type:'value',min:0,max:100,name:'%'},
    series:[
      {name:'NQ DB%',type:'line',data:nq,smooth:.25,symbol:'circle',symbolSize:4,lineStyle:{width:2.5,color:'#818cf8'},itemStyle:{color:'#818cf8'},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(129,140,248,.14)'},{offset:1,color:'rgba(129,140,248,0)'}]}}},
      {name:'ES DB%',type:'line',data:es,smooth:.25,symbol:'circle',symbolSize:4,lineStyle:{width:2.5,color:'#38bdf8'},itemStyle:{color:'#38bdf8'},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(56,189,248,.12)'},{offset:1,color:'rgba(56,189,248,0)'}]}}},
      {name:'50%',type:'line',data:labels.map(()=>50),lineStyle:{width:1,color:'#3e814c',type:'dashed'},symbol:'none',silent:true}
    ]
  }, true);
  // Table
  let h='';
  data.forEach(d=>{
    const n = dir === 'combined' ? d.NQ_DB_Prob : (dir === 'high_first' ? d.NQ_H_First_DB_Prob : d.NQ_L_First_DB_Prob);
    const e = dir === 'combined' ? d.ES_DB_Prob : (dir === 'high_first' ? d.ES_H_First_DB_Prob : d.ES_L_First_DB_Prob);
    if(n===undefined || e===undefined) return;
    const avg=(n+e)/2;
    const delta=n-e;
    const dc=delta>0?'c-dn':'c-up';
    const bg=avg>75?'var(--dn-dim)':avg<35?'var(--up-dim)':'transparent';
    h+=`<tr style="background:${bg}"><td class="c-mono">${d.Window}</td><td class="r c-mono">${n.toFixed(1)}</td><td class="r c-mono">${e.toFixed(1)}</td><td class="r c-mono">${avg.toFixed(1)}</td><td class="r c-mono ${dc}">${delta>0?'+':''}${delta.toFixed(1)}</td></tr>`;
  });
  $('tblProb').innerHTML=h;
}
if($('segProbDir')) initSeg('segProbDir', updateProb);
updateProb();

// ═══════════════════════════════════════════
// R EXTENSIONS
// ═══════════════════════════════════════════
let extWin=0,extPct='50%';

function extData(){return EXT[segVal('segAsset')]?.[segVal('segBreak')]?.[segVal('segDir')]||[]}

function initPctSel(){
  const s=$('selPct');if(s.children.length)return;
  PCT.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;if(p==='50%')o.selected=true;s.appendChild(o)});
}

function updateExt(){
  let d=[...extData()];
  if(!d.length)return;
  if(window.sortCol) {
    d.sort((a,b)=>{
      let va=a[window.sortCol], vb=b[window.sortCol];
      if(window.sortCol==='Window') return window.sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      return window.sortAsc ? va-vb : vb-va;
    });
  }
  const asset=segVal('segAsset').toUpperCase();
  const brk=segVal('segBreak')==='double_break'?'Double Break':segVal('segBreak')==='single_break'?'Single Break':'All Breaks';
  const dir={combined:'Combined',high_first:'High First',low_first:'Low First'}[segVal('segDir')];
  const tag=`${asset} · ${brk} · ${dir}`;
  $('extCount').textContent=d.length+' windows';

  // CDF
  const row=d[Math.min(extWin,d.length-1)];
  $('extCdfHead').innerHTML=`<span class="dot" style="background:var(--accent)"></span>CDF — ${row.Window} — ${tag}`;
  const vals=PCT.map(p=>row[p]);
  const lc=segVal('segBreak')==='double_break'?'#f87171':segVal('segBreak')==='single_break'?'#34d399':'#38bdf8';
  const ac=segVal('segBreak')==='double_break'?'rgba(248,113,113,.1)':segVal('segBreak')==='single_break'?'rgba(52,211,153,.1)':'rgba(56,189,248,.1)';

  ec('chartCdf').setOption({
    tooltip:{...TT,trigger:'axis',formatter:ps=>`<b style="color:#ececef">${ps[0].axisValue}</b><br>${ps[0].seriesName}: <b>${ps[0].value.toFixed(2)}R</b>`},
    grid:{top:20,right:12,bottom:28,left:48},
    xAxis:{...AXIS_STYLE,type:'category',data:PCT,name:'Percentile',nameTextStyle:{fontSize:10,color:'#5e626e'}},
    yAxis:{...AXIS_STYLE,type:'value',name:'R'},
    series:[{name:brk,type:'line',data:vals,smooth:.3,symbol:'circle',symbolSize:4,lineStyle:{width:2.5,color:lc},itemStyle:{color:lc},
      areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:ac},{offset:1,color:'transparent'}]}},
      markLine:{silent:true,data:[{yAxis:1,lineStyle:{color:'#3e814c',type:'dashed',width:1},label:{formatter:'1R',color:'#5e626e',fontFamily:'IBM Plex Mono',fontSize:10}}]}
    }]
  },true);

  // Bar
  $('extBarHead').innerHTML=`<span class="dot" style="background:var(--warm)"></span>${extPct} Percentile — ${tag}`;
  const barLabels=d.map(r=>r.Window);
  const barVals=d.map(r=>r[extPct]);
  ec('chartBar').setOption({
    tooltip:{...TT,trigger:'axis',formatter:ps=>`<b style="color:#ececef">${ps[0].axisValue}</b><br>${extPct}: <b>${ps[0].value.toFixed(2)}R</b>`},
    grid:{top:10,right:12,bottom:60,left:48},
    dataZoom:[{type:'inside'}],
    xAxis:{...AXIS_STYLE,type:'category',data:barLabels,axisLabel:{...AXIS_STYLE.axisLabel,rotate:45,fontSize:9}},
    yAxis:{...AXIS_STYLE,type:'value',name:'R'},
    series:[{type:'bar',data:barVals,itemStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:lc},{offset:1,color:lc.replace(')',',0.2)').replace('rgb','rgba')}]},borderRadius:[3,3,0,0]},barMaxWidth:12}]
  },true);

  // Table
  let maxV=0;
  d.forEach(r=>PCT.forEach(p=>{if(p!=='100%'&&r[p]>maxV)maxV=r[p]}));
  function cellBg(v){const t=Math.min(1,v/(maxV||5));return `hsla(${155-t*135},50%,${38-t*10}%,.18)`}

  let th='<tr><th style="cursor:pointer;user-select:none" onclick="window.sortCol=\'Window\';window.sortAsc=!window.sortAsc;updateExt()">Window'+(window.sortCol==='Window'?(window.sortAsc?'▲':'▼'):'')+'</th>';PCT.forEach(p=>th+=`<th class="r" style="cursor:pointer;user-select:none" onclick="window.sortCol=\'${p}\';window.sortAsc=!window.sortAsc;updateExt()">${p}${window.sortCol===p?(window.sortAsc?'▲':'▼'):''}</th>`);th+='</tr>';
  $('extTHead').innerHTML=th;

  let tb='';
  d.forEach((r,i)=>{
    const cls=i===extWin?' class="hl clickable"':' class="clickable"';
    tb+=`<tr${cls} data-i="${i}"><td class="c-mono">${r.Window}</td>`;
    PCT.forEach(p=>{const v=r[p];tb+=`<td class="r c-mono" style="background:${cellBg(v)}">${typeof v==='number'?v.toFixed(2):v}</td>`});
    tb+='</tr>';
  });
  $('extTBody').innerHTML=tb;

  // Click row to select window
  $$('#extTBody tr.clickable').forEach(tr=>{
    tr.addEventListener('click',()=>{extWin=parseInt(tr.dataset.i);updateExt()});
  });
}

initSeg('segAsset',()=>{extWin=0;updateExt()});
initSeg('segBreak',()=>{extWin=0;updateExt()});
initSeg('segDir',()=>{extWin=0;updateExt()});
$('selPct').addEventListener('change',e=>{extPct=e.target.value;updateExt()});
initPctSel();
updateExt();

// ═══════════════════════════════════════════
// HEATMAP
// ═══════════════════════════════════════════
function updateHeatmap(){
  const type=segVal('segHmType');
  const asset=segVal('segHmAsset');
  const dir=segVal('segHmDir');
  const c=ec('chartHeatmap');

  if(type==='prob'){
    $('hmTitle').textContent='Double Break Probability — NQ vs ES';
    const windows=probData.map(d=>d.Window);
    const data=[];
    probData.forEach((d,yi)=>{data.push([0,yi,+d.NQ_DB_Prob.toFixed(1)]);data.push([1,yi,+d.ES_DB_Prob.toFixed(1)])});
    document.getElementById('chartHeatmap').style.height = Math.max(620, windows.length * 22 + 100) + 'px';
    c.resize();
    c.setOption({
      tooltip:{...TT,formatter:p=>`<b style="color:#ececef">${probData[p.value[1]].Window}</b><br>${['NQ','ES'][p.value[0]]}: <b>${p.value[2]}%</b>`},
      xAxis:{type:'category',data:['NQ','ES'],position:'top',axisLabel:{fontFamily:'IBM Plex Mono',fontSize:12,color:'#a0a4ae'},axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisTick:{show:false}},
      yAxis:{type:'category',data:windows,inverse:true,axisLabel:{fontFamily:'IBM Plex Mono',fontSize:10,color:'#5e626e'},axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisTick:{show:false},splitLine:{show:false}},
      grid:{top:36,right:80,bottom:8,left:96},
      visualMap:{min:12,max:90,calculable:true,orient:'vertical',right:6,top:'center',
        inRange:{color:['#064e3b','#059669','#34d399','#fbbf24','#f87171','#991b1b']},
        textStyle:{color:'#5e626e',fontFamily:'IBM Plex Mono',fontSize:10}},
      series:[{type:'heatmap',data:data,label:{show:true,fontFamily:'IBM Plex Mono',fontSize:10,color:'#ececef',formatter:p=>p.value[2]+'%'},
        emphasis:{itemStyle:{shadowBlur:6,shadowColor:'rgba(0,0,0,.5)'}}}]
    },true);
  }else if(type==='corr'){
    $('hmTitle').textContent='Cross-Asset Correlation: Leader vs Lagger (Same Side Break)';
    if (!corrData || !corrData.length) { c.clear(); return; }
    const windows=corrData.map(d=>d.Window);
    const cols = [
      { key: 'ES High Break (NQ Follows)', label: 'ES Leads ↑ (NQ Lags)' },
      { key: 'ES Low Break (NQ Follows)', label: 'ES Leads ↓ (NQ Lags)' },
      { key: 'NQ High Break (ES Follows)', label: 'NQ Leads ↑ (ES Lags)' },
      { key: 'NQ Low Break (ES Follows)', label: 'NQ Leads ↓ (ES Lags)' }
    ];
    const data=[];
    corrData.forEach((d,yi)=>{
      cols.forEach((col, xi)=>{
        data.push([xi, yi, typeof d[col.key]==='number'?+d[col.key].toFixed(1):0]);
      });
    });
    document.getElementById('chartHeatmap').style.height = Math.max(620, windows.length * 22 + 100) + 'px';
    c.resize();
    c.setOption({
      tooltip:{...TT,formatter:p=>`<b style="color:#ececef">${windows[p.value[1]]}</b><br>${cols[p.value[0]].label}: <b>${p.value[2]}%</b>`},
      xAxis:{type:'category',data:cols.map(c=>c.label),position:'top',axisLabel:{fontFamily:'IBM Plex Mono',fontSize:12,color:'#a0a4ae'},axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisTick:{show:false}},
      yAxis:{type:'category',data:windows,inverse:true,axisLabel:{fontFamily:'IBM Plex Mono',fontSize:10,color:'#5e626e'},axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisTick:{show:false},splitLine:{show:false}},
      grid:{top:36,right:80,bottom:8,left:96},
      visualMap:{min:30,max:90,calculable:true,orient:'vertical',right:6,top:'center',
        inRange:{color:['#121417','#191c21','#fbbf24','#f87171','#991b1b']},
        textStyle:{color:'#5e626e',fontFamily:'IBM Plex Mono',fontSize:10}},
      series:[{type:'heatmap',data:data,label:{show:true,fontFamily:'IBM Plex Mono',fontSize:10,color:'#ececef',formatter:p=>p.value[2]+'%'},
        emphasis:{itemStyle:{shadowBlur:6,shadowColor:'rgba(0,0,0,.5)'}}}]
    },true);
  }else{
    const btype=type==='ext_db'?'double_break':type==='ext_sb'?'single_break':'all_breaks';
    const label=btype==='double_break'?'Double Break':btype==='single_break'?'Single Break':'All Breaks';
    const dirLabel={combined:'Combined',high_first:'High First',low_first:'Low First'}[dir];
    $('hmTitle').textContent=`${asset.toUpperCase()} ${label} Extension — ${dirLabel}`;

    const d=EXT[asset]?.[btype]?.[dir];
    if(!d||!d.length){c.clear();return}

    const windows=d.map(r=>r.Window);
    const data=[];
    let maxV=0;
    d.forEach((r,yi)=>{
      PCT.forEach((p,xi)=>{const v=r[p];if(p!=='100%'&&v>maxV)maxV=v;data.push([xi,yi,typeof v==='number'?+v.toFixed(2):0])});
    });

    document.getElementById('chartHeatmap').style.height = Math.max(620, windows.length * 22 + 100) + 'px';
    c.resize();
    c.setOption({
      tooltip:{...TT,formatter:p=>`<b style="color:#ececef">${windows[p.value[1]]}</b> · ${PCT[p.value[0]]}<br>Extension: <b>${p.value[2]}R</b>`},
      xAxis:{type:'category',data:PCT,position:'top',axisLabel:{fontFamily:'IBM Plex Mono',fontSize:10,color:'#5e626e'},axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisTick:{show:false}},
      yAxis:{type:'category',data:windows,inverse:true,axisLabel:{fontFamily:'IBM Plex Mono',fontSize:10,color:'#5e626e'},axisLine:{lineStyle:{color:'rgba(255,255,255,0.06)'}},axisTick:{show:false},splitLine:{show:false}},
      grid:{top:36,right:80,bottom:8,left:96},
      visualMap:{min:0,max:Math.min(maxV,8),calculable:true,orient:'vertical',right:6,top:'center',
        inRange:{color:['#121417','#191c21','#064e3b','#059669','#34d399','#6ee7b7','#fbbf24','#f87171']},
        textStyle:{color:'#5e626e',fontFamily:'IBM Plex Mono',fontSize:10}},
      series:[{type:'heatmap',data:data,label:{show:false},emphasis:{itemStyle:{shadowBlur:6,shadowColor:'rgba(0,0,0,.5)'}}}]
    },true);
  }
}
initSeg('segHmType',updateHeatmap);
initSeg('segHmAsset',updateHeatmap);
initSeg('segHmDir',updateHeatmap);
updateHeatmap();

// ═══════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════
setTimeout(resizeAll,300);
</script>
</body>
</html>'''

# Replace placeholder with actual data
html_final = html_template.replace('__DATA_BLOCK__', data_block)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_final)

print(f"Dashboard saved to {OUT_PATH}")
print(f"Size: {os.path.getsize(OUT_PATH)/1024:.0f} KB")
