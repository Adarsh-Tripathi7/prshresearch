import pandas as pd
import numpy as np
from numba import njit
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
def compute_db_duration(
    session_starts, session_ends, mins_arr, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr
):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    rth_close_m = 1380 # 16:00 EST
    
    nq_durations_sum = np.zeros(num_windows, dtype=np.float64)
    nq_db_counts = np.zeros(num_windows, dtype=np.int32)
    
    es_durations_sum = np.zeros(num_windows, dtype=np.float64)
    es_db_counts = np.zeros(num_windows, dtype=np.int32)
    
    valid_sessions = np.zeros(num_windows, dtype=np.int32)
    
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
                
            valid_sessions[w] += 1
            
            # Check for Double Break before RTH Close
            nq_broke_h_m = -1
            nq_broke_l_m = -1
            es_broke_h_m = -1
            es_broke_l_m = -1
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m and m <= rth_close_m:
                    if nq_broke_h_m == -1 and nq_h_arr[i] > ib_nq_h: nq_broke_h_m = m
                    if nq_broke_l_m == -1 and nq_l_arr[i] < ib_nq_l: nq_broke_l_m = m
                    
                    if es_broke_h_m == -1 and es_h_arr[i] > ib_es_h: es_broke_h_m = m
                    if es_broke_l_m == -1 and es_l_arr[i] < ib_es_l: es_broke_l_m = m
                    
                    if nq_broke_h_m != -1 and nq_broke_l_m != -1 and es_broke_h_m != -1 and es_broke_l_m != -1:
                        break
                elif m > rth_close_m:
                    break
            
            if nq_broke_h_m != -1 and nq_broke_l_m != -1:
                nq_db_counts[w] += 1
                nq_durations_sum[w] += abs(nq_broke_h_m - nq_broke_l_m)
            
            if es_broke_h_m != -1 and es_broke_l_m != -1:
                es_db_counts[w] += 1
                es_durations_sum[w] += abs(es_broke_h_m - es_broke_l_m)
                
    return nq_db_counts, es_db_counts, valid_sessions, nq_durations_sum, es_durations_sum

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
        windows_list.append([start_time, start_time + 6])
        h1 = ((start_time // 60) + 17) % 24
        m1 = start_time % 60
        h2 = (((start_time + 6) // 60) + 17) % 24
        m2 = (start_time + 6) % 60
        labels.append(f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}")
        start_time += 7
    
    windows_arr = np.array(windows_list, dtype=np.int32)
    
    print("Running Analysis...")
    nq_db_counts, es_db_counts, valid_sessions, nq_durations_sum, es_durations_sum = compute_db_duration(
        session_starts, session_ends, mins_arr, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr
    )

    results = []
    for w in range(len(labels)):
        total = valid_sessions[w]
        if total > 0:
            nq_prob = (nq_db_counts[w] / total) * 100
            es_prob = (es_db_counts[w] / total) * 100
        else:
            nq_prob = 0
            es_prob = 0
            
        nq_avg_duration = nq_durations_sum[w] / nq_db_counts[w] if nq_db_counts[w] > 0 else 0
        es_avg_duration = es_durations_sum[w] / es_db_counts[w] if es_db_counts[w] > 0 else 0
        
        results.append({
            'Window': labels[w],
            'NQ_DB_Prob': nq_prob,
            'ES_DB_Prob': es_prob,
            'NQ_Avg_DB_Duration_Mins': nq_avg_duration,
            'ES_Avg_DB_Duration_Mins': es_avg_duration
        })
        
    res_df = pd.DataFrame(results)
    
    # Filter for windows with probability > 75%
    high_prob_df = res_df[(res_df['NQ_DB_Prob'] > 75) | (res_df['ES_DB_Prob'] > 75)]
    
    print("\n--- High Probability Double Break Windows (> 75%) ---")
    if high_prob_df.empty:
        print("No windows found with > 75% Double Break Probability.")
    else:
        print(high_prob_df.to_string(index=False))

    report_path = os.path.join(results_dir, "high_prob_db_durations_7m.txt")
    with open(report_path, "w") as f:
        f.write("High Probability Double Break Windows (> 75%)\n")
        f.write("="*50 + "\n")
        f.write(high_prob_df.to_string(index=False))
        
    print(f"\nSaved report to {report_path}")

if __name__ == "__main__":
    main()
