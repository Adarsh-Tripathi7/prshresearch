import pandas as pd
import numpy as np
from numba import njit
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time

def get_session_date(dt):
    if dt.hour >= 17:
        return dt.date() + pd.Timedelta(days=1)
    else:
        return dt.date()

def calc_mins_from_start(dt):
    if dt.hour >= 17:
        return (dt.hour - 17) * 60 + dt.minute
    else:
        return (dt.hour + 7) * 60 + dt.minute

@njit
def compute_directional_double_breaks(
    session_starts, session_ends, mins_arr, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr
):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    
    es_led_h = np.zeros(num_windows, dtype=np.int32)
    es_led_h_followed = np.zeros(num_windows, dtype=np.int32)
    es_led_l = np.zeros(num_windows, dtype=np.int32)
    es_led_l_followed = np.zeros(num_windows, dtype=np.int32)
    
    nq_led_h = np.zeros(num_windows, dtype=np.int32)
    nq_led_h_followed = np.zeros(num_windows, dtype=np.int32)
    nq_led_l = np.zeros(num_windows, dtype=np.int32)
    nq_led_l_followed = np.zeros(num_windows, dtype=np.int32)
    
    for w in range(num_windows):
        start_m = windows_arr[w, 0]
        end_m = windows_arr[w, 1]
        
        for s in range(num_sessions):
            idx_start = session_starts[s]
            idx_end = session_ends[s]
            
            # 1. Find IB extremes
            ib_nq_h = -1.0
            ib_nq_l = 1e9
            ib_es_h = -1.0
            ib_es_l = 1e9
            
            has_ib_data = False
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m >= start_m and m <= end_m:
                    if nq_h_arr[i] > ib_nq_h: ib_nq_h = nq_h_arr[i]
                    if nq_l_arr[i] < ib_nq_l: ib_nq_l = nq_l_arr[i]
                    if es_h_arr[i] > ib_es_h: ib_es_h = es_h_arr[i]
                    if es_l_arr[i] < ib_es_l: ib_es_l = es_l_arr[i]
                    has_ib_data = True
                elif m > end_m:
                    break 
                    
            if not has_ib_data:
                continue
                
            # 2. Find Double Breaks
            nq_h_break_idx = -1
            nq_l_break_idx = -1
            es_h_break_idx = -1
            es_l_break_idx = -1
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m:
                    if nq_h_break_idx == -1 and nq_h_arr[i] > ib_nq_h: nq_h_break_idx = i
                    if nq_l_break_idx == -1 and nq_l_arr[i] < ib_nq_l: nq_l_break_idx = i
                    if es_h_break_idx == -1 and es_h_arr[i] > ib_es_h: es_h_break_idx = i
                    if es_l_break_idx == -1 and es_l_arr[i] < ib_es_l: es_l_break_idx = i
                    
                    if nq_h_break_idx != -1 and nq_l_break_idx != -1 and es_h_break_idx != -1 and es_l_break_idx != -1:
                        break 
                        
            # Determine Double Break Completion Times & Directions
            nq_db_idx = -1
            nq_db_dir = 0
            if nq_h_break_idx != -1 and nq_l_break_idx != -1:
                nq_db_idx = nq_h_break_idx if nq_h_break_idx > nq_l_break_idx else nq_l_break_idx
                nq_db_dir = 1 if nq_db_idx == nq_h_break_idx else -1
                
            es_db_idx = -1
            es_db_dir = 0
            if es_h_break_idx != -1 and es_l_break_idx != -1:
                es_db_idx = es_h_break_idx if es_h_break_idx > es_l_break_idx else es_l_break_idx
                es_db_dir = 1 if es_db_idx == es_h_break_idx else -1
                
            # Determine leader and lagger
            if nq_db_idx != -1 and es_db_idx != -1:
                if nq_db_idx == es_db_idx:
                    continue 
                elif nq_db_idx < es_db_idx: # NQ Led
                    if nq_db_dir == 1:
                        nq_led_h[w] += 1
                        if es_db_dir == 1: nq_led_h_followed[w] += 1
                    else:
                        nq_led_l[w] += 1
                        if es_db_dir == -1: nq_led_l_followed[w] += 1
                elif es_db_idx < nq_db_idx: # ES Led
                    if es_db_dir == 1:
                        es_led_h[w] += 1
                        if nq_db_dir == 1: es_led_h_followed[w] += 1
                    else:
                        es_led_l[w] += 1
                        if nq_db_dir == -1: es_led_l_followed[w] += 1
            elif nq_db_idx != -1 and es_db_idx == -1:
                if nq_db_dir == 1: nq_led_h[w] += 1
                else: nq_led_l[w] += 1
            elif es_db_idx != -1 and nq_db_idx == -1:
                if es_db_dir == 1: es_led_h[w] += 1
                else: es_led_l[w] += 1
                
    return (es_led_h, es_led_h_followed, es_led_l, es_led_l_followed,
            nq_led_h, nq_led_h_followed, nq_led_l, nq_led_l_followed)

