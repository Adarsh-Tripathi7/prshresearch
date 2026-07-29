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
def compute_db_correlation(session_starts, session_ends, nq_h_arr, nq_l_arr, es_h_arr, es_l_arr):
    num_sessions = len(session_starts)
    
    nq_first_db_count = 0
    es_follows_nq = 0
    
    es_first_db_count = 0
    nq_follows_es = 0
    
    for curr_sess in range(1, num_sessions):
        p_start = session_starts[curr_sess-1]
        p_end = session_ends[curr_sess-1]
        
        c_start = session_starts[curr_sess]
        c_end = session_ends[curr_sess]
        
        if p_start > p_end or c_start > c_end:
            continue
            
        p_nq_h = -np.inf
        p_nq_l = np.inf
        p_es_h = -np.inf
        p_es_l = np.inf
        
        for i in range(p_start, p_end+1):
            if nq_h_arr[i] > p_nq_h: p_nq_h = nq_h_arr[i]
            if nq_l_arr[i] < p_nq_l: p_nq_l = nq_l_arr[i]
            if es_h_arr[i] > p_es_h: p_es_h = es_h_arr[i]
            if es_l_arr[i] < p_es_l: p_es_l = es_l_arr[i]
            
        nq_h_broken = False
        nq_l_broken = False
        es_h_broken = False
        es_l_broken = False
        
        nq_db_min = 9999999
        es_db_min = 9999999
        
        for i in range(c_start, c_end+1):
            if not nq_h_broken and nq_h_arr[i] > p_nq_h: nq_h_broken = True
            if not nq_l_broken and nq_l_arr[i] < p_nq_l: nq_l_broken = True
            if nq_h_broken and nq_l_broken and nq_db_min == 9999999:
                nq_db_min = i
                
            if not es_h_broken and es_h_arr[i] > p_es_h: es_h_broken = True
            if not es_l_broken and es_l_arr[i] < p_es_l: es_l_broken = True
            if es_h_broken and es_l_broken and es_db_min == 9999999:
                es_db_min = i
                
        if nq_db_min < 9999999 and nq_db_min < es_db_min:
            nq_first_db_count += 1
            if es_db_min < 9999999:
                es_follows_nq += 1
                
        elif es_db_min < 9999999 and es_db_min < nq_db_min:
            es_first_db_count += 1
            if nq_db_min < 9999999:
                nq_follows_es += 1
                
    return (nq_first_db_count, es_follows_nq, es_first_db_count, nq_follows_es)

def run_correlation(df, group_col):
    unique_groups = df[group_col].unique()
    group_map = {g: i for i, g in enumerate(unique_groups)}
    idx_arr = df[group_col].map(group_map).values.astype(np.int32)
    
    nq_h_arr = df['NQ_High'].values.astype(np.float32)
    nq_l_arr = df['NQ_Low'].values.astype(np.float32)
    es_h_arr = df['ES_High'].values.astype(np.float32)
    es_l_arr = df['ES_Low'].values.astype(np.float32)

    num_groups = len(unique_groups)
    g_starts = np.zeros(num_groups, dtype=np.int32)
    g_ends = np.zeros(num_groups, dtype=np.int32)

    curr_g = idx_arr[0]
    g_starts[curr_g] = 0
    for i in range(1, len(idx_arr)):
        if idx_arr[i] != curr_g:
            g_ends[curr_g] = i - 1
            curr_g = idx_arr[i]
            g_starts[curr_g] = i
    g_ends[curr_g] = len(idx_arr) - 1
    
    return compute_db_correlation(g_starts, g_ends, nq_h_arr, nq_l_arr, es_h_arr, es_l_arr)

def main():
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
    iso = df['SessionDate'].dt.isocalendar()
    df['Week'] = iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)
    
    print("Sorting...")
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    print("Running Daily Correlation...")
    nq_1_d, es_f_nq_d, es_1_d, nq_f_es_d = run_correlation(df, 'SessionDate')
    
    print("Running Weekly Correlation...")
    nq_1_w, es_f_nq_w, es_1_w, nq_f_es_w = run_correlation(df, 'Week')
    
    print("\n" + "="*50)
    print("DAILY RANGE DOUBLE BREAK CORRELATION")
    print("="*50)
    p_es_f_nq = (es_f_nq_d / nq_1_d * 100) if nq_1_d > 0 else 0
    p_nq_f_es = (nq_f_es_d / es_1_d * 100) if es_1_d > 0 else 0
    print(f"When NQ Double Breaks first: ES follows {p_es_f_nq:.2f}% of the time ({es_f_nq_d}/{nq_1_d})")
    print(f"When ES Double Breaks first: NQ follows {p_nq_f_es:.2f}% of the time ({nq_f_es_d}/{es_1_d})")
    
    print("\n" + "="*50)
    print("WEEKLY RANGE DOUBLE BREAK CORRELATION")
    print("="*50)
    p_es_f_nq_w = (es_f_nq_w / nq_1_w * 100) if nq_1_w > 0 else 0
    p_nq_f_es_w = (nq_f_es_w / es_1_w * 100) if es_1_w > 0 else 0
    print(f"When NQ Double Breaks first: ES follows {p_es_f_nq_w:.2f}% of the time ({es_f_nq_w}/{nq_1_w})")
    print(f"When ES Double Breaks first: NQ follows {p_nq_f_es_w:.2f}% of the time ({nq_f_es_w}/{es_1_w})")
    
if __name__ == "__main__":
    main()
