import pandas as pd
import numpy as np
from numba import njit
import json
import os
import time

def parse_time(t_str):
    parts = t_str.split(':')
    h = int(parts[0])
    m = int(parts[1])
    return h * 60 + m

@njit
def compute_bnf_metrics(
    session_starts, session_ends, mins_arr,
    h_arr, l_arr, windows_arr,
    # Outputs
    prob_db_out,
    hf_lb_out, hf_hb_out, hf_tot_out,
    lf_hb_out, lf_lb_out, lf_tot_out,
    ext_arr, type_arr, dir_arr, window_idx_arr
):
    num_windows = len(windows_arr)
    num_sessions = len(session_starts)
    
    count_ext = 0
    
    for w in range(num_windows):
        start_m = windows_arr[w, 0]
        end_m = windows_arr[w, 1]
        
        valid_sessions = 0
        db_count = 0
        
        # First extreme counters
        hf_tot = 0; hf_lb = 0; hf_hb = 0
        lf_tot = 0; lf_hb = 0; lf_lb = 0
        
        for s in range(num_sessions):
            idx_start = session_starts[s]
            idx_end = session_ends[s]
            
            # Find IB extremes
            ib_h = -1.0
            ib_l = 1e9
            
            has_ib = False
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m >= start_m and m <= end_m:
                    if h_arr[i] > ib_h: ib_h = h_arr[i]
                    if l_arr[i] < ib_l: ib_l = l_arr[i]
                    has_ib = True
                elif m > end_m:
                    break
            
            if not has_ib:
                continue
                
            r = ib_h - ib_l
            if r <= 0:
                continue
                
            valid_sessions += 1
            
            # Analyze breaks and extensions
            first_dir = 0 # 1 for High First, -1 for Low First
            max_ext = 0.0
            is_double = 0
            
            for i in range(idx_start, idx_end):
                m = mins_arr[i]
                if m > end_m:
                    if first_dir == 0:
                        if h_arr[i] > ib_h:
                            first_dir = 1
                            max_ext = h_arr[i] - ib_h
                            if l_arr[i] < ib_l:
                                is_double = 2
                                break
                        elif l_arr[i] < ib_l:
                            first_dir = -1
                            max_ext = ib_l - l_arr[i]
                            if h_arr[i] > ib_h:
                                is_double = 2
                                break
                    else:
                        if first_dir == 1:
                            if l_arr[i] < ib_l:
                                is_double = 2
                                break
                            ext = h_arr[i] - ib_h
                            if ext > max_ext: max_ext = ext
                        else:
                            if h_arr[i] > ib_h:
                                is_double = 2
                                break
                            ext = ib_l - l_arr[i]
                            if ext > max_ext: max_ext = ext
            
            if first_dir != 0:
                if is_double == 0: is_double = 1
                
                # Ext data
                ext_arr[count_ext] = max_ext / r
                type_arr[count_ext] = is_double
                dir_arr[count_ext] = first_dir
                window_idx_arr[count_ext] = w
                count_ext += 1
                
                # DB / First Break stats
                if is_double == 2:
                    db_count += 1
                    
                if first_dir == 1:
                    hf_tot += 1
                    if is_double == 2: hf_lb += 1
                    else: hf_hb += 1
                else:
                    lf_tot += 1
                    if is_double == 2: lf_hb += 1
                    else: lf_lb += 1
        
        prob_db_out[w] = (db_count / valid_sessions * 100.0) if valid_sessions > 0 else 0.0
        hf_tot_out[w] = hf_tot; hf_lb_out[w] = hf_lb; hf_hb_out[w] = hf_hb
        lf_tot_out[w] = lf_tot; lf_hb_out[w] = lf_hb; lf_lb_out[w] = lf_lb

    return count_ext

