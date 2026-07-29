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
def compute_internal_structure(session_starts, session_ends, mins_arr, o_arr, h_arr, l_arr, c_arr, windows_arr):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    
    # Results array: [num_windows, num_sessions, 6]
    # 0: IB_Range_Pct
    # 1: Choppiness_Index
    # 2: Closing_Vector
    # 3: First_Break_Dir (1=H, -1=L, 0=None)
    # 4: Is_Double_Break (1 or 0)
    # 5: MFE_Pct
    results = np.zeros((num_windows, num_sessions, 6), dtype=np.float32)
    results.fill(-1.0)
    
    for w in range(num_windows):
        start_m = windows_arr[w, 0]
        end_m = windows_arr[w, 1]
        
        for s in range(num_sessions):
            idx_start = session_starts[s]
            idx_end = session_ends[s]
            
            ib_h = -1.0
            ib_l = 1e9
            ib_o = -1.0
            ib_c = -1.0
            
            path_length = 0.0
            prev_c = -1.0
            
            has_ib_data = False
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m >= start_m and m <= end_m:
                    if not has_ib_data:
                        ib_o = o_arr[i]
                        has_ib_data = True
                        
                    if h_arr[i] > ib_h: ib_h = h_arr[i]
                    if l_arr[i] < ib_l: ib_l = l_arr[i]
                    ib_c = c_arr[i]
                    
                    if prev_c != -1.0:
                        path_length += abs(c_arr[i] - prev_c)
                    prev_c = c_arr[i]
                    
                elif m > end_m:
                    break
                    
            if not has_ib_data or ib_o <= 0 or (ib_h - ib_l) == 0:
                continue
                
            ib_range_pts = ib_h - ib_l
            ib_range_pct = (ib_range_pts / ib_o) * 100.0
            choppiness = path_length / ib_range_pts
            closing_vector = (ib_c - ib_l) / ib_range_pts
            
            # Find breaks and MFE
            h_broken = False
            l_broken = False
            first_dir = 0
            
            max_h_after = ib_h
            min_l_after = ib_l
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m:
                    # Update tracking first
                    if first_dir == 1 and not l_broken:
                        if h_arr[i] > max_h_after: max_h_after = h_arr[i]
                    elif first_dir == -1 and not h_broken:
                        if l_arr[i] < min_l_after: min_l_after = l_arr[i]
                        
                    # Check breaks
                    if not h_broken and h_arr[i] > ib_h:
                        h_broken = True
                        if first_dir == 0:
                            first_dir = 1
                            if h_arr[i] > max_h_after: max_h_after = h_arr[i]
                            
                    if not l_broken and l_arr[i] < ib_l:
                        l_broken = True
                        if first_dir == 0:
                            first_dir = -1
                            if l_arr[i] < min_l_after: min_l_after = l_arr[i]
                            
                    if h_broken and l_broken:
                        break # Stop tracking MFE once it double breaks
                        
            is_db = 1.0 if (h_broken and l_broken) else 0.0
            
            mfe_pct = 0.0
            if first_dir == 1:
                mfe_pct = ((max_h_after - ib_h) / ib_o) * 100.0
            elif first_dir == -1:
                mfe_pct = ((ib_l - min_l_after) / ib_o) * 100.0
                
            results[w, s, 0] = ib_range_pct
            results[w, s, 1] = choppiness
            results[w, s, 2] = closing_vector
            results[w, s, 3] = first_dir
            results[w, s, 4] = is_db
            results[w, s, 5] = mfe_pct
            
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
    o_arr = df['Open'].values.astype(np.float32)
    h_arr = df['High'].values.astype(np.float32)
    l_arr = df['Low'].values.astype(np.float32)
    c_arr = df['Last'].values.astype(np.float32)

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
    
    print("Running Internal Structure Analysis (Numba)...")
    t_numba = time.time()
    results = compute_internal_structure(session_starts, session_ends, mins_arr, o_arr, h_arr, l_arr, c_arr, windows_arr)
    print(f"Numba computation took: {time.time() - t_numba:.4f} seconds!")

    # We will compute aggregations across ALL windows combined for a high-level view, 
    # but we can also output window-specific. Let's do a global and per-window aggregation.
    
    out_rows_chop = []
    out_rows_vec = []
    
    for w in range(len(labels)):
        valid = results[w, :, 0] != -1.0
        r_chop = results[w, valid, 1]
        r_vec = results[w, valid, 2]
        r_db = results[w, valid, 4]
        r_mfe = results[w, valid, 5]
        
        if len(r_chop) < 50: continue
        
        # Choppiness Tertiles (Clean, Normal, Choppy)
        c_p33 = np.percentile(r_chop, 33)
        c_p66 = np.percentile(r_chop, 66)
        
        c1 = r_chop <= c_p33
        c2 = (r_chop > c_p33) & (r_chop <= c_p66)
        c3 = r_chop > c_p66
        
        out_rows_chop.append({
            'Window': labels[w],
            'Clean_DB_Prob': r_db[c1].mean()*100 if c1.sum()>0 else 0,
            'Clean_Avg_MFE': r_mfe[c1].mean() if c1.sum()>0 else 0,
            'Normal_DB_Prob': r_db[c2].mean()*100 if c2.sum()>0 else 0,
            'Normal_Avg_MFE': r_mfe[c2].mean() if c2.sum()>0 else 0,
            'Choppy_DB_Prob': r_db[c3].mean()*100 if c3.sum()>0 else 0,
            'Choppy_Avg_MFE': r_mfe[c3].mean() if c3.sum()>0 else 0,
        })
        
        # Vector Tertiles (Bearish Close, Neutral Close, Bullish Close)
        v1 = r_vec <= 0.25 # Bottom 25% (Bearish)
        v2 = (r_vec > 0.25) & (r_vec <= 0.75) # Middle 50%
        v3 = r_vec > 0.75 # Top 25% (Bullish)
        
        out_rows_vec.append({
            'Window': labels[w],
            'Bear_Close_DB_Prob': r_db[v1].mean()*100 if v1.sum()>0 else 0,
            'Bear_Close_MFE': r_mfe[v1].mean() if v1.sum()>0 else 0,
            'Neutral_Close_DB_Prob': r_db[v2].mean()*100 if v2.sum()>0 else 0,
            'Neutral_Close_MFE': r_mfe[v2].mean() if v2.sum()>0 else 0,
            'Bull_Close_DB_Prob': r_db[v3].mean()*100 if v3.sum()>0 else 0,
            'Bull_Close_MFE': r_mfe[v3].mean() if v3.sum()>0 else 0,
        })
        
    df_chop = pd.DataFrame(out_rows_chop)
    df_vec = pd.DataFrame(out_rows_vec)
    
    df_chop.to_csv(os.path.join(results_dir, "ib_choppiness.csv"), index=False)
    df_vec.to_csv(os.path.join(results_dir, "ib_closing_vector.csv"), index=False)
    
    print("Saved advanced internal structure CSVs!")

if __name__ == "__main__":
    main()
