import pandas as pd
import numpy as np
from numba import njit
import time

NQ_PATH = r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet"
ES_PATH = r"d:\Antigravity\Historical data\ES Futures Datasets\Full Data\parquet\ES_1m_full_data.parquet"

@njit
def compute_retracement_arrays(session_starts, session_ends, nq_h, nq_l, es_h, es_l):
    N = len(session_starts)

    nq_retrace = np.zeros(N, dtype=np.float32)
    es_retrace = np.zeros(N, dtype=np.float32)
    nq_cnt = 0
    es_cnt = 0

    for curr in range(1, N):
        prev = curr - 1
        ps = session_starts[prev]; pe = session_ends[prev]
        cs = session_starts[curr]; ce = session_ends[curr]

        if ps > pe or cs > ce: continue

        p_nq_h = -1e10; p_nq_l = 1e10
        p_es_h = -1e10; p_es_l = 1e10
        for i in range(ps, pe + 1):
            if nq_h[i] > p_nq_h: p_nq_h = nq_h[i]
            if nq_l[i] < p_nq_l: p_nq_l = nq_l[i]
            if es_h[i] > p_es_h: p_es_h = es_h[i]
            if es_l[i] < p_es_l: p_es_l = es_l[i]

        nq_pdr = p_nq_h - p_nq_l
        es_pdr = p_es_h - p_es_l
        if nq_pdr <= 0.0 or es_pdr <= 0.0: continue

        nq_break_dir = 0; nq_min_dn = 1e10; nq_max_up = -1e10
        es_break_dir = 0; es_min_dn = 1e10; es_max_up = -1e10

        for i in range(cs, ce + 1):
            # NQ
            if nq_break_dir == 0:
                if nq_h[i] > p_nq_h: nq_break_dir = 1
                elif nq_l[i] < p_nq_l: nq_break_dir = -1
            
            if nq_break_dir == 1:
                if nq_l[i] < nq_min_dn: nq_min_dn = nq_l[i]
            elif nq_break_dir == -1:
                if nq_h[i] > nq_max_up: nq_max_up = nq_h[i]

            # ES
            if es_break_dir == 0:
                if es_h[i] > p_es_h: es_break_dir = 1
                elif es_l[i] < p_es_l: es_break_dir = -1
            
            if es_break_dir == 1:
                if es_l[i] < es_min_dn: es_min_dn = es_l[i]
            elif es_break_dir == -1:
                if es_h[i] > es_max_up: es_max_up = es_h[i]

        if nq_break_dir == 1:
            r = (p_nq_h - nq_min_dn) / nq_pdr
            nq_retrace[nq_cnt] = r
            nq_cnt += 1
        elif nq_break_dir == -1:
            r = (nq_max_up - p_nq_l) / nq_pdr
            nq_retrace[nq_cnt] = r
            nq_cnt += 1
            
        if es_break_dir == 1:
            r = (p_es_h - es_min_dn) / es_pdr
            es_retrace[es_cnt] = r
            es_cnt += 1
        elif es_break_dir == -1:
            r = (es_max_up - p_es_l) / es_pdr
            es_retrace[es_cnt] = r
            es_cnt += 1

    return nq_retrace[:nq_cnt], es_retrace[:es_cnt]

def get_session_date(dt):
    if dt.hour >= 17: return dt.date() + pd.Timedelta(days=1)
    else: return dt.date()

def normalise(df, sym):
    df.columns = [c.strip() for c in df.columns]
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
    elif 'Date' in df.columns and 'Time' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df = df.sort_values('Datetime').reset_index(drop=True)
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    return df[['Datetime', 'SessionDate', 'High', 'Low']].rename(
        columns={'High': f'{sym}_H', 'Low': f'{sym}_L'})

def build_sessions(df):
    sess_dates = df['SessionDate'].values
    unique_sessions, inv = np.unique(sess_dates, return_inverse=True)
    N = len(unique_sessions)
    sess_starts = np.zeros(N, dtype=np.int32)
    sess_ends   = np.zeros(N, dtype=np.int32)
    curr = inv[0]; sess_starts[curr] = 0
    for i in range(1, len(inv)):
        if inv[i] != curr:
            sess_ends[curr] = i - 1
            curr = inv[i]
            sess_starts[curr] = i
    sess_ends[curr] = len(inv) - 1
    return sess_starts, sess_ends

def get_percentiles_dict(arr):
    # We want the probability P of retracing AT LEAST X.
    # This means X is the (100 - P) percentile of the array.
    probs = list(range(100, -5, -5))
    res = {}
    for p in probs:
        perc_val = 100 - p
        val = np.percentile(arr, perc_val)
        if val < 0: val = 0.0
        res[str(p)] = round(float(val), 4)
    return res

def main():
    nq = normalise(pd.read_parquet(NQ_PATH), 'NQ')
    es = normalise(pd.read_parquet(ES_PATH), 'ES')
    df = pd.merge(nq, es, on=['Datetime', 'SessionDate'], how='inner')
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    sess_starts, sess_ends = build_sessions(df)
    
    nq_h_arr = df['NQ_H'].values.astype(np.float32)
    nq_l_arr = df['NQ_L'].values.astype(np.float32)
    es_h_arr = df['ES_H'].values.astype(np.float32)
    es_l_arr = df['ES_L'].values.astype(np.float32)
    
    nq_arr, es_arr = compute_retracement_arrays(sess_starts, sess_ends, nq_h_arr, nq_l_arr, es_h_arr, es_l_arr)
    
    
    out_json = {
        "nq": get_percentiles_dict(nq_arr),
        "es": get_percentiles_dict(es_arr)
    }
    import json
    print(json.dumps(out_json))

if __name__ == "__main__":
    main()