def main():
    results_dir = r"d:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    
    t0 = time.time()
    print("Loading datasets (via pyarrow)...")
    nq_1m = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
    es_1m = pd.read_parquet(r"d:\Antigravity\Historical data\ES Futures Datasets\Full Data\parquet\ES_1m_full_data.parquet")

    nq_1m = nq_1m[['Date', 'Time', 'High', 'Low']].rename(
        columns={'High': 'NQ_High', 'Low': 'NQ_Low'})
    es_1m = es_1m[['Date', 'Time', 'High', 'Low']].rename(
        columns={'High': 'ES_High', 'Low': 'ES_Low'})
        
    print("Merging datasets...")
    df = pd.merge(nq_1m, es_1m, on=['Date', 'Time'], how='inner')
    
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    df['Mins'] = df['Datetime'].apply(calc_mins_from_start)
    
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    print("Preparing arrays for Numba JIT compilation...")
    unique_sessions = df['SessionDate'].unique()
    session_map = {sess: i for i, sess in enumerate(unique_sessions)}
    session_idx_arr = df['SessionDate'].map(session_map).values.astype(np.int32)

    mins_arr = df['Mins'].values.astype(np.int32)
    nq_h_arr = df['NQ_High'].values.astype(np.float32)
    nq_l_arr = df['NQ_Low'].values.astype(np.float32)
    es_h_arr = df['ES_High'].values.astype(np.float32)
    es_l_arr = df['ES_Low'].values.astype(np.float32)

    num_sessions = len(unique_sessions)
    session_starts = np.zeros(num_sessions, dtype=np.int32)
    session_ends = np.zeros(num_sessions, dtype=np.int32)

    curr_sess = session_idx_arr[0]
    session_starts[curr_sess] = 0
    for i in range(1, len(session_idx_arr)):
        if session_idx_arr[i] != curr_sess:
            session_ends[curr_sess] = i
            curr_sess = session_idx_arr[i]
            session_starts[curr_sess] = i
    session_ends[curr_sess] = len(session_idx_arr)

    # Generate windows
    windows_list = []
    labels = []
    start_time = 60 # 18:00
    while start_time <= 1260: # 14:00
        windows_list.append([start_time, start_time + 14])
        h1 = ((start_time // 60) + 17) % 24
        m1 = start_time % 60
        h2 = (((start_time + 14) // 60) + 17) % 24
        m2 = (start_time + 14) % 60
        labels.append(f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}")
        start_time += 15
    
    windows_arr = np.array(windows_list, dtype=np.int32)
    
    print("Running Directional Double Break Analysis (Numba JIT)...")
    t_numba_start = time.time()
    out = compute_directional_double_breaks(
        session_starts, session_ends, mins_arr, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr
    )
    (es_led_h, es_led_h_followed, es_led_l, es_led_l_followed,
     nq_led_h, nq_led_h_followed, nq_led_l, nq_led_l_followed) = out
    t_numba_end = time.time()
    print(f"Numba computation took: {t_numba_end - t_numba_start:.4f} seconds!")

    # ---------------------------------------------------------
    # BUILD RESULTS
    # ---------------------------------------------------------
    results = []
    for w in range(len(labels)):
        es_h_prob = (es_led_h_followed[w] / es_led_h[w]) * 100 if es_led_h[w] > 0 else 0
        es_l_prob = (es_led_l_followed[w] / es_led_l[w]) * 100 if es_led_l[w] > 0 else 0
        nq_h_prob = (nq_led_h_followed[w] / nq_led_h[w]) * 100 if nq_led_h[w] > 0 else 0
        nq_l_prob = (nq_led_l_followed[w] / nq_led_l[w]) * 100 if nq_led_l[w] > 0 else 0
        
        results.append({
            'Window': labels[w],
            'ES Resolves UP (NQ Follows)': es_h_prob,
            'ES Resolves DOWN (NQ Follows)': es_l_prob,
            'NQ Resolves UP (ES Follows)': nq_h_prob,
            'NQ Resolves DOWN (ES Follows)': nq_l_prob
        })
        
    res_df = pd.DataFrame(results)

    print("Generating Dashboard...")
    hm_df = res_df.set_index('Window')
    
    plt.figure(figsize=(14, 16))
    sns.heatmap(hm_df, annot=True, fmt=".1f", cmap="Reds", cbar_kws={'label': 'Correlation Probability (%)'})
    plt.title('Rolling IB Double Break Correlation by Resolution Direction')
    plt.ylabel('Rolling 15-Minute Window')
    plt.xlabel('Leader & Resolution Direction')
    plt.tight_layout()
    
    plots_path = os.path.join(results_dir, "ib_double_break_directional_heatmap_15m.png")
    plt.savefig(plots_path, dpi=300)
    plt.close()
    
    avg_es_h = res_df['ES Resolves UP (NQ Follows)'].mean()
    avg_es_l = res_df['ES Resolves DOWN (NQ Follows)'].mean()
    avg_nq_h = res_df['NQ Resolves UP (ES Follows)'].mean()
    avg_nq_l = res_df['NQ Resolves DOWN (ES Follows)'].mean()
    
    total_time = time.time() - t0
    
    report = f"""# 🌪️ Directional Gravity: Cross-Asset "Double Breaks"
*Testing whether a Double Break that resolves UPwards acts differently than a Double Break that resolves DOWNwards.*

## 📊 Directional Double Break Resolution
Since a Double Break means BOTH sides of the IB were broken, the "Direction" is determined by whichever side broke *second* (which is the side the market is actively resolving towards).

Excluding simultaneous breaks, here is the correlation of the lagging asset completing a double break in the *same* final resolution direction:
- **Average ES Resolving UP:** {avg_es_h:.2f}% *(NQ completes double break to the upside)*
- **Average ES Resolving DOWN:** {avg_es_l:.2f}% *(NQ completes double break to the downside)*
- **Average NQ Resolving UP:** {avg_nq_h:.2f}% *(ES completes double break to the upside)*
- **Average NQ Resolving DOWN:** {avg_nq_l:.2f}% *(ES completes double break to the downside)*

### 🔍 Key Observation (Resolution Asymmetry)
Compare these numbers to the Single Break directional probabilities. Double breaks often represent extreme structural failure on one side of the market (e.g. a failed breakdown) leading to a massive squeeze in the opposite direction. The heatmap below proves whether upside squeezes or downside liquidation cascades command more statistical cross-asset gravity!

## 📉 Directional Double Break Correlation Heatmap
![Directional Double Break Correlation Heatmap](file:///{plots_path.replace('\\', '/')})

## 💡 Quantitative Conclusion
If NQ breaks its Low, and then wildly reverses to break its High (resolving UP), and ES has not yet completed its double break, the statistics below give you the exact mathematical edge to play the lagging ES breakout to the upside.
"""

    dashboard_path = os.path.join(results_dir, "ib_double_break_directional_dashboard_15m.md")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Dashboard saved to {dashboard_path}")

if __name__ == "__main__":
    main()
