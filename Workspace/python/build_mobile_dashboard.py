import re
import os

FILES = [
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_7m_1m_step.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_7m.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_10m.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_15m_step.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_15m.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_30m_15m_step.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_30m.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_45m.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_60m.html",
    r"d:\Antigravity\Dashboard\ib_interactive_dashboard_120m.html"
]

OUT_DIR = r"d:\Antigravity\imobile ib dashboard"

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Prsh Capital | TITLE_PLACEHOLDER</title>
<meta name="description" content="Prsh Capital Research Hub. Advanced quantitative analysis, probability models, and market extension matrices for NQ and ES futures.">
<meta name="keywords" content="Prsh Capital, Quantitative Research, Trading, NQ, ES, Futures, Probability Models, Extension Matrix">
<meta property="og:title" content="Prsh Capital | TITLE_PLACEHOLDER">
<meta property="og:description" content="Advanced quantitative analysis and probability models for NQ and ES futures.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://prshcapital.netlify.app/">
<meta property="og:image" content="https://prshcapital.netlify.app/screenshot-wide.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://prshcapital.netlify.app/screenshot-wide.png">
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#000000">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="icon" type="image/x-icon" href="favicon.ico">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png?v=3">
<link rel="icon" type="image/png" sizes="512x512" href="icon-512.png?v=3">
<link rel="apple-touch-icon" href="icon-192.png?v=3">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
</head>
<body>



<header class="app-bar">
  <div style="display:flex; align-items:center;">
    <a href="index.html" class="brand" aria-label="Go to Home" style="margin-right:0;">
      <svg class="prsh-logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke-width="2"></path>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke-width="2"></polyline>
        <line x1="12" y1="22.08" x2="12" y2="12" stroke-width="2"></line>
      </svg>
      Prsh <span style="font-weight:400; color:var(--text-3); margin-left:4px;">Capital</span>
    </a>
    <div style="display:flex; gap:6px; margin-left:12px;">
      <button class="time-badge" id="timeBadgeBtn">TITLE_PLACEHOLDER</button>
      <button class="asset-badge" id="btnGlobalAsset">NQ | ES</button>
    </div>
  </div>
  <nav class="desktop-nav" id="desktopNav" role="tablist" aria-label="Dashboard Views" style="margin-left:auto; margin-right:24px;">
    <button class="active" data-p="overview" role="tab" aria-selected="true" tabindex="0">Overview</button>
    <button data-p="probability" role="tab" aria-selected="false" tabindex="-1">DB %</button>
    <button data-p="hl_first" role="tab" aria-selected="false" tabindex="-1">H/L First</button>
    <button data-p="extensions" role="tab" aria-selected="false" tabindex="-1">Extensions</button>
    <button data-p="heatmap" role="tab" aria-selected="false" tabindex="-1">Heatmap</button>
  </nav>
  <div class="search-box">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input type="text" id="search" placeholder="Search window (e.g. 09:30)...">
  </div>
</header>



<div id="spotlight"><div class="spot-head"><div class="spot-title" id="spotTitle"></div><button class="spot-close" id="spotClose">&times;</button></div><div class="spot-grid" id="spotGrid"></div></div>

<div class="kpi-strip" id="kpiStrip"></div>

