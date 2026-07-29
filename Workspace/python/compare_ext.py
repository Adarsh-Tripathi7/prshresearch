import pandas as pd
import numpy as np
from numba import njit
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
def compute_extensions(
    session_starts, session_ends, mins_arr, 
    nq_h_arr, nq_l_arr, windows_arr,
    ext_arr_nq, type_arr_nq, use_new_logic
):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    count_nq = 0
    
    for w in range(num_windows):
        start_m = windows_arr[w, 0]
        end_m = windows_arr[w, 1]
        
        for s in range(num_sessions):
            idx_start = session_starts[s]
            idx_end = session_ends[s]
            
            ib_nq_h = -1.0
            ib_nq_l = 1e9
            has_ib = False
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m >= start_m and m <= end_m:
                    if nq_h_arr[i] > ib_nq_h: ib_nq_h = nq_h_arr[i]
                    if nq_l_arr[i] < ib_nq_l: ib_nq_l = nq_l_arr[i]
                    has_ib = True
                elif m > end_m:
                    break
                    
            if not has_ib: continue
            nq_r = ib_nq_h - ib_nq_l
            if nq_r <= 0: continue
                
            nq_first_dir = 0
            nq_max_ext = 0.0
            nq_is_double = 0
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m:
                    if nq_first_dir == 0:
                        if nq_h_arr[i] > ib_nq_h:
                            nq_first_dir = 1
                            nq_max_ext = nq_h_arr[i] - ib_nq_h
                            if nq_l_arr[i] < ib_nq_l:
                                nq_is_double = 2
                                break
                        elif nq_l_arr[i] < ib_nq_l:
                            nq_first_dir = -1
                            nq_max_ext = ib_nq_l - nq_l_arr[i]
                            if nq_h_arr[i] > ib_nq_h:
                                nq_is_double = 2
                                break
                    else:
                        if use_new_logic:
                            if nq_first_dir == 1:
                                if nq_l_arr[i] < ib_nq_l:
                                    nq_is_double = 2
                                    break
                                ext = nq_h_arr[i] - ib_nq_h
                                if ext > nq_max_ext: nq_max_ext = ext
                            else:
                                if nq_h_arr[i] > ib_nq_h:
                                    nq_is_double = 2
                                    break
                                ext = ib_nq_l - nq_l_arr[i]
                                if ext > nq_max_ext: nq_max_ext = ext
                        else:
                            if nq_first_dir == 1:
                                ext = nq_h_arr[i] - ib_nq_h
                                if ext > nq_max_ext: nq_max_ext = ext
                                if nq_l_arr[i] < ib_nq_l:
                                    nq_is_double = 2
                                    break
                            else:
                                ext = ib_nq_l - nq_l_arr[i]
                                if ext > nq_max_ext: nq_max_ext = ext
                                if nq_h_arr[i] > ib_nq_h:
                                    nq_is_double = 2
                                    break
                                    
            if nq_first_dir != 0:
                if nq_is_double == 0: nq_is_double = 1
                ext_arr_nq[count_nq] = nq_max_ext / nq_r
                type_arr_nq[count_nq] = nq_is_double
                count_nq += 1
                
    return count_nq

def run_comparison():
    print("Loading NQ data...")
    df = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
    df['Time'] = pd.to_datetime(df['Time'], format='mixed').dt.time
    df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    
    df['SessionDate'] = df['DateTime'].apply(get_session_date)
    df['MinsFromStart'] = df['DateTime'].apply(calc_mins_from_start)
    
    # Pre-compute both filtered and unfiltered
    df_old = df.copy()
    df_new = df[df['MinsFromStart'] <= 1380].copy()
    
    def process_df(d, use_new):
        session_dates = d['SessionDate'].values
        unique_sessions = np.unique(session_dates)
        session_to_idx = {val: idx for idx, val in enumerate(unique_sessions)}
        session_idx = np.array([session_to_idx[val] for val in session_dates], dtype=np.int32)
        
        session_starts = []
        session_ends = []
        current_s = session_idx[0]
        start_i = 0
        for i in range(1, len(session_idx)):
            if session_idx[i] != current_s:
                session_starts.append(start_i)
                session_ends.append(i)
                current_s = session_idx[i]
                start_i = i
        session_starts.append(start_i)
        session_ends.append(len(session_idx))
        
        session_starts = np.array(session_starts, dtype=np.int32)
        session_ends = np.array(session_ends, dtype=np.int32)
        mins_arr = d['MinsFromStart'].values.astype(np.int32)
        nq_h_arr = d['High'].values.astype(np.float64)
        nq_l_arr = d['Low'].values.astype(np.float64)
        
        windows = []
        start_time = 60
        max_time = 1380
        while start_time + 9 <= max_time:
            windows.append([start_time, start_time + 9])
            start_time += 10
        windows_arr = np.array(windows, dtype=np.int32)
        
        max_possible = len(windows) * len(session_starts)
        ext_arr = np.zeros(max_possible, dtype=np.float64)
        type_arr = np.zeros(max_possible, dtype=np.int32)
        
        c = compute_extensions(session_starts, session_ends, mins_arr, nq_h_arr, nq_l_arr, windows_arr, ext_arr, type_arr, use_new)
        
        return ext_arr[:c], type_arr[:c]

    print("Running OLD logic...")
    old_ext, old_type = process_df(df_old, False)
    
    print("Running NEW logic...")
    new_ext, new_type = process_df(df_new, True)
    
    old_db = np.mean(old_ext[old_type == 2])
    old_sb = np.mean(old_ext[old_type == 1])
    
    new_db = np.mean(new_ext[new_type == 2])
    new_sb = np.mean(new_ext[new_type == 1])
    
    print("--- Results ---")
    print(f"Old Single Break Avg: {old_sb:.2f}R")
    print(f"New Single Break Avg: {new_sb:.2f}R (Difference: {new_sb - old_sb:.2f}R)")
    print(f"Old Double Break Avg: {old_db:.2f}R")
    print(f"New Double Break Avg: {new_db:.2f}R (Difference: {new_db - old_db:.2f}R)")

run_comparison()
