import pandas as pd
import numpy as np
from numba import njit
import matplotlib.pyplot as plt
import seaborn as sns
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
def compute_extensions(
    session_starts, session_ends, mins_arr, 
    nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr,
    ext_arr_nq, type_arr_nq, dir_arr_nq, ext_arr_es, type_arr_es, dir_arr_es,
    window_idx_arr_nq, window_idx_arr_es
):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    
    count_nq = 0
    count_es = 0
    
    for w in range(num_windows):
        start_m = windows_arr[w, 0]
        end_m = windows_arr[w, 1]
        
        for s in range(num_sessions):
            idx_start = session_starts[s]
            idx_end = session_ends[s]
            
            # Find IB extremes
            ib_nq_h = -1.0
            ib_nq_l = 1e9
            ib_es_h = -1.0
            ib_es_l = 1e9
            
            has_ib = False
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m >= start_m and m <= end_m:
                    if nq_h_arr[i] > ib_nq_h: ib_nq_h = nq_h_arr[i]
                    if nq_l_arr[i] < ib_nq_l: ib_nq_l = nq_l_arr[i]
                    if es_h_arr[i] > ib_es_h: ib_es_h = es_h_arr[i]
                    if es_l_arr[i] < ib_es_l: ib_es_l = es_l_arr[i]
                    has_ib = True
                elif m > end_m:
                    break
                    
            if not has_ib:
                continue
                
            nq_r = ib_nq_h - ib_nq_l
            es_r = ib_es_h - ib_es_l
            if nq_r <= 0 or es_r <= 0:
                continue
                
            # Process NQ
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
            
            if nq_first_dir != 0:
                if nq_is_double == 0: nq_is_double = 1
                ext_arr_nq[count_nq] = nq_max_ext / nq_r
                type_arr_nq[count_nq] = nq_is_double
                dir_arr_nq[count_nq] = nq_first_dir
                window_idx_arr_nq[count_nq] = w
                count_nq += 1
                
            # Process ES
            es_first_dir = 0
            es_max_ext = 0.0
            es_is_double = 0
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m:
                    if es_first_dir == 0:
                        if es_h_arr[i] > ib_es_h:
                            es_first_dir = 1
                            es_max_ext = es_h_arr[i] - ib_es_h
                            if es_l_arr[i] < ib_es_l:
                                es_is_double = 2
                                break
                        elif es_l_arr[i] < ib_es_l:
                            es_first_dir = -1
                            es_max_ext = ib_es_l - es_l_arr[i]
                            if es_h_arr[i] > ib_es_h:
                                es_is_double = 2
                                break
                    else:
                        if es_first_dir == 1:
                            if es_l_arr[i] < ib_es_l:
                                es_is_double = 2
                                break
                            ext = es_h_arr[i] - ib_es_h
                            if ext > es_max_ext: es_max_ext = ext
                        else:
                            if es_h_arr[i] > ib_es_h:
                                es_is_double = 2
                                break
                            ext = ib_es_l - es_l_arr[i]
                            if ext > es_max_ext: es_max_ext = ext
            
            if es_first_dir != 0:
                if es_is_double == 0: es_is_double = 1
                ext_arr_es[count_es] = es_max_ext / es_r
                type_arr_es[count_es] = es_is_double
                dir_arr_es[count_es] = es_first_dir
                window_idx_arr_es[count_es] = w
                count_es += 1
                
    return count_nq, count_es

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
    
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    df['Mins'] = df['Datetime'].apply(calc_mins_from_start)
    
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    print("Preparing arrays for Numba JIT compilation...")
    unique_sessions = df['SessionDate'].unique()
    session_map = {sess: i for i, sess in enumerate(unique_sessions)}
    session_idx_arr = df['SessionDate'].map(session_map).values.astype(np.int32)

    mins_arr = df['Mins'].values.astype(np.int32)
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
            session_ends[curr_sess] = i
            curr_sess = session_idx_arr[i]
            session_starts[curr_sess] = i
    session_ends[curr_sess] = len(session_idx_arr)

    # Generate windows
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
        start_time += 15
    
    windows_arr = np.array(windows_list, dtype=np.int32)
    
    max_events = len(windows_list) * num_sessions
    ext_arr_nq = np.zeros(max_events, dtype=np.float32)
    type_arr_nq = np.zeros(max_events, dtype=np.int32)
    dir_arr_nq = np.zeros(max_events, dtype=np.int32)
    window_idx_arr_nq = np.zeros(max_events, dtype=np.int32)
    
    ext_arr_es = np.zeros(max_events, dtype=np.float32)
    type_arr_es = np.zeros(max_events, dtype=np.int32)
    dir_arr_es = np.zeros(max_events, dtype=np.int32)
    window_idx_arr_es = np.zeros(max_events, dtype=np.int32)
    
    print("Running Extension Analysis (Numba JIT)...")
    t_numba_start = time.time()
    c_nq, c_es = compute_extensions(
        session_starts, session_ends, mins_arr, 
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr, windows_arr,
        ext_arr_nq, type_arr_nq, dir_arr_nq, ext_arr_es, type_arr_es, dir_arr_es,
        window_idx_arr_nq, window_idx_arr_es
    )
    t_numba_end = time.time()
    print(f"Numba computation took: {t_numba_end - t_numba_start:.4f} seconds!")

    # ---------------------------------------------------------
    # BUILD RESULTS
    # ---------------------------------------------------------
    df_nq = pd.DataFrame({
        'Extension_R': ext_arr_nq[:c_nq],
        'Type': type_arr_nq[:c_nq],
        'Dir': dir_arr_nq[:c_nq],
        'Window_Idx': window_idx_arr_nq[:c_nq]
    })
    df_nq['Asset'] = 'NQ'
    
    df_es = pd.DataFrame({
        'Extension_R': ext_arr_es[:c_es],
        'Type': type_arr_es[:c_es],
        'Dir': dir_arr_es[:c_es],
        'Window_Idx': window_idx_arr_es[:c_es]
    })
    df_es['Asset'] = 'ES'
    
    res_df = pd.concat([df_nq, df_es])
    res_df['Type_Str'] = res_df['Type'].map({1: 'Single Break (Trend)', 2: 'Double Break (Fake-out)'})
    res_df['Window_Label'] = res_df['Window_Idx'].apply(lambda x: labels[x])
    
    # Calculate percentiles (5% to 100%)
    percentiles = np.concatenate(([0.01], np.arange(0.05, 1.05, 0.05)))
    
    def get_percentile_matrix(df_subset, filename_prefix):
        if len(df_subset) == 0: return pd.DataFrame()
        
        grouped = df_subset.groupby('Window_Label')['Extension_R']
        res_list = []
        for label in labels:
            if label in grouped.groups:
                g = grouped.get_group(label)
                q = g.quantile(percentiles).round(2).values
                res_list.append([label] + list(q))
            else:
                res_list.append([label] + [np.nan]*len(percentiles))
                
        cols = ['Window'] + [f"{int(p*100)}%" for p in percentiles]
        df_pct = pd.DataFrame(res_list, columns=cols)
        
        csv_path = os.path.join(results_dir, f"{filename_prefix}_percentiles_15m_step.csv")
        df_pct.to_csv(csv_path, index=False)
        return df_pct

    print("Generating Matrices and CSVs...")
    nq_db = res_df[(res_df['Asset'] == 'NQ') & (res_df['Type'] == 2)]
    nq_sb = res_df[(res_df['Asset'] == 'NQ') & (res_df['Type'] == 1)]
    es_db = res_df[(res_df['Asset'] == 'ES') & (res_df['Type'] == 2)]
    es_sb = res_df[(res_df['Asset'] == 'ES') & (res_df['Type'] == 1)]
    
    nq_all = res_df[res_df['Asset'] == 'NQ']
    es_all = res_df[res_df['Asset'] == 'ES']
    
    # Combined (regardless of direction)
    nq_db_df = get_percentile_matrix(nq_db, "nq_double_break_combined")
    nq_sb_df = get_percentile_matrix(nq_sb, "nq_single_break_combined")
    nq_ab_df = get_percentile_matrix(nq_all, "nq_all_breaks_combined")
    
    es_db_df = get_percentile_matrix(es_db, "es_double_break_combined")
    es_sb_df = get_percentile_matrix(es_sb, "es_single_break_combined")
    es_ab_df = get_percentile_matrix(es_all, "es_all_breaks_combined")
    
    # Directional
    nq_db_h_df = get_percentile_matrix(nq_db[nq_db['Dir'] == 1], "nq_double_break_high_first")
    nq_db_l_df = get_percentile_matrix(nq_db[nq_db['Dir'] == -1], "nq_double_break_low_first")
    nq_sb_h_df = get_percentile_matrix(nq_sb[nq_sb['Dir'] == 1], "nq_single_break_high_first")
    nq_sb_l_df = get_percentile_matrix(nq_sb[nq_sb['Dir'] == -1], "nq_single_break_low_first")
    nq_ab_h_df = get_percentile_matrix(nq_all[nq_all['Dir'] == 1], "nq_all_breaks_high_first")
    nq_ab_l_df = get_percentile_matrix(nq_all[nq_all['Dir'] == -1], "nq_all_breaks_low_first")
    
    es_db_h_df = get_percentile_matrix(es_db[es_db['Dir'] == 1], "es_double_break_high_first")
    es_db_l_df = get_percentile_matrix(es_db[es_db['Dir'] == -1], "es_double_break_low_first")
    es_sb_h_df = get_percentile_matrix(es_sb[es_sb['Dir'] == 1], "es_single_break_high_first")
    es_sb_l_df = get_percentile_matrix(es_sb[es_sb['Dir'] == -1], "es_single_break_low_first")
    es_ab_h_df = get_percentile_matrix(es_all[es_all['Dir'] == 1], "es_all_breaks_high_first")
    es_ab_l_df = get_percentile_matrix(es_all[es_all['Dir'] == -1], "es_all_breaks_low_first")
    
    total_time = time.time() - t0
    
    def df_to_markdown(df):
        if df.empty: return ""
        cols = df.columns.tolist()
        res = "| " + " | ".join(cols) + " |\n"
        res += "|" + "|".join(["---"] * len(cols)) + "|\n"
        for _, row in df.iterrows():
            vals = [str(v) if pd.notnull(v) else "" for v in row.values]
            res += "| " + " | ".join(vals) + " |\n"
        return res

    report = f"""# 📏 Breakout Excursion: 'R' Multiples by Time Window (Directional)
*Quantifying the Maximum Favorable Excursion (MFE) of IB breakouts before a reversal or session end, strictly categorized by which side (High vs Low) broke first.*

**1R is strictly defined as the distance between the IB High and IB Low for that specific 60-minute window.**

## 📂 Exported Datasets (CSV)
Due to the massive size of the data (40 rows x 20 percentile columns across 8 matrices), the raw data matrices have been saved to your `Results` folder as CSVs:
- `nq_double_break_high_first_percentiles_15m_step.csv`
- `nq_double_break_low_first_percentiles_15m_step.csv`
- `nq_single_break_high_first_percentiles_15m_step.csv`
- `nq_single_break_low_first_percentiles_15m_step.csv`
- `es_double_break_high_first_percentiles_15m_step.csv`
- `es_double_break_low_first_percentiles_15m_step.csv`
- `es_single_break_high_first_percentiles_15m_step.csv`
- `es_single_break_low_first_percentiles_15m_step.csv`

## 📊 NQ Percentile Matrices

### NQ Double Breaks (High Broken First)
*Maximum profit before the fake-out reversed to stop you out at the IB Low.*
{df_to_markdown(nq_db_h_df)}

### NQ Double Breaks (Low Broken First)
*Maximum profit before the fake-out reversed to stop you out at the IB High.*
{df_to_markdown(nq_db_l_df)}

### NQ Single Breaks (High Broken First / Trend Long)
*Maximum profit if you buy a breakout that never reverses.*
{df_to_markdown(nq_sb_h_df)}

### NQ Single Breaks (Low Broken First / Trend Short)
*Maximum profit if you short a breakout that never reverses.*
{df_to_markdown(nq_sb_l_df)}

## 📊 ES Percentile Matrices

### ES Double Breaks (High Broken First)
{df_to_markdown(es_db_h_df)}

### ES Double Breaks (Low Broken First)
{df_to_markdown(es_db_l_df)}

### ES Single Breaks (High Broken First / Trend Long)
{df_to_markdown(es_sb_h_df)}

### ES Single Breaks (Low Broken First / Trend Short)
{df_to_markdown(es_sb_l_df)}

## 💡 Quantitative Conclusion
You now have the exact directional R-multiple extension parameters for **every single time window** of the day. 
"""

    dashboard_path = os.path.join(results_dir, "ib_extension_detailed_dashboard_15m_step.md")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Dashboard saved to {dashboard_path}")

if __name__ == "__main__":
    main()
