import pandas as pd
import json
import os

df_perc = pd.read_csv(r'd:\Antigravity\Results\db_duration_percentiles.csv')
df_prob = pd.read_csv(r'd:\Antigravity\Results\db_probability_by_rth_close.csv')
df = pd.merge(df_prob, df_perc, on='Window')

# Fill NaN with 0 for JSON serialization
df = df.fillna(0)

data_json = df.to_json(orient='records')

html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Double Break Analytics Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            /* Notion Colors */
            --primary: #0075de;
            --primary-active: #005bab;
            --secondary: #213183;
            --on-primary: #ffffff;
            --canvas: #ffffff;
            --canvas-soft: #f6f5f4;
            --surface: #ffffff;
            --ink: #000000;
            --ink-secondary: #31302e;
            --ink-muted: #615d59;
            --ink-faint: #a39e98;
            --hairline: #e6e6e6;
            
            /* Shadows & Border */
            --shadow-sm: rgba(0,0,0,0.01) 0 0.175px 1.041px, rgba(0,0,0,0.02) 0 0.8px 2.925px, rgba(0,0,0,0.027) 0 2.025px 7.847px, rgba(0,0,0,0.04) 0 4px 18px;
        }}
        
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--canvas-soft);
            color: var(--ink);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }}
        
        /* Hero Band (secondary night color) */
        header {{
            background-color: var(--secondary);
            color: var(--on-primary);
            padding: 48px 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 24px;
        }}
        
        h1 {{
            margin: 0;
            font-size: 54px;
            font-weight: 700;
            line-height: 1.04;
            letter-spacing: -1.875px;
        }}
        
        /* Nav / Controls */
        .controls {{
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-top: -24px;
            padding: 24px;
        }}
        
        /* Utility Button */
        button {{
            background: var(--surface);
            color: var(--ink);
            border: 1px solid var(--hairline);
            padding: 8px 16px; 
            border-radius: 8px; /* rounded.md */
            font-family: inherit;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
        }}
        button:hover {{
            background: var(--canvas-soft);
        }}
        button.active {{
            background: var(--primary);
            color: var(--on-primary);
            border-color: var(--primary);
        }}
        
        /* Main Container */
        .container {{
            padding: 40px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        
        /* Legend */
        .legend {{
            display: flex;
            gap: 32px;
            color: var(--ink-muted);
            font-size: 14px;
            justify-content: flex-end;
            align-items: center;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .gradient-bar {{
            width: 120px;
            height: 8px;
            border-radius: 4px;
        }}
        .gradient-prob {{
            background: linear-gradient(90deg, rgba(255,255,255, 0.1), rgba(26,174,57, 0.25)); /* transparent to soft green */
        }}
        .gradient-dur {{
            background: linear-gradient(90deg, rgba(255,255,255, 0.1), rgba(255,100,200, 0.15)); /* transparent to soft pink */
        }}
        
        /* Feature Card (Table Container) */
        .table-container {{
            background: var(--surface);
            border: 1px solid var(--hairline);
            border-radius: 12px; /* rounded.lg */
            overflow: auto;
            box-shadow: var(--shadow-sm);
            max-height: calc(100vh - 300px);
        }}
        
        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            text-align: right;
            white-space: nowrap;
        }}
        
        th, td {{
            padding: 12px 16px; /* spacing.sm spacing.md */
            border-bottom: 1px solid var(--hairline);
        }}
        
        th {{
            position: sticky;
            top: 0;
            background: var(--canvas-soft);
            color: var(--ink-secondary);
            font-size: 12px; /* eyebrow */
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.125px;
            z-index: 10;
        }}
        
        td {{
            font-size: 15px; /* body-sm */
            font-weight: 400;
            color: var(--ink);
        }}
        
        th:first-child, td:first-child {{
            text-align: left;
            position: sticky;
            left: 0;
            font-weight: 600;
        }}
        
        td:first-child {{
            background: var(--surface);
            z-index: 5;
            border-right: 1px solid var(--hairline);
        }}
        
        th:first-child {{
            background: var(--canvas-soft);
            z-index: 30;
            border-right: 1px solid var(--hairline);
        }}
        
        tbody tr:hover td:not(:first-child) {{
            background: var(--canvas-soft);
        }}
        
        .cell-value {{
            font-variant-numeric: tabular-nums;
        }}
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: var(--canvas-soft); }}
        ::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--ink-faint); }}
    </style>