<div class="container">
  
  <div class="page active" id="page-overview">
    <div class="grid grid-2">
      <div class="card">
        <div class="card-header"><div class="card-title"><div class="dot" style="background:var(--dn)"></div> DB Probability (Combined)</div></div>
        <div class="card-body"><div id="chartProb" class="echart"></div></div>
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title"><div class="dot" style="background:var(--up)"></div> Median Extension (NQ)</div></div>
        <div class="card-body"><div id="chartMedExt" class="echart"></div></div>
      </div>
    </div>
  </div>

  <div class="page" id="page-probability">
    <div class="grid">
      <div class="card">
        <div class="card-header">
          <div class="card-title"><div class="dot" style="background:var(--accent)"></div> DB Probability Explorer</div>
        </div>
        <div class="card-body"><div id="chartProbFull" class="echart" style="height:400px"></div></div>
      </div>
      <div class="card">
        <div class="card-body dense table-wrap">
          <table>
            <thead><tr><th>Window</th><th class="r">NQ %</th><th class="r">ES %</th><th class="r">Avg</th><th class="r">Δ</th></tr></thead>
            <tbody id="tblProb"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="page" id="page-hl_first">
    <div class="grid">
      <div class="card">
        <div class="card-header">
          <div class="card-title"><div class="dot" style="background:var(--accent)"></div> High First / Low First Double Break %</div>
          <div class="segments-scroll"><div class="segments" id="segHlFirstDir">
            <button class="active" data-v="high_first">High First</button>
            <button data-v="low_first">Low First</button>
            <button data-v="combined">Combined</button>
          </div></div>
        </div>
        <div class="card-body"><div id="chartHlFirst" class="echart" style="height:400px"></div></div>
      </div>
      <div class="card">
        <div class="card-body dense table-wrap">
          <table>
            <thead><tr><th>Window</th><th class="r">Opposite Break NQ %</th><th class="r">Opposite Break ES %</th><th class="r">Opp Break (Close) %</th><th class="r">Avg</th><th class="r">Δ</th></tr></thead>
            <tbody id="tblHlFirst"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="page" id="page-extensions">
    <div class="grid">
      <div class="card">
        <div class="card-header">
          <div class="card-title"><div class="dot" style="background:var(--warm)"></div> R-Multiple Extensions</div>
          <div class="segments-scroll"><div class="segments" id="segBreak">
            <button class="active" data-v="double_break">Double Break</button>
            <button data-v="single_break">Single Break</button>
            <button data-v="all_breaks">All Breaks</button>
          </div></div>
          <div class="segments-scroll"><div class="segments" id="segDir">
            <button class="active" data-v="combined">Combined</button>
            <button data-v="high_first">High First</button>
            <button data-v="low_first">Low First</button>
          </div></div>
        </div>
        <div class="card-body">
          <div style="font-size:12px; color:var(--text-3); margin-bottom:8px">Select a row in the table below to update CDF.</div>
          <div id="chartCdf" class="echart" style="height:280px"></div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="card-title" id="extBarHead"><div class="dot" style="background:var(--up)"></div> 50th Percentile</div>
          </div>
        </div>
        <div class="card-body"><div id="chartBar" class="echart" style="height:250px"></div></div>
      </div>

      <div class="card">
        <div class="card-header" style="padding-bottom:0">
          <div style="font-size:11px; color:var(--text-2); font-weight:500;">Tip: Click on a percentile header below (e.g. 90%) to change the chart</div>
        </div>
        <div class="card-body dense table-wrap" style="max-height:400px; overflow-y:auto; margin-top:8px;">
          <table>
            <thead id="extTHead"></thead>
            <tbody id="extTBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="page" id="page-heatmap">
    <div class="grid">
      <div class="card">
        <div class="card-header">
          <div class="card-title" id="hmTitle"><div class="dot" style="background:var(--accent)"></div> Heatmap</div>
          <div class="segments-scroll"><div class="segments" id="segHmType">
            <button class="active" data-v="prob">DB Prob</button>
            <button data-v="ext_db">DB Ext</button>
            <button data-v="ext_sb">SB Ext</button>
            <button data-v="ext_ab">All Ext</button>
            <button data-v="corr">Leader/Lagger</button>
          </div></div>
          <div class="segments-scroll" id="hmDirWrap"><div class="segments" id="segHmDir">
            <button class="active" data-v="combined">Combined</button>
            <button data-v="high_first">High First</button>
            <button data-v="low_first">Low First</button>
          </div></div>
        </div>
        <!-- Wrap Heatmap so it can expand fully in height inside the card -->
        <div class="card-body heatmap-wrap">
          <div id="chartHeatmap" class="echart" style="min-width: 600px;"></div>
        </div>
      </div>
    </div>
  </div>

