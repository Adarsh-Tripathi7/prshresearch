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
def compute_compression(session_starts, session_ends, mins_arr, high_arr, low_arr, windows_arr):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    
    # We will store (ib_range, db_status) for every session and every window
    # Shape: (num_windows, num_sessions, 2)
    # where index 0 = range, index 1 = 1 if DB else 0
    results = np.zeros((num_windows, num_sessions, 2), dtype=np.float32)
    results.fill(-1.0) # -1 means invalid/no data
    
    for w in range(num_windows):
        start_m = windows_arr[w, 0]
        end_m = windows_arr[w, 1]
        
        for s in range(num_sessions):
            idx_start = session_starts[s]
            idx_end = session_ends[s]
            
            ib_h = -1.0
            ib_l = 1e9
            
            has_ib_data = False
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m >= start_m and m <= end_m:
                    if high_arr[i] > ib_h: ib_h = high_arr[i]
                    if low_arr[i] < ib_l: ib_l = low_arr[i]
                    has_ib_data = True
                elif m > end_m:
                    break
                    
            if not has_ib_data:
                continue
                
            ib_range = ib_h - ib_l
            
            h_broken = False
            l_broken = False
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m:
                    if not h_broken and high_arr[i] > ib_h: h_broken = True
                    if not l_broken and low_arr[i] < ib_l: l_broken = True
                    
                    if h_broken and l_broken:
                        break
                        
            is_db = 1.0 if (h_broken and l_broken) else 0.0
            results[w, s, 0] = ib_range
            results[w, s, 1] = is_db
            
    return results

def main():
    results_dir = r"d:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    
    t0 = time.time()
    print("Loading NQ 1m dataset...")
    df = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
    
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    df['Mins'] = df['Datetime'].apply(calc_mins_from_start)
    
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    print("Preparing arrays...")
    unique_sessions = df['SessionDate'].unique()
    session_map = {sess: i for i, sess in enumerate(unique_sessions)}
    session_idx_arr = df['SessionDate'].map(session_map).values.astype(np.int32)

    mins_arr = df['Mins'].values.astype(np.int32)
    h_arr = df['High'].values.astype(np.float32)
    l_arr = df['Low'].values.astype(np.float32)

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

    # 60m windows, 30m step
    windows_list = []
    labels = []
    start_time = 60 # 18:00
    while start_time <= 1260: # 14:00
        windows_list.append([start_time, start_time + 59])
        h1 = ((start_time // 60) + 17) % 24
        m1 = start_time % 60
        h2 = (((start_time + 59) // 60) + 17) % 24
        m2 = (start_time + 59) % 60
        labels.append(f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}")
        start_time += 30
    
    windows_arr = np.array(windows_list, dtype=np.int32)
    
    print("Running Compression Analysis (Numba)...")
    t_numba_start = time.time()
    results = compute_compression(session_starts, session_ends, mins_arr, h_arr, l_arr, windows_arr)
    print(f"Numba computation took: {time.time() - t_numba_start:.4f} seconds!")

    # Process results into quartiles per window
    output_rows = []
    for w in range(len(labels)):
        # Extract valid sessions for this window
        valid_mask = results[w, :, 0] != -1.0
        ranges = results[w, valid_mask, 0]
        db_flags = results[w, valid_mask, 1]
        
        if len(ranges) < 100: continue # Skip if not enough data
        
        q25 = np.percentile(ranges, 25)
        q50 = np.percentile(ranges, 50)
        q75 = np.percentile(ranges, 75)
        
        q1_mask = ranges <= q25
        q2_mask = (ranges > q25) & (ranges <= q50)
        q3_mask = (ranges > q50) & (ranges <= q75)
        q4_mask = ranges > q75
        
        q1_prob = db_flags[q1_mask].mean() * 100 if q1_mask.sum() > 0 else 0
        q2_prob = db_flags[q2_mask].mean() * 100 if q2_mask.sum() > 0 else 0
        q3_prob = db_flags[q3_mask].mean() * 100 if q3_mask.sum() > 0 else 0
        q4_prob = db_flags[q4_mask].mean() * 100 if q4_mask.sum() > 0 else 0
        
        output_rows.append({
            'Window': labels[w],
            'Q1_Tight_DB_Prob': q1_prob,
            'Q2_Normal_DB_Prob': q2_prob,
            'Q3_Wide_DB_Prob': q3_prob,
            'Q4_Extreme_DB_Prob': q4_prob,
            'Q1_Max_Range': q25,
            'Q4_Min_Range': q75
        })
        
    df_out = pd.DataFrame(output_rows)
    out_path = os.path.join(results_dir, "ib_compression_60m.csv")
    df_out.to_csv(out_path, index=False)
    print(f"Saved compression data to {out_path}")

if __name__ == "__main__":
    main()
