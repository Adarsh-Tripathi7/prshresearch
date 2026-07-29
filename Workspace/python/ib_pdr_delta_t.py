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
def compute_pdr_delta_t(
    session_starts, session_ends, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
):
    num_sessions = len(session_starts)
    valid_sessions = 0
    
    # 0-5, 6-15, 16-30, 31-60, >60
    buckets = np.zeros(5, dtype=np.int32)
    total_correlated = 0
    
    for curr_sess in range(1, num_sessions):
        prev_sess = curr_sess - 1
        
        p_start = session_starts[prev_sess]
        p_end = session_ends[prev_sess]
        
        c_start = session_starts[curr_sess]
        c_end = session_ends[curr_sess]
        
        if p_start > p_end or c_start > c_end:
            continue
            
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
        
        for i in range(c_start, c_end + 1):
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
                    
            if nq_first != 0 and es_first != 0:
                break
                
        if nq_first != 0 and es_first != 0 and nq_first == es_first:
            delta = abs(nq_min - es_min)
            total_correlated += 1
            if delta <= 5: buckets[0] += 1
            elif delta <= 15: buckets[1] += 1
            elif delta <= 30: buckets[2] += 1
            elif delta <= 60: buckets[3] += 1
            else: buckets[4] += 1
                
        valid_sessions += 1
        
    return total_correlated, buckets

def main():
    t0 = time.time()
    print("Loading datasets (via pyarrow)...")
    nq_1m = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
    es_1m = pd.read_parquet(r"d:\Antigravity\Historical data\ES Futures Datasets\Full Data\parquet\ES_1m_full_data.parquet")

    nq_1m = nq_1m[['Date', 'Time', 'High', 'Low']].rename(columns={'High': 'NQ_High', 'Low': 'NQ_Low'})
    es_1m = es_1m[['Date', 'Time', 'High', 'Low']].rename(columns={'High': 'ES_High', 'Low': 'ES_Low'})
        
    df = pd.merge(nq_1m, es_1m, on=['Date', 'Time'], how='inner')
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    df = df.sort_values('Datetime').reset_index(drop=True)
    
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

    print("Running Numba loop...")
    total_corr, buckets = compute_pdr_delta_t(
        session_starts, session_ends, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
    )
    
    print(f"Total correlated breaks evaluated: {total_corr}")
    print(f"Delta-T 0-5 mins:   {buckets[0]} ({(buckets[0]/total_corr)*100:.2f}%)")
    print(f"Delta-T 6-15 mins:  {buckets[1]} ({(buckets[1]/total_corr)*100:.2f}%)")
    print(f"Delta-T 16-30 mins: {buckets[2]} ({(buckets[2]/total_corr)*100:.2f}%)")
    print(f"Delta-T 31-60 mins: {buckets[3]} ({(buckets[3]/total_corr)*100:.2f}%)")
    print(f"Delta-T >60 mins:   {buckets[4]} ({(buckets[4]/total_corr)*100:.2f}%)")
    
if __name__ == "__main__":
    main()
