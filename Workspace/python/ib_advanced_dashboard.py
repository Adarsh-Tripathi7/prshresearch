import os, csv, json

DATA_DIR = r"d:\Antigravity\Results"
OUT_PATH = os.path.join(r"d:\Antigravity\Dashboard", "ib_advanced_dashboard.html")

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

comp = read_csv_json("ib_compression_60m.csv")
urg = read_csv_json("ib_urgency_60m.csv")

data_block = json.dumps({"comp": comp, "urg": urg}, separators=(',',':'))

html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>IB Advanced Volatility Dynamics</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root {
  --bg: #09090b;
  --bg-raised: #18181b;
  --bg-surface: #27272a;
  --border: #3f3f46;
  --text-1: #fafafa;
  --text-2: #a1a1aa;
  --up: #10b981;
  --dn: #ef4444;
  --accent: #6366f1;
  --warm: #f59e0b;
  --font: 'DM Sans', sans-serif;
  --mono: 'IBM Plex Mono', monospace;
}
body{font-family:var(--font);background:var(--bg);color:var(--text-1);padding:40px}
.container{max-width:1400px;margin:0 auto}
.header{margin-bottom:40px}
.title{font-size:24px;font-weight:700;letter-spacing:-.5px;color:var(--text-1)}
.subtitle{font-size:14px;color:var(--text-2);margin-top:8px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.card{background:var(--bg-raised);border:1px solid var(--border);border-radius:12px;overflow:hidden;padding:24px}
.card-title{font-size:16px;font-weight:600;margin-bottom:16px;color:var(--text-1)}
.echart{width:100%;height:400px}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="title">Institutional IB Dynamics: Compression & Urgency</div>
    <div class="subtitle">Volatility-Adjusted Range Dynamics & Time-to-Break Velocity (60m Window Baseline)</div>
  </div>
  
  <div class="grid">
    <div class="card">
      <div class="card-title">IB Compression (Double Break % by IB Size)</div>
      <div id="chartComp" class="echart"></div>
    </div>
    <div class="card">
      <div class="card-title">Breakout Urgency (Double Break % by Time-to-Break)</div>
      <div id="chartUrg" class="echart"></div>
    </div>
  </div>
</div>

<script>
const _D = __DATA_BLOCK__;
const comp = _D.comp;
const urg = _D.urg;

const c1 = echarts.init(document.getElementById('chartComp'));
const c2 = echarts.init(document.getElementById('chartUrg'));
window.addEventListener('resize', () => { c1.resize(); c2.resize(); });

// Compression Chart
const labels = comp.map(d=>d.Window);
c1.setOption({
  tooltip:{trigger:'axis', backgroundColor:'#18181b', borderColor:'#3f3f46', textStyle:{color:'#fafafa'}},
  legend:{top:0, right:0, textStyle:{color:'#a1a1aa'}},
  grid:{top:40, right:20, bottom:60, left:50},
  dataZoom:[{type:'inside'}],
  xAxis:{type:'category', data:labels, axisLabel:{rotate:45, color:'#a1a1aa'}},
  yAxis:{type:'value', name:'DB %', max:100, axisLabel:{color:'#a1a1aa'}, splitLine:{lineStyle:{color:'#27272a'}}},
  series:[
    {name:'Q1 (Tight IB)', type:'line', smooth:true, data:comp.map(d=>d.Q1_Tight_DB_Prob), itemStyle:{color:'#ef4444'}, lineStyle:{width:3}},
    {name:'Q4 (Wide IB)', type:'line', smooth:true, data:comp.map(d=>d.Q4_Extreme_DB_Prob), itemStyle:{color:'#10b981'}, lineStyle:{width:3}},
    {name:'Q2/Q3 (Normal)', type:'line', smooth:true, data:comp.map(d=>(d.Q2_Normal_DB_Prob+d.Q3_Wide_DB_Prob)/2), itemStyle:{color:'#6366f1'}, lineStyle:{width:1.5, type:'dashed'}}
  ]
});

// Urgency Chart
c2.setOption({
  tooltip:{trigger:'axis', backgroundColor:'#18181b', borderColor:'#3f3f46', textStyle:{color:'#fafafa'}},
  legend:{top:0, right:0, textStyle:{color:'#a1a1aa'}},
  grid:{top:40, right:20, bottom:60, left:50},
  dataZoom:[{type:'inside'}],
  xAxis:{type:'category', data:labels, axisLabel:{rotate:45, color:'#a1a1aa'}},
  yAxis:{type:'value', name:'DB %', max:100, axisLabel:{color:'#a1a1aa'}, splitLine:{lineStyle:{color:'#27272a'}}},
  series:[
    {name:'Urgent (<15m)', type:'line', smooth:true, data:urg.map(d=>d.Urgent_DB_Prob), itemStyle:{color:'#10b981'}, lineStyle:{width:3}},
    {name:'Exhausted (>3h)', type:'line', smooth:true, data:urg.map(d=>d.Exhausted_DB_Prob), itemStyle:{color:'#ef4444'}, lineStyle:{width:3}},
    {name:'Normal (15m-1h)', type:'line', smooth:true, data:urg.map(d=>d.Normal_DB_Prob), itemStyle:{color:'#6366f1'}, lineStyle:{width:1.5, type:'dashed'}}
  ]
});
</script>
</body>
</html>'''

html_final = html.replace('__DATA_BLOCK__', data_block)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_final)
    
print(f"Advanced dashboard saved to {OUT_PATH}")
