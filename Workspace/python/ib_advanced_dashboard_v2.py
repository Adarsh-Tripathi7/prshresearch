import os, csv, json

DATA_DIR = r"d:\Antigravity\Results"
OUT_PATH = os.path.join(r"d:\Antigravity\Dashboard", "ib_advanced_dashboard_v2.html")

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

chop = read_csv_json("ib_choppiness.csv")
vec = read_csv_json("ib_closing_vector.csv")

data_block = json.dumps({"chop": chop, "vec": vec}, separators=(',',':'))

html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>IB Structural Edge Terminal</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root {
  --bg: #09090b;
  --bg-card: #18181b;
  --border: #27272a;
  --text-primary: #fafafa;
  --text-secondary: #a1a1aa;
  --accent-1: #3b82f6; /* Blue */
  --accent-2: #8b5cf6; /* Purple */
  --up: #10b981;
  --dn: #ef4444;
  --warn: #f59e0b;
}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text-primary);padding:32px;line-height:1.5}
.container{max-width:1600px;margin:0 auto}
.header{margin-bottom:40px;border-bottom:1px solid var(--border);padding-bottom:24px}
.title{font-size:28px;font-weight:700;letter-spacing:-.5px;margin-bottom:8px}
.subtitle{font-size:15px;color:var(--text-secondary);max-width:800px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1),0 2px 4px -1px rgba(0,0,0,0.06)}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.card-title{font-size:17px;font-weight:600;display:flex;align-items:center;gap:8px}
.card-title::before{content:'';display:block;width:4px;height:16px;background:var(--accent-1);border-radius:2px}
.chart{width:100%;height:450px}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="title">IB Structural Edge Terminal</div>
    <div class="subtitle">Truly out-of-the-box quantitative analysis focusing on the <b>Internal Structure</b> (Closing Vectors) and <b>Internal Turbulence</b> (Choppiness Index) of the 60-minute Initial Balance. Max Extensions are calculated in exact percentages.</div>
  </div>
  
  <div class="grid">
    <div class="card">
      <div class="card-header"><div class="card-title">Closing Vector: Avg Single-Break Extension (%)</div></div>
      <div class="subtitle" style="margin-bottom:16px;font-size:13px">Does a strong IB close (Top 25% or Bottom 25%) lead to a much larger % trend extension than a neutral close?</div>
      <div id="c1" class="chart"></div>
    </div>
    
    <div class="card">
      <div class="card-header"><div class="card-title" style="--accent-1:var(--accent-2)">Choppiness Index: Double Break Probability</div></div>
      <div class="subtitle" style="margin-bottom:16px;font-size:13px">Does a highly turbulent IB (high Path Length) exhaust the market and guarantee a fakeout/Double Break?</div>
      <div id="c2" class="chart"></div>
    </div>
  </div>
  
  <div class="grid">
    <div class="card">
      <div class="card-header"><div class="card-title" style="--accent-1:var(--warn)">Closing Vector: Double Break Probability</div></div>
      <div class="subtitle" style="margin-bottom:16px;font-size:13px">Does a neutral close in the middle of the IB guarantee chop and a subsequent Double Break?</div>
      <div id="c3" class="chart"></div>
    </div>
    
    <div class="card">
      <div class="card-header"><div class="card-title" style="--accent-1:var(--up)">Choppiness Index: Avg Single-Break Extension (%)</div></div>
      <div class="subtitle" style="margin-bottom:16px;font-size:13px">Does a clean, non-choppy IB yield a substantially larger % trend extension when it breaks?</div>
      <div id="c4" class="chart"></div>
    </div>
  </div>
</div>

<script>
const _D = __DATA_BLOCK__;
const chop = _D.chop;
const vec = _D.vec;

