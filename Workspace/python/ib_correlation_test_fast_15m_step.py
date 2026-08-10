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
def compute_all_windows(
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
                
            # 2. Find first break
            nq_first_break_idx = -1
            nq_break_dir = 0 # 1 for high, -1 for low
            
            es_first_break_idx = -1
            es_break_dir = 0
            
            # Scan post window
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m:
                    # check NQ
                    if nq_first_break_idx == -1:
                        if nq_h_arr[i] > ib_nq_h:
                            nq_first_break_idx = i
                            nq_break_dir = 1
                        elif nq_l_arr[i] < ib_nq_l:
                            nq_first_break_idx = i
                            nq_break_dir = -1
                            
                    # check ES
                    if es_first_break_idx == -1:
                        if es_h_arr[i] > ib_es_h:
                            es_first_break_idx = i
                            es_break_dir = 1
                        elif es_l_arr[i] < ib_es_l:
                            es_first_break_idx = i
                            es_break_dir = -1
                            
                    if nq_first_break_idx != -1 and es_first_break_idx != -1:
                        break
                        
            # Determine leader and lagger
            if nq_first_break_idx != -1 and es_first_break_idx != -1:
                if nq_first_break_idx == es_first_break_idx:
                    continue 
                elif nq_first_break_idx < es_first_break_idx:
                    if nq_break_dir == 1:
                        nq_led_h[w] += 1
                        if es_break_dir == 1: nq_led_h_followed[w] += 1
                    else:
                        nq_led_l[w] += 1
                        if es_break_dir == -1: nq_led_l_followed[w] += 1
                        
                elif es_first_break_idx < nq_first_break_idx:
                    if es_break_dir == 1:
                        es_led_h[w] += 1
                        if nq_break_dir == 1: es_led_h_followed[w] += 1
                    else:
                        es_led_l[w] += 1
                        if nq_break_dir == -1: es_led_l_followed[w] += 1
                        
            elif nq_first_break_idx != -1 and es_first_break_idx == -1:
                if nq_break_dir == 1: nq_led_h[w] += 1
                else: nq_led_l[w] += 1
            elif es_first_break_idx != -1 and nq_first_break_idx == -1:
                if es_break_dir == 1: es_led_h[w] += 1
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
    
    # ---------------------------------------------------------
    # EXTRACT ARRAYS FOR NUMBA
    # ---------------------------------------------------------
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
        start_time += 1
    
    windows_arr = np.array(windows_list, dtype=np.int32)
    
    print("Running Numba compiled loop (Blazingly Fast)...")
    t_numba_start = time.time()
    out = compute_all_windows(
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
            'ES High Break (NQ Follows)': es_h_prob,
            'ES Low Break (NQ Follows)': es_l_prob,
            'NQ High Break (ES Follows)': nq_h_prob,
            'NQ Low Break (ES Follows)': nq_l_prob
        })
        
    res_df = pd.DataFrame(results)
    
    csv_path = os.path.join(results_dir, "ib_correlation_directional_15m_step.csv")
    res_df.to_csv(csv_path, index=False)
    print(f"Saved correlation data to {csv_path}")

    print("Generating Dashboard...")
    hm_df = res_df.set_index('Window')
    
    plt.figure(figsize=(14, 16))
    sns.heatmap(hm_df, annot=True, fmt=".1f", cmap="magma", cbar_kws={'label': 'Correlation Probability (%)'})
    plt.title('Rolling IB Breakout Correlation by Direction (No Simultaneous Breaks)')
    plt.ylabel('Rolling 15-Minute Window')
    plt.xlabel('Leader & Break Direction')
    plt.tight_layout()
    
    plots_path = os.path.join(results_dir, "ib_correlation_directional_heatmap_15m_step.png")
    plt.savefig(plots_path, dpi=300)
    plt.close()
    
    avg_es_h = res_df['ES High Break (NQ Follows)'].mean()
    avg_es_l = res_df['ES Low Break (NQ Follows)'].mean()
    avg_nq_h = res_df['NQ High Break (ES Follows)'].mean()
    avg_nq_l = res_df['NQ Low Break (ES Follows)'].mean()
    
    total_time = time.time() - t0
    
    report = f"""# 🧭 Directional Bias: Cross-Asset IB Correlation (High vs Low)
*Testing if market gravity differs between Bullish breakouts (IB High) and Bearish breakdowns (IB Low).*

## 🚀 Performance Metrics
- **Processing Engine:** Numba JIT Compiled over Numpy Arrays
- **Math Execution Time:** {t_numba_end - t_numba_start:.4f} seconds (Blazingly Fast!)

## 📊 Directional High-Frequency Correlation
Excluding simultaneous breaks, here is the *true* actionable statistical edge separated by direction:
- **Average ES Leading HIGH Break:** {avg_es_h:.2f}% *(NQ Follows Up)*
- **Average ES Leading LOW Break:** {avg_es_l:.2f}% *(NQ Follows Down)*
- **Average NQ Leading HIGH Break:** {avg_nq_h:.2f}% *(ES Follows Up)*
- **Average NQ Leading LOW Break:** {avg_nq_l:.2f}% *(ES Follows Down)*

### 🔍 Key Observation (Bulls vs Bears)
Look at the averages above and the heatmap below to determine if there is a structural asymmetry. Typically, because the broader equity market has an upward drift (bullish bias), High Breaks often have slightly more structural follow-through, while Low Breaks can sometimes be liquidity traps (fake breakdowns). However, macro sell-offs are famously highly correlated. The data below reveals the exact quantitative truth!

## 📉 Directional Correlation Heatmap
![Directional IB Correlation Heatmap](file:///{plots_path.replace('\\', '/')})

## 💡 Quantitative Conclusion
By categorizing the breakouts by direction, a trader can fine-tune their sizing. If the data shows that "ES Leading Low Breaks" have a structurally lower correlation probability during specific time windows (e.g., European session), a trader should reduce their size on short setups, or demand tighter stops. 
"""

    dashboard_path = os.path.join(results_dir, "ib_correlation_directional_dashboard_15m_step.md")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Dashboard saved to {dashboard_path}")

if __name__ == "__main__":
    main()
