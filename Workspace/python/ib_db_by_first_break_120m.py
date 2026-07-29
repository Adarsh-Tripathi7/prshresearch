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
def compute_directional_first_db(
    session_starts, session_ends, mins_arr, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr
):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    
    rth_close_m = 1380 # 16:00 EST
    
    nq_h_first_counts = np.zeros(num_windows, dtype=np.int32)
    nq_h_first_db_counts = np.zeros(num_windows, dtype=np.int32)
    nq_l_first_counts = np.zeros(num_windows, dtype=np.int32)
    nq_l_first_db_counts = np.zeros(num_windows, dtype=np.int32)
    
    es_h_first_counts = np.zeros(num_windows, dtype=np.int32)
    es_h_first_db_counts = np.zeros(num_windows, dtype=np.int32)
    es_l_first_counts = np.zeros(num_windows, dtype=np.int32)
    es_l_first_db_counts = np.zeros(num_windows, dtype=np.int32)
    
    for w in range(num_windows):
        start_m = windows_arr[w, 0]
        end_m = windows_arr[w, 1]
        
        for s in range(num_sessions):
            idx_start = session_starts[s]
            idx_end = session_ends[s]
            
            # Find IB extremes
            ib_nq_h = -1.0
            ib_nq_l = 1e9
            ib_es_h = -1.0
            ib_es_l = 1e9
            
            has_ib = False
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m >= start_m and m <= end_m:
                    if nq_h_arr[i] > ib_nq_h: ib_nq_h = nq_h_arr[i]
                    if nq_l_arr[i] < ib_nq_l: ib_nq_l = nq_l_arr[i]
                    if es_h_arr[i] > ib_es_h: ib_es_h = es_h_arr[i]
                    if es_l_arr[i] < ib_es_l: ib_es_l = es_l_arr[i]
                    has_ib = True
                elif m > end_m:
                    break
                    
            if not has_ib:
                continue
                
            # Check which breaks first and if it double breaks
            nq_first_break = 0 # 1 for high, -1 for low
            es_first_break = 0
            nq_db = False
            es_db = False
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m and m <= rth_close_m:
                    # NQ
                    if nq_first_break == 0:
                        if nq_h_arr[i] > ib_nq_h: nq_first_break = 1
                        elif nq_l_arr[i] < ib_nq_l: nq_first_break = -1
                    
                    if nq_first_break == 1 and not nq_db:
                        if nq_l_arr[i] < ib_nq_l: nq_db = True
                    elif nq_first_break == -1 and not nq_db:
                        if nq_h_arr[i] > ib_nq_h: nq_db = True
                        
                    # ES
                    if es_first_break == 0:
                        if es_h_arr[i] > ib_es_h: es_first_break = 1
                        elif es_l_arr[i] < ib_es_l: es_first_break = -1
                        
                    if es_first_break == 1 and not es_db:
                        if es_l_arr[i] < ib_es_l: es_db = True
                    elif es_first_break == -1 and not es_db:
                        if es_h_arr[i] > ib_es_h: es_db = True
                        
                    if nq_db and es_db:
                        break
                            
                elif m > rth_close_m:
                    break
            
            if nq_first_break == 1:
                nq_h_first_counts[w] += 1
                if nq_db: nq_h_first_db_counts[w] += 1
            elif nq_first_break == -1:
                nq_l_first_counts[w] += 1
                if nq_db: nq_l_first_db_counts[w] += 1
                
            if es_first_break == 1:
                es_h_first_counts[w] += 1
                if es_db: es_h_first_db_counts[w] += 1
            elif es_first_break == -1:
                es_l_first_counts[w] += 1
                if es_db: es_l_first_db_counts[w] += 1
                
    return (nq_h_first_counts, nq_h_first_db_counts, nq_l_first_counts, nq_l_first_db_counts,
            es_h_first_counts, es_h_first_db_counts, es_l_first_counts, es_l_first_db_counts)

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
        windows_list.append([start_time, start_time + 119])
        h1 = ((start_time // 60) + 17) % 24
        m1 = start_time % 60
        h2 = (((start_time + 119) // 60) + 17) % 24
        m2 = (start_time + 119) % 60
        labels.append(f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}")
        start_time += 60
    
    windows_arr = np.array(windows_list, dtype=np.int32)
    
    print("Running DB Probability Analysis (Numba JIT)...")
    t_numba_start = time.time()
    out = compute_directional_first_db(
        session_starts, session_ends, mins_arr, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr
    )
    (nq_h_first_counts, nq_h_first_db_counts, nq_l_first_counts, nq_l_first_db_counts,
     es_h_first_counts, es_h_first_db_counts, es_l_first_counts, es_l_first_db_counts) = out
    t_numba_end = time.time()
    print(f"Numba computation took: {t_numba_end - t_numba_start:.4f} seconds!")

    # ---------------------------------------------------------
    # BUILD RESULTS
    # ---------------------------------------------------------
    results = []
    for w in range(len(labels)):
        nq_h_prob = (nq_h_first_db_counts[w] / nq_h_first_counts[w]) * 100 if nq_h_first_counts[w] > 0 else 0
        nq_l_prob = (nq_l_first_db_counts[w] / nq_l_first_counts[w]) * 100 if nq_l_first_counts[w] > 0 else 0
        es_h_prob = (es_h_first_db_counts[w] / es_h_first_counts[w]) * 100 if es_h_first_counts[w] > 0 else 0
        es_l_prob = (es_l_first_db_counts[w] / es_l_first_counts[w]) * 100 if es_l_first_counts[w] > 0 else 0
            
        results.append({
            'Window': labels[w],
            'NQ_H_First_DB_Prob': nq_h_prob,
            'NQ_L_First_DB_Prob': nq_l_prob,
            'ES_H_First_DB_Prob': es_h_prob,
            'ES_L_First_DB_Prob': es_l_prob
        })
        
    res_df = pd.DataFrame(results)
    
    # Save to CSV
    csv_path = os.path.join(results_dir, "db_probability_by_first_break_120m.csv")
    res_df.to_csv(csv_path, index=False)
    
    # Heatmap
    hm_df = res_df.set_index('Window')
    
    plt.figure(figsize=(10, 16))
    sns.heatmap(hm_df, annot=True, fmt=".1f", cmap="OrRd", cbar_kws={'label': 'Double Break Probability (%)'})
    plt.title('Probability of Double Break Based on Which Side Breaks First')
    plt.ylabel('Rolling 120-Minute IB Window')
    plt.xlabel('Asset & First Break Side')
    plt.tight_layout()
    
    plots_path = os.path.join(results_dir, "db_probability_first_break_heatmap_120m.png")
    plt.savefig(plots_path, dpi=300)
    plt.close()
    
    def df_to_markdown(df):
        if df.empty: return ""
        cols = ['Window', 'NQ H First DB Prob (%)', 'NQ L First DB Prob (%)', 'ES H First DB Prob (%)', 'ES L First DB Prob (%)']
        res = "| " + " | ".join(cols) + " |\n"
        res += "|" + "|".join(["---"] * len(cols)) + "|\n"
        for _, row in df.iterrows():
            vals = [str(row['Window']), 
                    f"{row['NQ_H_First_DB_Prob']:.2f}%", 
                    f"{row['NQ_L_First_DB_Prob']:.2f}%",
                    f"{row['ES_H_First_DB_Prob']:.2f}%",
                    f"{row['ES_L_First_DB_Prob']:.2f}%"]
            res += "| " + " | ".join(vals) + " |\n"
        return res
        
    report = f"""# 🎲 Base-Rate Probability: Double Breaks by First Break Side
*What is the probability of a double break given that the Initial Balance High broke first vs. the Initial Balance Low broke first?*

## 📊 Probability Heatmap
![First Break Double Break Probability Heatmap](file:///{plots_path.replace('\\', '/')})

## 📝 Detailed Probability Matrix
{df_to_markdown(res_df)}

## 💡 Quantitative Conclusion
This analysis shows whether breaking the High or the Low first makes an IB more susceptible to a Double Break (full reversal).
"""

    dashboard_path = os.path.join(results_dir, "db_probability_first_break_dashboard_120m.md")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Dashboard saved to {dashboard_path}")

if __name__ == "__main__":
    main()
