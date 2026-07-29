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
def compute_pdr_correlation(
    session_starts, session_ends, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
):
    num_sessions = len(session_starts)
    
    valid_sessions = 0
    
    # Counts
    nq_h_first = 0
    nq_l_first = 0
    es_h_first = 0
    es_l_first = 0
    
    # Joint counts
    es_h_given_nq_h = 0
    es_l_given_nq_l = 0
    nq_h_given_es_h = 0
    nq_l_given_es_l = 0
    
    for curr_sess in range(1, num_sessions):
        prev_sess = curr_sess - 1
        
        p_start = session_starts[prev_sess]
        p_end = session_ends[prev_sess]
        
        c_start = session_starts[curr_sess]
        c_end = session_ends[curr_sess]
        
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
            
        # 2. Find First Break in Current Session
        nq_first = 0 # 1=High, 2=Low
        es_first = 0 # 1=High, 2=Low
        
        for i in range(c_start, c_end + 1):
            if nq_first == 0:
                if nq_h_arr[i] > prev_nq_high:
                    nq_first = 1
                elif nq_l_arr[i] < prev_nq_low:
                    nq_first = 2
                    
            if es_first == 0:
                if es_h_arr[i] > prev_es_high:
                    es_first = 1
                elif es_l_arr[i] < prev_es_low:
                    es_first = 2
                    
            if nq_first != 0 and es_first != 0:
                break
                
        # 3. Update Counts
        if nq_first == 1:
            nq_h_first += 1
            if es_first == 1:
                es_h_given_nq_h += 1
        elif nq_first == 2:
            nq_l_first += 1
            if es_first == 2:
                es_l_given_nq_l += 1
                
        if es_first == 1:
            es_h_first += 1
            if nq_first == 1:
                nq_h_given_es_h += 1
        elif es_first == 2:
            es_l_first += 1
            if nq_first == 2:
                nq_l_given_es_l += 1
                
        valid_sessions += 1
        
    return (
        valid_sessions, 
        nq_h_first, nq_l_first, es_h_first, es_l_first,
        es_h_given_nq_h, es_l_given_nq_l, nq_h_given_es_h, nq_l_given_es_l
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
     nq_h_first, nq_l_first, es_h_first, es_l_first,
     es_h_given_nq_h, es_l_given_nq_l, nq_h_given_es_h, nq_l_given_es_l) = compute_pdr_correlation(
        session_starts, session_ends, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
    )
    
    t_numba_end = time.time()
    print(f"Numba computation took: {t_numba_end - t_numba_start:.4f} seconds!")
    print(f"Total valid sessions analyzed: {valid_sessions}")
    print("-" * 40)
    
    # Calculate %
    p_es_h_given_nq_h = (es_h_given_nq_h / nq_h_first * 100) if nq_h_first > 0 else 0
    p_es_l_given_nq_l = (es_l_given_nq_l / nq_l_first * 100) if nq_l_first > 0 else 0
    p_nq_h_given_es_h = (nq_h_given_es_h / es_h_first * 100) if es_h_first > 0 else 0
    p_nq_l_given_es_l = (nq_l_given_es_l / es_l_first * 100) if es_l_first > 0 else 0
    
    print(f"When NQ Breaks PDR HIGH first:")
    print(f"  -> ES also breaks HIGH first: {p_es_h_given_nq_h:.2f}% ({es_h_given_nq_h}/{nq_h_first})")
    print(f"When NQ Breaks PDR LOW first:")
    print(f"  -> ES also breaks LOW first:  {p_es_l_given_nq_l:.2f}% ({es_l_given_nq_l}/{nq_l_first})")
    
    print(f"\nWhen ES Breaks PDR HIGH first:")
    print(f"  -> NQ also breaks HIGH first: {p_nq_h_given_es_h:.2f}% ({nq_h_given_es_h}/{es_h_first})")
    print(f"When ES Breaks PDR LOW first:")
    print(f"  -> NQ also breaks LOW first:  {p_nq_l_given_es_l:.2f}% ({nq_l_given_es_l}/{es_l_first})")
    print("-" * 40)
    
    # Export to CSV
    results_list = [
        {"Condition": "NQ Breaks High First", "Probability_ES_Follows": p_es_h_given_nq_h},
        {"Condition": "NQ Breaks Low First", "Probability_ES_Follows": p_es_l_given_nq_l},
        {"Condition": "ES Breaks High First", "Probability_NQ_Follows": p_nq_h_given_es_h},
        {"Condition": "ES Breaks Low First", "Probability_NQ_Follows": p_nq_l_given_es_l},
    ]
    
    res_df = pd.DataFrame(results_list)
    csv_path = os.path.join(results_dir, "pdr_first_break_correlation.csv")
    res_df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

if __name__ == "__main__":
    main()
