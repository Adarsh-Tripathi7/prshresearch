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
def compute_pdr_by_weekday(
    session_starts, session_ends, session_weekdays,
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
):
    num_sessions = len(session_starts)
    
    # [Mon, Tue, Wed, Thu, Fri] -> indices 0,1,2,3,4
    # Store counts: 0: Valid, 1: NQ_DB, 2: NQ_SB, 3: NQ_NB, 4: ES_DB, 5: ES_SB, 6: ES_NB
    res = np.zeros((5, 7), dtype=np.int32)
    
    for curr_sess in range(1, num_sessions):
        prev_sess = curr_sess - 1
        
        p_start = session_starts[prev_sess]
        p_end = session_ends[prev_sess]
        c_start = session_starts[curr_sess]
        c_end = session_ends[curr_sess]
        
        if p_start > p_end or c_start > c_end:
            continue
            
        wd = session_weekdays[curr_sess]
        if wd > 4 or wd < 0:
            continue # Skip weekends if any anomalies exist
            
        # 1. Calc prev day range
        p_nq_h = -np.inf
        p_nq_l = np.inf
        p_es_h = -np.inf
        p_es_l = np.inf
        for i in range(p_start, p_end+1):
            if nq_h_arr[i] > p_nq_h: p_nq_h = nq_h_arr[i]
            if nq_l_arr[i] < p_nq_l: p_nq_l = nq_l_arr[i]
            if es_h_arr[i] > p_es_h: p_es_h = es_h_arr[i]
            if es_l_arr[i] < p_es_l: p_es_l = es_l_arr[i]
            
        # 2. Check current day breaks
        nq_h_broken = False
        nq_l_broken = False
        es_h_broken = False
        es_l_broken = False
        
        for i in range(c_start, c_end+1):
            if nq_h_arr[i] > p_nq_h: nq_h_broken = True
            if nq_l_arr[i] < p_nq_l: nq_l_broken = True
            if es_h_arr[i] > p_es_h: es_h_broken = True
            if es_l_arr[i] < p_es_l: es_l_broken = True
                
        # 3. Categorize
        res[wd, 0] += 1 # Valid
        if nq_h_broken and nq_l_broken: res[wd, 1] += 1
        elif nq_h_broken or nq_l_broken: res[wd, 2] += 1
        else: res[wd, 3] += 1
            
        if es_h_broken and es_l_broken: res[wd, 4] += 1
        elif es_h_broken or es_l_broken: res[wd, 5] += 1
        else: res[wd, 6] += 1
                
    return res

def main():
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
    
    sess_df = pd.DataFrame({'SessionDate': unique_sessions})
    sess_df['Weekday'] = sess_df['SessionDate'].dt.weekday
    session_weekdays = sess_df['Weekday'].values.astype(np.int32)

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
    res = compute_pdr_by_weekday(
        session_starts, session_ends, session_weekdays,
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr
    )
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for i in range(5):
        valid = res[i, 0]
        if valid == 0: continue
        print(f"\n========================================")
        print(f"{days[i].upper()} (N={valid})")
        print(f"========================================")
        
        nq_db = res[i, 1] / valid * 100
        nq_sb = res[i, 2] / valid * 100
        nq_nb = res[i, 3] / valid * 100
        es_db = res[i, 4] / valid * 100
        es_sb = res[i, 5] / valid * 100
        es_nb = res[i, 6] / valid * 100
        
        print(f"NQ -> Single: {nq_sb:.2f}%, Double: {nq_db:.2f}%, Inside: {nq_nb:.2f}%")
        print(f"ES -> Single: {es_sb:.2f}%, Double: {es_db:.2f}%, Inside: {es_nb:.2f}%")
        
if __name__ == "__main__":
    main()
