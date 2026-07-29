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
def compute_pwr_metrics(
    session_starts, session_ends, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
):
    num_sessions = len(session_starts)
    valid_sessions = 0
    
    # Probabilities
    nq_double_break = 0
    nq_single_break = 0
    nq_no_break = 0
    es_double_break = 0
    es_single_break = 0
    es_no_break = 0
    
    # Correlation
    nq_h_first = 0
    nq_l_first = 0
    es_h_first = 0
    es_l_first = 0
    es_h_given_nq_h = 0
    es_l_given_nq_l = 0
    nq_h_given_es_h = 0
    nq_l_given_es_l = 0
    
    # Delta-T: 0-5, 6-15, 16-30, 31-60, 61-120, >120
    buckets = np.zeros(6, dtype=np.int32)
    total_correlated = 0
    
    for curr_sess in range(1, num_sessions):
        prev_sess = curr_sess - 1
        
        p_start = session_starts[prev_sess]
        p_end = session_ends[prev_sess]
        
        c_start = session_starts[curr_sess]
        c_end = session_ends[curr_sess]
        
        if p_start > p_end or c_start > c_end:
            continue
            
        # 1. Calculate Previous Week Range
        prev_nq_high = -np.inf
        prev_nq_low = np.inf
        prev_es_high = -np.inf
        prev_es_low = np.inf
        
        for i in range(p_start, p_end + 1):
            if nq_h_arr[i] > prev_nq_high: prev_nq_high = nq_h_arr[i]
            if nq_l_arr[i] < prev_nq_low: prev_nq_low = nq_l_arr[i]
            if es_h_arr[i] > prev_es_high: prev_es_high = es_h_arr[i]
            if es_l_arr[i] < prev_es_low: prev_es_low = es_l_arr[i]
            
        nq_first = 0
        es_first = 0
        nq_min = -1
        es_min = -1
        
        nq_broken_high = False
        nq_broken_low = False
        es_broken_high = False
        es_broken_low = False
        
        for i in range(c_start, c_end + 1):
            # Track all breaks for Probability stats
            if nq_h_arr[i] > prev_nq_high: nq_broken_high = True
            if nq_l_arr[i] < prev_nq_low: nq_broken_low = True
            if es_h_arr[i] > prev_es_high: es_broken_high = True
            if es_l_arr[i] < prev_es_low: es_broken_low = True
            
            # Track First Breaks for Correlation and Delta-T
            if nq_first == 0:
                if nq_h_arr[i] > prev_nq_high:
                    nq_first = 1
                    nq_min = i - c_start
                elif nq_l_arr[i] < prev_nq_low:
                    nq_first = 2
                    nq_min = i - c_start
                    
            if es_first == 0:
                if es_h_arr[i] > prev_es_high:
                    es_first = 1
                    es_min = i - c_start
                elif es_l_arr[i] < prev_es_low:
                    es_first = 2
                    es_min = i - c_start
                    
        # Update Probability Stats
        if nq_broken_high and nq_broken_low: nq_double_break += 1
        elif nq_broken_high or nq_broken_low: nq_single_break += 1
        else: nq_no_break += 1
            
        if es_broken_high and es_broken_low: es_double_break += 1
        elif es_broken_high or es_broken_low: es_single_break += 1
        else: es_no_break += 1
        
        # Update Correlation Stats
        if nq_first == 1:
            nq_h_first += 1
            if es_first == 1: es_h_given_nq_h += 1
        elif nq_first == 2:
            nq_l_first += 1
            if es_first == 2: es_l_given_nq_l += 1
                
        if es_first == 1:
            es_h_first += 1
            if nq_first == 1: nq_h_given_es_h += 1
        elif es_first == 2:
            es_l_first += 1
            if nq_first == 2: nq_l_given_es_l += 1
                
        # Update Delta-T Stats
        if nq_first != 0 and es_first != 0 and nq_first == es_first:
            delta = abs(nq_min - es_min)
            total_correlated += 1
            if delta <= 5: buckets[0] += 1
            elif delta <= 15: buckets[1] += 1
            elif delta <= 30: buckets[2] += 1
            elif delta <= 60: buckets[3] += 1
            elif delta <= 120: buckets[4] += 1
            else: buckets[5] += 1
                
        valid_sessions += 1
        
    return (
        valid_sessions,
        nq_double_break, nq_single_break, nq_no_break,
        es_double_break, es_single_break, es_no_break,
        nq_h_first, nq_l_first, es_h_first, es_l_first,
        es_h_given_nq_h, es_l_given_nq_l, nq_h_given_es_h, nq_l_given_es_l,
        total_correlated, buckets
    )