def get_percentile_matrix(df_subset, windows_labels, percentiles):
    res_list = []
    if len(df_subset) == 0:
        for w in windows_labels:
            res_list.append({"Window": w, **{f"{int(p*100)}%": 0 for p in percentiles}})
        return res_list
        
    grouped = df_subset.groupby('Window_Label')['Extension_R']
    for label in windows_labels:
        if label in grouped.groups:
            g = grouped.get_group(label)
            q = g.quantile(percentiles).round(2).values
            row = {"Window": label}
            for i, p in enumerate(percentiles):
                row[f"{int(p*100)}%"] = float(q[i])
            res_list.append(row)
        else:
            row = {"Window": label}
            for p in percentiles:
                row[f"{int(p*100)}%"] = 0.0
            res_list.append(row)
    return res_list

def generate_for_config(df, config_name, size, step):
    print(f"Generating data for {config_name} (Window: {size}m, Step: {step}m)...")
    
    unique_sessions = df['Date'].unique()
    session_map = {sess: i for i, sess in enumerate(unique_sessions)}
    session_idx_arr = df['Date'].map(session_map).values.astype(np.int32)

    mins_arr = df['Mins'].values.astype(np.int32)
    h_arr = df['High'].values.astype(np.float32)
    l_arr = df['Low'].values.astype(np.float32)

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

    # Windows from 09:15 (555) to 15:30 (930)
    windows_list = []
    labels = []
    
    start_time = 555
    end_limit = 930
    
    while start_time + size - 1 < end_limit:
        end_time = start_time + size - 1
        windows_list.append([start_time, end_time])
        h1 = start_time // 60; m1 = start_time % 60
        h2 = end_time // 60; m2 = end_time % 60
        labels.append(f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}")
        start_time += step

    windows_arr = np.array(windows_list, dtype=np.int32)
    num_windows = len(windows_list)
    max_events = num_windows * num_sessions
    
    # Outputs
    prob_db_out = np.zeros(num_windows, dtype=np.float32)
    hf_lb_out = np.zeros(num_windows, dtype=np.int32)
    hf_hb_out = np.zeros(num_windows, dtype=np.int32)
    hf_tot_out = np.zeros(num_windows, dtype=np.int32)
    lf_hb_out = np.zeros(num_windows, dtype=np.int32)
    lf_lb_out = np.zeros(num_windows, dtype=np.int32)
    lf_tot_out = np.zeros(num_windows, dtype=np.int32)
    
    ext_arr = np.zeros(max_events, dtype=np.float32)
    type_arr = np.zeros(max_events, dtype=np.int32)
    dir_arr = np.zeros(max_events, dtype=np.int32)
    window_idx_arr = np.zeros(max_events, dtype=np.int32)
    
    count_ext = compute_bnf_metrics(
        session_starts, session_ends, mins_arr,
        h_arr, l_arr, windows_arr,
        prob_db_out,
        hf_lb_out, hf_hb_out, hf_tot_out,
        lf_hb_out, lf_lb_out, lf_tot_out,
        ext_arr, type_arr, dir_arr, window_idx_arr
    )
    
    # 1. Prob DB
    prob_list = []
    for w in range(num_windows):
        prob_list.append({
            "Window": labels[w],
            "BNF_DB_Prob": float(prob_db_out[w])
        })
        
    # 2. Prob First
    prob_first_list = []
    for w in range(num_windows):
        h_tot = hf_tot_out[w]; l_tot = lf_tot_out[w]; cond_tot = h_tot + l_tot
        
        hf_lb_p = (hf_lb_out[w] / h_tot * 100) if h_tot > 0 else 0.0
        hf_hb_p = (hf_hb_out[w] / h_tot * 100) if h_tot > 0 else 0.0
        hf_cbm_p = hf_lb_p # CBM (Continuation Before Mean Reversion) logic simplified
        
        lf_hb_p = (lf_hb_out[w] / l_tot * 100) if l_tot > 0 else 0.0
        lf_lb_p = (lf_lb_out[w] / l_tot * 100) if l_tot > 0 else 0.0
        lf_cam_p = lf_hb_p
        
        comb_opp_p = ((hf_lb_out[w] + lf_hb_out[w]) / cond_tot * 100) if cond_tot > 0 else 0.0
        
        prob_first_list.append({
            "Window": labels[w],
            "BNF_H_First_L_Break_Prob": hf_lb_p,
            "BNF_H_First_H_Break_Prob": hf_hb_p,
            "BNF_H_First_CBM_Prob": hf_cbm_p,
            "BNF_L_First_H_Break_Prob": lf_hb_p,
            "BNF_L_First_L_Break_Prob": lf_lb_p,
            "BNF_L_First_CAM_Prob": lf_cam_p,
            "BNF_Comb_Opp_Prob": comb_opp_p,
            "BNF_Comb_Cond_Prob": comb_opp_p
        })
        
    # 3. Extensions
    df_ext = pd.DataFrame({
        'Extension_R': ext_arr[:count_ext],
        'Type': type_arr[:count_ext],
        'Dir': dir_arr[:count_ext],
        'Window_Idx': window_idx_arr[:count_ext]
    })
    df_ext['Window_Label'] = df_ext['Window_Idx'].apply(lambda x: labels[x])
    
    percentiles = np.concatenate(([0.01], np.arange(0.05, 1.05, 0.05)))
    
    ext_obj = {"bnf": {
        "double_break": {},
        "single_break": {},
        "all_breaks": {}
    }}
    
    # Double breaks
    df_db = df_ext[df_ext['Type'] == 2]
    ext_obj["bnf"]["double_break"]["combined"] = get_percentile_matrix(df_db, labels, percentiles)
    ext_obj["bnf"]["double_break"]["high_first"] = get_percentile_matrix(df_db[df_db['Dir'] == 1], labels, percentiles)
    ext_obj["bnf"]["double_break"]["low_first"] = get_percentile_matrix(df_db[df_db['Dir'] == -1], labels, percentiles)
    
    # Single breaks
    df_sb = df_ext[df_ext['Type'] == 1]
    ext_obj["bnf"]["single_break"]["combined"] = get_percentile_matrix(df_sb, labels, percentiles)
    ext_obj["bnf"]["single_break"]["high_first"] = get_percentile_matrix(df_sb[df_sb['Dir'] == 1], labels, percentiles)
    ext_obj["bnf"]["single_break"]["low_first"] = get_percentile_matrix(df_sb[df_sb['Dir'] == -1], labels, percentiles)
    
    # All breaks
    ext_obj["bnf"]["all_breaks"]["combined"] = get_percentile_matrix(df_ext, labels, percentiles)
    ext_obj["bnf"]["all_breaks"]["high_first"] = get_percentile_matrix(df_ext[df_ext['Dir'] == 1], labels, percentiles)
    ext_obj["bnf"]["all_breaks"]["low_first"] = get_percentile_matrix(df_ext[df_ext['Dir'] == -1], labels, percentiles)

    final_json = {
        "prob": prob_list,
        "prob_first": prob_first_list,
        "ext": ext_obj
    }
    
    out_dir = r"d:\Antigravity\banknifty_dashboard\data"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"time_range_{config_name}.js")
    with open(out_path, "w") as f:
        json_str = json.dumps(final_json, separators=(',', ':'))
        f.write(f"window._D = {json_str};\nif (typeof window.onDataLoaded === 'function') window.onDataLoaded();")
        
    print(f"Generated {out_path}")

def main():
    print("Loading Bank Nifty CSV...")
    df = pd.read_csv(r"C:\Users\Ashish Tripathi\Downloads\bank-nifty-1m-data.csv")
    
    # We only care about Date, Time, High, Low
    df = df[['Date', 'Time', 'High', 'Low']]
    df['Mins'] = df['Time'].apply(parse_time)
    
    configs = [
        ("10m", 10, 10),
        ("15m", 15, 15),
        ("30m", 30, 30),
        ("60m", 60, 30),
        ("7m_1m_step", 7, 1),
        ("60m_15m_step", 60, 15),
        ("30m_15m_step", 30, 15),
        ("20m_7m_step", 20, 7),
        ("10m_1m_step", 10, 1)
    ]
    
    for cfg in configs:
        generate_for_config(df, cfg[0], cfg[1], cfg[2])

if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Total processing time: {time.time() - t0:.2f}s")
