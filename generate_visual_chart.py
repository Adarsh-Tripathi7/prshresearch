import pandas as pd
import json
import os

def create_chart():
    print("Loading data...")
    df = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
    
    df['dt'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df = df.sort_values('dt').reset_index(drop=True)
    
    unique_dates = df['Date'].unique()
    last_5_dates = unique_dates[-5:]
    
    df = df[df['Date'].isin(last_5_dates)].copy()
    df['session_date'] = (df['dt'] - pd.Timedelta(hours=17)).dt.date
    
    markers = []
    
    grouped = df.groupby('session_date')
    
    for session_date, group in grouped:
        group = group.sort_values('dt')
        
        window = group[(group['dt'].dt.time >= pd.to_datetime('23:29').time()) & 
                       (group['dt'].dt.time <= pd.to_datetime('23:35').time())]
        
        if window.empty: continue
        
        w_high = window['High'].max()
        w_low = window['Low'].min()
        target = w_high + 0.40 * (w_high - w_low)
        sl = w_low
        
        after_window = group[group['dt'].dt.time > pd.to_datetime('23:35').time()]
        if after_window.empty: continue
        
        entered = False
        invalidated = False
        
        for idx, row in after_window.iterrows():
            if not entered and not invalidated:
                if row['Low'] <= w_low:
                    invalidated = True
                elif row['High'] > w_high:
                    entered = True
                    markers.append({
                        "time": int(row['dt'].timestamp()),
                        "position": "belowBar",
                        "color": "#22c55e",
                        "shape": "arrowUp",
                        "text": "LONG ENTRY"
                    })
                    
                    if row['High'] >= target:
                        markers.append({
                            "time": int(row['dt'].timestamp()),
                            "position": "aboveBar",
                            "color": "#3b82f6",
                            "shape": "arrowDown",
                            "text": "TARGET HIT"
                        })
                        break
                    elif row['Low'] <= sl:
                        markers.append({
                            "time": int(row['dt'].timestamp()),
                            "position": "aboveBar",
                            "color": "#ef4444",
                            "shape": "arrowDown",
                            "text": "STOP LOSS"
                        })
                        break
            elif entered:
                if row['High'] >= target:
                    markers.append({
                        "time": int(row['dt'].timestamp()),
                        "position": "aboveBar",
                        "color": "#3b82f6",
                        "shape": "arrowDown",
                        "text": "TARGET HIT"
                    })
                    break
                elif row['Low'] <= sl:
                    markers.append({
                        "time": int(row['dt'].timestamp()),
                        "position": "aboveBar",
                        "color": "#ef4444",
                        "shape": "arrowDown",
                        "text": "STOP LOSS"
                    })
                    break

    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            "time": int(row['dt'].timestamp()),
            "open": row['Open'],
            "high": row['High'],
            "low": row['Low'],
            "close": row['Last']
        })
        
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Strategy Visualization (Free)</title>
<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
<style>
    body {{ background: #131722; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: white; }}
    #tvchart {{ width: 100vw; height: 100vh; }}
    .header {{ position: absolute; top: 10px; left: 10px; z-index: 10; background: rgba(0,0,0,0.7); padding: 10px 20px; border-radius: 8px; border: 1px solid #2b2b43; }}
    .header h2 {{ margin: 0 0 5px 0; font-size: 18px; color: #d1d4dc; }}
    .header p {{ margin: 0; font-size: 13px; color: #888; }}
</style>
</head>
<body>
    <div class="header">
        <h2>Offline Strategy Visualizer</h2>
        <p>1-Minute Chart | Displaying last 5 sessions | Data: NQ Parquet</p>
    </div>
    <div id="tvchart"></div>
    <script>
        const chart = LightweightCharts.createChart(document.getElementById('tvchart'), {{
            layout: {{
                background: {{ color: '#131722' }},
                textColor: '#d1d4dc',
            }},
            grid: {{
                vertLines: {{ color: '#2b2b43' }},
                horzLines: {{ color: '#2b2b43' }},
            }},
            crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
            rightPriceScale: {{ borderColor: '#2b2b43' }},
            timeScale: {{ borderColor: '#2b2b43', timeVisible: true, secondsVisible: false }},
        }});
        
        const candleSeries = chart.addCandlestickSeries({{
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350'
        }});
        
        const data = {json.dumps(chart_data)};
        candleSeries.setData(data);
        
        const markers = {json.dumps(markers)};
        if (markers.length > 0) {{
            candleSeries.setMarkers(markers);
        }}
    </script>
</body>
</html>"""

    with open(r"d:\Antigravity\Results\strategy_visualizer.html", "w") as f:
        f.write(html_content)
        
    print(r"Generated visualizer at d:\Antigravity\Results\strategy_visualizer.html")

if __name__ == "__main__":
    create_chart()
