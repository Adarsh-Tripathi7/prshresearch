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

@njit
def compute_pdr_probabilities(
    session_starts, session_ends, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
):
    num_sessions = len(session_starts)
    
    # We skip session 0 because it has no previous session
    valid_sessions = 0
    
    nq_double_break = 0
    nq_single_break = 0
    nq_no_break = 0
    
    es_double_break = 0
    es_single_break = 0
    es_no_break = 0
    
    for curr_sess in range(1, num_sessions):
        prev_sess = curr_sess - 1
        
        p_start = session_starts[prev_sess]
        p_end = session_ends[prev_sess]
        
        c_start = session_starts[curr_sess]
        c_end = session_ends[curr_sess]
        
        # If any session is empty, skip
        if p_start > p_end or c_start > c_end:
            continue
            
        # 1. Calculate Previous Session Range
        prev_nq_high = -np.inf
        prev_nq_low = np.inf
        prev_es_high = -np.inf
        prev_es_low = np.inf
        
        for i in range(p_start, p_end + 1):
            if nq_h_arr[i] > prev_nq_high: prev_nq_high = nq_h_arr[i]
            if nq_l_arr[i] < prev_nq_low: prev_nq_low = nq_l_arr[i]
            if es_h_arr[i] > prev_es_high: prev_es_high = es_h_arr[i]
            if es_l_arr[i] < prev_es_low: prev_es_low = es_l_arr[i]
            
        # 2. Scan Current Session for Breaks
        nq_broken_high = False
        nq_broken_low = False
        es_broken_high = False
        es_broken_low = False
        
        for i in range(c_start, c_end + 1):
            if nq_h_arr[i] > prev_nq_high: nq_broken_high = True
            if nq_l_arr[i] < prev_nq_low: nq_broken_low = True
            
            if es_h_arr[i] > prev_es_high: es_broken_high = True
            if es_l_arr[i] < prev_es_low: es_broken_low = True
            
            # Optimization: if both double broke, we can exit early
            if nq_broken_high and nq_broken_low and es_broken_high and es_broken_low:
                break
                
        # 3. Categorize NQ
        if nq_broken_high and nq_broken_low:
            nq_double_break += 1
        elif nq_broken_high or nq_broken_low:
            nq_single_break += 1
        else:
            nq_no_break += 1
            
        # 4. Categorize ES
        if es_broken_high and es_broken_low:
            es_double_break += 1
        elif es_broken_high or es_broken_low:
            es_single_break += 1
        else:
            es_no_break += 1
            
        valid_sessions += 1
        
    return (
        valid_sessions, 
        nq_double_break, nq_single_break, nq_no_break,
        es_double_break, es_single_break, es_no_break
    )

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
    
    print("Computing Session Dates...")
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    
    print("Sorting...")
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    print("Preparing arrays for Numba JIT compilation...")
    unique_sessions = df['SessionDate'].unique()
    session_map = {sess: i for i, sess in enumerate(unique_sessions)}
    session_idx_arr = df['SessionDate'].map(session_map).values.astype(np.int32)

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
            session_ends[curr_sess] = i - 1
            curr_sess = session_idx_arr[i]
            session_starts[curr_sess] = i
    session_ends[curr_sess] = len(session_idx_arr) - 1

    print("Running Numba compiled loop (Blazingly Fast)...")
    t_numba_start = time.time()
    
    (valid_sessions, 
     nq_db, nq_sb, nq_nb,
     es_db, es_sb, es_nb) = compute_pdr_probabilities(
        session_starts, session_ends, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
    )
    
    t_numba_end = time.time()
    print(f"Numba computation took: {t_numba_end - t_numba_start:.4f} seconds!")
    print(f"Total valid sessions analyzed: {valid_sessions}")
    print("-" * 40)
    
    # Calculate %
    nq_db_pct = (nq_db / valid_sessions) * 100
    nq_sb_pct = (nq_sb / valid_sessions) * 100
    nq_nb_pct = (nq_nb / valid_sessions) * 100
    
    es_db_pct = (es_db / valid_sessions) * 100
    es_sb_pct = (es_sb / valid_sessions) * 100
    es_nb_pct = (es_nb / valid_sessions) * 100
    
    print(f"NQ PDR Break Probabilities:")
    print(f"  Double Break: {nq_db_pct:.2f}%")
    print(f"  Single Break: {nq_sb_pct:.2f}%")
    print(f"  No Break:     {nq_nb_pct:.2f}%")
    
    print(f"\nES PDR Break Probabilities:")
    print(f"  Double Break: {es_db_pct:.2f}%")
    print(f"  Single Break: {es_sb_pct:.2f}%")
    print(f"  No Break:     {es_nb_pct:.2f}%")
    print("-" * 40)
    
    # Export to CSV
    results_list = [
        {"Asset": "NQ", "Total_Sessions": valid_sessions, "Double_Break_Prob": nq_db_pct, "Single_Break_Prob": nq_sb_pct, "No_Break_Prob": nq_nb_pct},
        {"Asset": "ES", "Total_Sessions": valid_sessions, "Double_Break_Prob": es_db_pct, "Single_Break_Prob": es_sb_pct, "No_Break_Prob": es_nb_pct},
    ]
    
    res_df = pd.DataFrame(results_list)
    csv_path = os.path.join(results_dir, "previous_day_range_probs.csv")
    res_df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

if __name__ == "__main__":
    main()