if (!chop || !vec || chop.length === 0 || vec.length === 0) {
    document.querySelector('.container').innerHTML += '<h2 style="color:red;margin-top:40px">Data not found! Please ensure Python scripts have finished running.</h2>';
} else {

const labels = chop.map(d=>d.Window);

const charts = [
  echarts.init(document.getElementById('c1')),
  echarts.init(document.getElementById('c2')),
  echarts.init(document.getElementById('c3')),
  echarts.init(document.getElementById('c4'))
];
window.addEventListener('resize', () => charts.forEach(c => c.resize()));

const axisStyle = { axisLabel: { color: '#a1a1aa' }, splitLine: { lineStyle: { color: '#27272a' } } };
const tt = { trigger: 'axis', backgroundColor: '#18181b', borderColor: '#3f3f46', textStyle: { color: '#fafafa' } };

// 1. Closing Vector: MFE %
charts[0].setOption({
  tooltip: tt, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' } },
  grid: { top: 40, right: 20, bottom: 60, left: 50 }, dataZoom: [{ type: 'inside' }],
  xAxis: { type: 'category', data: labels, axisLabel: { rotate: 45, color: '#a1a1aa' } },
  yAxis: { type: 'value', name: 'Max Ext (%)', ...axisStyle },
  series: [
    { name: 'Bullish Close (Top 25%)', type: 'line', smooth: 0.2, data: vec.map(d=>d.Bull_Close_MFE), itemStyle: { color: '#10b981' }, lineStyle: { width: 3 } },
    { name: 'Bearish Close (Bot 25%)', type: 'line', smooth: 0.2, data: vec.map(d=>d.Bear_Close_MFE), itemStyle: { color: '#ef4444' }, lineStyle: { width: 3 } },
    { name: 'Neutral Close (Mid 50%)', type: 'line', smooth: 0.2, data: vec.map(d=>d.Neutral_Close_MFE), itemStyle: { color: '#6366f1' }, lineStyle: { width: 1.5, type: 'dashed' } }
  ]
});

// 2. Choppiness Index: DB %
charts[1].setOption({
  tooltip: tt, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' } },
  grid: { top: 40, right: 20, bottom: 60, left: 50 }, dataZoom: [{ type: 'inside' }],
  xAxis: { type: 'category', data: labels, axisLabel: { rotate: 45, color: '#a1a1aa' } },
  yAxis: { type: 'value', name: 'DB Probability (%)', max: 100, min: 20, ...axisStyle },
  series: [
    { name: 'Choppy IB (Top 33%)', type: 'line', smooth: 0.2, data: chop.map(d=>d.Choppy_DB_Prob), itemStyle: { color: '#f59e0b' }, lineStyle: { width: 3 } },
    { name: 'Clean IB (Bot 33%)', type: 'line', smooth: 0.2, data: chop.map(d=>d.Clean_DB_Prob), itemStyle: { color: '#3b82f6' }, lineStyle: { width: 3 } },
    { name: 'Normal IB', type: 'line', smooth: 0.2, data: chop.map(d=>d.Normal_DB_Prob), itemStyle: { color: '#a1a1aa' }, lineStyle: { width: 1.5, type: 'dashed' } }
  ]
});

// 3. Closing Vector: DB %
charts[2].setOption({
  tooltip: tt, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' } },
  grid: { top: 40, right: 20, bottom: 60, left: 50 }, dataZoom: [{ type: 'inside' }],
  xAxis: { type: 'category', data: labels, axisLabel: { rotate: 45, color: '#a1a1aa' } },
  yAxis: { type: 'value', name: 'DB Probability (%)', max: 100, min: 20, ...axisStyle },
  series: [
    { name: 'Neutral Close', type: 'line', smooth: 0.2, data: vec.map(d=>d.Neutral_Close_DB_Prob), itemStyle: { color: '#6366f1' }, lineStyle: { width: 3 } },
    { name: 'Bullish Close', type: 'line', smooth: 0.2, data: vec.map(d=>d.Bull_Close_DB_Prob), itemStyle: { color: '#10b981' }, lineStyle: { width: 1.5 } },
    { name: 'Bearish Close', type: 'line', smooth: 0.2, data: vec.map(d=>d.Bear_Close_DB_Prob), itemStyle: { color: '#ef4444' }, lineStyle: { width: 1.5 } }
  ]
});

// 4. Choppiness Index: MFE %
charts[3].setOption({
  tooltip: tt, legend: { top: 0, right: 0, textStyle: { color: '#a1a1aa' } },
  grid: { top: 40, right: 20, bottom: 60, left: 50 }, dataZoom: [{ type: 'inside' }],
  xAxis: { type: 'category', data: labels, axisLabel: { rotate: 45, color: '#a1a1aa' } },
  yAxis: { type: 'value', name: 'Max Ext (%)', ...axisStyle },
  series: [
    { name: 'Clean IB', type: 'line', smooth: 0.2, data: chop.map(d=>d.Clean_Avg_MFE), itemStyle: { color: '#3b82f6' }, lineStyle: { width: 3 } },
    { name: 'Choppy IB', type: 'line', smooth: 0.2, data: chop.map(d=>d.Choppy_Avg_MFE), itemStyle: { color: '#f59e0b' }, lineStyle: { width: 3 } },
    { name: 'Normal IB', type: 'line', smooth: 0.2, data: chop.map(d=>d.Normal_Avg_MFE), itemStyle: { color: '#a1a1aa' }, lineStyle: { width: 1.5, type: 'dashed' } }
  ]
});

}
</script>
</body>
</html>'''

html_final = html.replace('__DATA_BLOCK__', data_block)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_final)
    
print(f"V2 Dashboard saved to {OUT_PATH}")