</div>

<!-- BOTTOM NAV -->
<nav class="bottom-nav" id="bottomNav" role="tablist" aria-label="Mobile Dashboard Views">
  <button class="nav-btn active" data-p="overview" role="tab" aria-selected="true" tabindex="0"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg> Overview</button>
  <button class="nav-btn" data-p="probability" role="tab" aria-selected="false" tabindex="-1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 20V10M12 20V4M6 20v-6"></path></svg> DB %</button>
  <button class="nav-btn" data-p="hl_first" role="tab" aria-selected="false" tabindex="-1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 3v18M3 12h18"/></svg> H/L First</button>
  <button class="nav-btn" data-p="extensions" role="tab" aria-selected="false" tabindex="-1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg> Ext</button>
  <button class="nav-btn" data-p="heatmap" role="tab" aria-selected="false" tabindex="-1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg> Heatmap</button>
</nav>

<script>
const _D = DATA_PLACEHOLDER;
</script>
<script src="main.js"></script>
</body>
</html>
"""

import json
import csv

def format_title(name):
    parts = name.split('_')
    if 'step' in parts:
        if len(parts) == 3:
            return f"{parts[0]} / {parts[1]} STEP".upper()
        elif len(parts) == 2:
            return f"{parts[0]} STEP".upper()
    return name.upper()

NAME_TO_CSV = {
    '7m_1m_step': '7m_1m_step',
    '7m': '7m',
    '10m': '10m',
    '15m_step': '15m_1m_step',
    '15m': '15m',
    '30m_15m_step': '30m_15m_step',
    '30m': '30m',
    '45m': '45m',
    '60m': '60m',
    '120m': '120m'
}

for source_file in FILES:
    if not os.path.exists(source_file):
        continue
    with open(source_file, "r", encoding="utf-8") as f:
        html = f.read()
    
    match = re.search(r'const _D = (\{.*?\});\n', html, re.DOTALL)
    if not match:
        continue
    data_json_str = match.group(1)
    
    basename = os.path.basename(source_file)
    name_parts = basename.replace("ib_interactive_dashboard_", "").replace(".html", "")
    new_basename = basename.replace("ib_interactive_dashboard_", "time_range_")
    
    clean_title = format_title(name_parts)
    
    # Parse existing JSON
    try:
        data_obj = json.loads(data_json_str)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON in {basename}")
        continue
        
    # Read CSV and inject prob_first
    csv_name = NAME_TO_CSV.get(name_parts)
    if csv_name:
        csv_path = os.path.join(r"d:\Antigravity\Results\FirstExtremeProbs", f"{csv_name}.csv")
        if os.path.exists(csv_path):
            prob_first = []
            with open(csv_path, "r", encoding="utf-8") as cf:
                reader = csv.DictReader(cf)
                for row in reader:
                    nq_hf_tot = float(row["NQ_HF_Total"])
                    nq_lf_tot = float(row["NQ_LF_Total"])
                    nq_tot = nq_hf_tot + nq_lf_tot
                    nq_hf_lb = nq_hf_tot * float(row["NQ_HF_LowBrokenFirst_Prob"]) / 100
                    nq_lf_hb = nq_lf_tot * float(row["NQ_LF_HighBrokenFirst_Prob"]) / 100
                    nq_comb_opp = ((nq_hf_lb + nq_lf_hb) / nq_tot * 100) if nq_tot > 0 else 0
                    
                    nq_hf_cbm_tot = float(row["NQ_HF_CBM_Total"])
                    nq_lf_cam_tot = float(row["NQ_LF_CAM_Total"])
                    nq_cond_tot = nq_hf_cbm_tot + nq_lf_cam_tot
                    nq_hf_cbm_lb = nq_hf_cbm_tot * float(row["NQ_HF_CBM_Prob"]) / 100
                    nq_lf_cam_hb = nq_lf_cam_tot * float(row["NQ_LF_CAM_Prob"]) / 100
                    nq_comb_cond = ((nq_hf_cbm_lb + nq_lf_cam_hb) / nq_cond_tot * 100) if nq_cond_tot > 0 else 0

                    es_hf_tot = float(row["ES_HF_Total"])
                    es_lf_tot = float(row["ES_LF_Total"])
                    es_tot = es_hf_tot + es_lf_tot
                    es_hf_lb = es_hf_tot * float(row["ES_HF_LowBrokenFirst_Prob"]) / 100
                    es_lf_hb = es_lf_tot * float(row["ES_LF_HighBrokenFirst_Prob"]) / 100
                    es_comb_opp = ((es_hf_lb + es_lf_hb) / es_tot * 100) if es_tot > 0 else 0
                    
                    es_hf_cbm_tot = float(row["ES_HF_CBM_Total"])
                    es_lf_cam_tot = float(row["ES_LF_CAM_Total"])
                    es_cond_tot = es_hf_cbm_tot + es_lf_cam_tot
                    es_hf_cbm_lb = es_hf_cbm_tot * float(row["ES_HF_CBM_Prob"]) / 100
                    es_lf_cam_hb = es_lf_cam_tot * float(row["ES_LF_CAM_Prob"]) / 100
                    es_comb_cond = ((es_hf_cbm_lb + es_lf_cam_hb) / es_cond_tot * 100) if es_cond_tot > 0 else 0

                    prob_first.append({
                        "Window": row["Window"],
                        "NQ_H_First_L_Break_Prob": float(row["NQ_HF_LowBrokenFirst_Prob"]),
                        "NQ_H_First_H_Break_Prob": float(row["NQ_HF_HighBrokenFirst_Prob"]),
                        "NQ_H_First_CBM_Prob": float(row["NQ_HF_CBM_Prob"]),
                        "NQ_L_First_H_Break_Prob": float(row["NQ_LF_HighBrokenFirst_Prob"]),
                        "NQ_L_First_L_Break_Prob": float(row["NQ_LF_LowBrokenFirst_Prob"]),
                        "NQ_L_First_CAM_Prob": float(row["NQ_LF_CAM_Prob"]),
                        "NQ_Comb_Opp_Prob": nq_comb_opp,
                        "NQ_Comb_Cond_Prob": nq_comb_cond,
                        "ES_H_First_L_Break_Prob": float(row["ES_HF_LowBrokenFirst_Prob"]),
                        "ES_H_First_H_Break_Prob": float(row["ES_HF_HighBrokenFirst_Prob"]),
                        "ES_H_First_CBM_Prob": float(row["ES_HF_CBM_Prob"]),
                        "ES_L_First_H_Break_Prob": float(row["ES_LF_HighBrokenFirst_Prob"]),
                        "ES_L_First_L_Break_Prob": float(row["ES_LF_LowBrokenFirst_Prob"]),
                        "ES_L_First_CAM_Prob": float(row["ES_LF_CAM_Prob"]),
                        "ES_Comb_Opp_Prob": es_comb_opp,
                        "ES_Comb_Cond_Prob": es_comb_cond
                    })
            data_obj["prob_first"] = prob_first
        else:
            print(f"Warning: CSV not found for {csv_name}")
            
    # Serialize back to JSON string
    updated_json_str = json.dumps(data_obj)
    
    # Generate HTML
    final_html = TEMPLATE.replace("DATA_PLACEHOLDER", updated_json_str).replace("TITLE_PLACEHOLDER", clean_title)
    
    target_file = os.path.join(OUT_DIR, new_basename)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(final_html)
        
print("Updated badge titles, injected JSON data, and reverted decoupling for file:/// protocol support!")