def main():
    results_dir = r"d:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    
    t0 = time.time()
    print("Loading datasets (via pyarrow)...")
    nq_1m = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
    es_1m = pd.read_parquet(r"d:\Antigravity\Historical data\ES Futures Datasets\Full Data\parquet\ES_1m_full_data.parquet")

    nq_1m = nq_1m[['Date', 'Time', 'High', 'Low']].rename(columns={'High': 'NQ_High', 'Low': 'NQ_Low'})
    es_1m = es_1m[['Date', 'Time', 'High', 'Low']].rename(columns={'High': 'ES_High', 'Low': 'ES_Low'})
        
    print("Merging datasets...")
    df = pd.merge(nq_1m, es_1m, on=['Date', 'Time'], how='inner')
    
    print("Computing Session Dates and Weeks...")
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    
    # Group into ISO Weeks
    iso = df['SessionDate'].dt.isocalendar()
    df['Week'] = iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)
    
    print("Sorting...")
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    print("Preparing arrays for Numba JIT compilation...")
    unique_weeks = df['Week'].unique()
    week_map = {w: i for i, w in enumerate(unique_weeks)}
    week_idx_arr = df['Week'].map(week_map).values.astype(np.int32)

    nq_h_arr = df['NQ_High'].values.astype(np.float32)
    nq_l_arr = df['NQ_Low'].values.astype(np.float32)
    es_h_arr = df['ES_High'].values.astype(np.float32)
    es_l_arr = df['ES_Low'].values.astype(np.float32)

    num_weeks = len(unique_weeks)
    week_starts = np.zeros(num_weeks, dtype=np.int32)
    week_ends = np.zeros(num_weeks, dtype=np.int32)

    curr_wk = week_idx_arr[0]
    week_starts[curr_wk] = 0
    for i in range(1, len(week_idx_arr)):
        if week_idx_arr[i] != curr_wk:
            week_ends[curr_wk] = i - 1
            curr_wk = week_idx_arr[i]
            week_starts[curr_wk] = i
    week_ends[curr_wk] = len(week_idx_arr) - 1

    print("Running Numba compiled loop (Blazingly Fast)...")
    t_numba_start = time.time()
    
    (
        valid_weeks,
        nq_db, nq_sb, nq_nb,
        es_db, es_sb, es_nb,
        nq_h_first, nq_l_first, es_h_first, es_l_first,
        es_h_given_nq_h, es_l_given_nq_l, nq_h_given_es_h, nq_l_given_es_l,
        total_corr, buckets
    ) = compute_pwr_metrics(
        week_starts, week_ends, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
    )
    
    t_numba_end = time.time()
    print(f"Numba computation took: {t_numba_end - t_numba_start:.4f} seconds!")
    print(f"Total valid weeks analyzed: {valid_weeks}")
    print("-" * 40)
    
    # Print Probabilities
    print(f"NQ PWR Break Probabilities:")
    print(f"  Double Break: {(nq_db/valid_weeks)*100:.2f}%")
    print(f"  Single Break: {(nq_sb/valid_weeks)*100:.2f}%")
    print(f"  No Break:     {(nq_nb/valid_weeks)*100:.2f}%")
    print(f"ES PWR Break Probabilities:")
    print(f"  Double Break: {(es_db/valid_weeks)*100:.2f}%")
    print(f"  Single Break: {(es_sb/valid_weeks)*100:.2f}%")
    print(f"  No Break:     {(es_nb/valid_weeks)*100:.2f}%")
    print("-" * 40)
    
    # Print Correlation
    p_es_h = (es_h_given_nq_h / nq_h_first * 100) if nq_h_first > 0 else 0
    p_es_l = (es_l_given_nq_l / nq_l_first * 100) if nq_l_first > 0 else 0
    p_nq_h = (nq_h_given_es_h / es_h_first * 100) if es_h_first > 0 else 0
    p_nq_l = (nq_l_given_es_l / es_l_first * 100) if es_l_first > 0 else 0
    print(f"First Break Correlation:")
    print(f"  If NQ High First -> ES High First: {p_es_h:.2f}%")
    print(f"  If NQ Low First  -> ES Low First:  {p_es_l:.2f}%")
    print(f"  If ES High First -> NQ High First: {p_nq_h:.2f}%")
    print(f"  If ES Low First  -> NQ Low First:  {p_nq_l:.2f}%")
    print("-" * 40)
    
    # Print Delta T
    print(f"Delta-T (Time Lag):")
    print(f"  Total correlated breaks evaluated: {total_corr}")
    print(f"  0-5 mins:   {buckets[0]} ({(buckets[0]/total_corr)*100:.2f}%)")
    print(f"  6-15 mins:  {buckets[1]} ({(buckets[1]/total_corr)*100:.2f}%)")
    print(f"  16-30 mins: {buckets[2]} ({(buckets[2]/total_corr)*100:.2f}%)")
    print(f"  31-60 mins: {buckets[3]} ({(buckets[3]/total_corr)*100:.2f}%)")
    print(f"  61-120 mins: {buckets[4]} ({(buckets[4]/total_corr)*100:.2f}%)")
    print(f"  >120 mins:  {buckets[5]} ({(buckets[5]/total_corr)*100:.2f}%)")
    
if __name__ == "__main__":
    main()