</head>
<body>

    <header>
        <h1>Double Break Analytics</h1>
    </header>
    
    <div class="controls">
        <button id="btn-nq" class="active" onclick="setAsset('NQ')">NQ (Nasdaq)</button>
        <button id="btn-es" onclick="setAsset('ES')">ES (S&P 500)</button>
    </div>

    <div class="container">
        <div class="legend">
            <div class="legend-item">
                <span>Probability Heatmap:</span>
                <span>Low</span>
                <div class="gradient-bar gradient-prob"></div>
                <span>High</span>
            </div>
            <div class="legend-item">
                <span>Duration Heatmap:</span>
                <span>Fast</span>
                <div class="gradient-bar gradient-dur"></div>
                <span>Slow</span>
            </div>
        </div>
        <div class="table-container">
            <table id="data-table">
                <thead>
                    <tr id="table-header"></tr>
                </thead>
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </div>

    <script>
        const rawData = {data_json};
        let currentAsset = 'NQ';
        const percentiles = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95];

        function setAsset(asset) {{
            currentAsset = asset;
            document.getElementById('btn-nq').classList.toggle('active', asset === 'NQ');
            document.getElementById('btn-es').classList.toggle('active', asset === 'ES');
            renderTable();
        }}

        function getColor(val, min, max, isProb) {{
            if(val === 0) return 'transparent';
            
            let t = (val - min) / (max - min);
            t = Math.max(0, Math.min(1, t));
            
            if(isProb) {{
                const opacity = (t * 0.25); // max 25% opacity
                return `rgba(26, 174, 57, ${{opacity}})`; // varying green
            }} else {{
                const opacity = (t * 0.15); // max 15% opacity
                return `rgba(255, 100, 200, ${{opacity}})`; // varying pink
            }}
        }}

        function renderTable() {{
            const thead = document.getElementById('table-header');
            const tbody = document.getElementById('table-body');
            
            thead.innerHTML = '';
            tbody.innerHTML = '';

            let thHTML = `<th>Window</th><th>Prob (%)</th>`;
            percentiles.forEach(p => {{
                thHTML += `<th>P${{p}}</th>`;
            }});
            thead.innerHTML = thHTML;

            const probKey = currentAsset + '_DB_Prob';
            const probs = rawData.map(d => d[probKey]);
            const minProb = Math.min(...probs);
            const maxProb = Math.max(...probs);

            let allDurs = [];
            rawData.forEach(d => {{
                percentiles.forEach(p => {{
                    const v = d[`${{currentAsset}}_P${{p}}`];
                    if(v > 0) allDurs.push(v);
                }});
            }});
            const minDur = Math.min(...allDurs);
            const maxDur = Math.max(...allDurs);

            rawData.forEach(row => {{
                const tr = document.createElement('tr');
                
                let tdHTML = `<td>${{row.Window}}</td>`;
                
                const prob = row[probKey];
                const probColor = getColor(prob, minProb, maxProb, true);
                tdHTML += `<td style="background: ${{probColor}}"><span class="cell-value">${{prob.toFixed(1)}}%</span></td>`;
                
                percentiles.forEach(p => {{
                    const val = row[`${{currentAsset}}_P${{p}}`];
                    const color = getColor(val, minDur, maxDur, false);
                    const displayVal = val > 0 ? val.toFixed(1) : '-';
                    tdHTML += `<td style="background: ${{color}}"><span class="cell-value">${{displayVal}}</span></td>`;
                }});
                
                tr.innerHTML = tdHTML;
                tbody.appendChild(tr);
            }});
        }}

        renderTable();
    </script>
</body>
</html>
'''

out_path = r'd:\Antigravity\Results\IB Analysis\db_percentiles_dashboard.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f'Dashboard generated at {out_path}')
