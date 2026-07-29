import pandas as pd
import numpy as np
from numba import njit
import time
import os

@njit
def calc_probs(session_ids, session_mins, highs, lows, closes, num_sessions, max_minute=1320, window_size=7, step=1):
    num_windows = (max_minute - window_size) // step + 1
    
    # 0 = High First Total
    # 1 = High First -> Low Broken First
    # 2 = High First -> High Broken First
    # 3 = Low First Total
    # 4 = Low First -> High Broken First
    # 5 = Low First -> Low Broken First
    
    # Add new stats:
    # 6 = High First + Close < Mid Total
    # 7 = High First + Close < Mid -> Low Broken First (Opposite break)
    # 8 = Low First + Close > Mid Total
    # 9 = Low First + Close > Mid -> High Broken First (Opposite break)
    results = np.zeros((num_windows, 10), dtype=np.int32)
    
    n = len(session_ids)
    idx = 0
    while idx < n:
        start_idx = idx
        current_session = session_ids[idx]
        
        while idx < n and session_ids[idx] == current_session:
            idx += 1
        end_idx = idx
        
        for w in range(num_windows):
            w_start_min = w * step
            w_end_min = w_start_min + window_size - 1
            
            w_high = -1e9
            w_low = 1e9
            high_time = -1
            low_time = -1
            w_close = 0.0
            has_data = False
            
            # Find window high, low, and their times
            for i in range(start_idx, end_idx):
                m = session_mins[i]
                if m >= w_start_min and m <= w_end_min:
                    if highs[i] > w_high:
                        w_high = highs[i]
                        high_time = m
                    if lows[i] < w_low:
                        w_low = lows[i]
                        low_time = m
                    w_close = closes[i]  # Continuously update to get the last one
                    has_data = True
                elif m > w_end_min:
                    break
                    
            if not has_data or high_time == low_time:
                continue
                
            w_mid = (w_high + w_low) / 2.0
            high_first = high_time < low_time
            
            if high_first:
                results[w, 0] += 1
                if w_close < w_mid:
                    results[w, 6] += 1
            else:
                results[w, 3] += 1
                if w_close > w_mid:
                    results[w, 8] += 1
            
            for i in range(start_idx, end_idx):
                m = session_mins[i]
                if m > w_end_min:
                    broke_high = highs[i] > w_high
                    broke_low = lows[i] < w_low
                    
                    if broke_high and broke_low:
                        # Tie, don't count for either
                        break
                    elif broke_high:
                        if high_first:
                            results[w, 2] += 1
                        else:
                            results[w, 4] += 1
                            if w_close > w_mid:
                                results[w, 9] += 1
                        break
                    elif broke_low:
                        if high_first:
                            results[w, 1] += 1
                            if w_close < w_mid:
                                results[w, 7] += 1
                        else:
                            results[w, 5] += 1
                        break
                        
    return results

def load_data(file_path):
    print(f"Loading {file_path}...")
    df = pd.read_parquet(file_path)
    
    hours = df['Time'].str.slice(0, 2).astype(int)
    minutes = df['Time'].str.slice(3, 5).astype(int)
    
    session_min = np.where(hours >= 18, 
                           (hours - 18) * 60 + minutes, 
                           (hours + 6) * 60 + minutes)
    
    dt = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    session_date = (dt - pd.Timedelta(hours=17)).dt.date
    session_ids = pd.factorize(session_date)[0]
    
    # Remove data after 4 PM (1320 minutes)
    valid = session_min <= 1320
    session_ids = session_ids[valid]
    session_min = session_min[valid]
    highs = df['High'].values.astype(np.float64)[valid]
    lows = df['Low'].values.astype(np.float64)[valid]
    closes = df['Last'].values.astype(np.float64)[valid]
    
    return {
        'session_ids': session_ids.astype(np.int32),
        'session_mins': session_min.astype(np.int32),
        'highs': highs,
        'lows': lows,
        'closes': closes,
        'num_sessions': session_ids.max() + 1
    }

def format_window(w, step=1, window_size=7):
    start_min = w * step
    end_min = start_min + window_size - 1
    
    def min_to_str(m):
        h = (18 + m // 60) % 24
        mm = m % 60
        return f"{h:02d}:{mm:02d}"
        
    return f"{min_to_str(start_min)}-{min_to_str(end_min)}"

def main():
    base_dir = r"d:\Antigravity\Historical data"
    nq_path = os.path.join(base_dir, "NQ Futures Datasets", "Full Data", "parquet", "NQ_1m_full_data.parquet")
    es_path = os.path.join(base_dir, "ES Futures Datasets", "Full Data", "parquet", "ES_1m_full_data.parquet")
    
    # Load once
    nq_data = load_data(nq_path)
    es_data = load_data(es_path)
    
    configs = [
        (10, 10, '10m'),
        (120, 60, '120m'),
        (15, 15, '15m'),
        (15, 1, '15m_1m_step'),
        (30, 30, '30m'),
        (30, 15, '30m_15m_step'),
        (45, 45, '45m'),
        (60, 30, '60m'),
        (7, 7, '7m'),
        (7, 1, '7m_1m_step')
    ]
    
    out_dir = r"d:\Antigravity\Results\FirstExtremeProbs"
    os.makedirs(out_dir, exist_ok=True)
    
    for window_size, step, name in configs:
        print(f"\\nProcessing {name} (Window: {window_size}m, Step: {step}m)...")
        
        t0 = time.time()
        nq_res = calc_probs(nq_data['session_ids'], nq_data['session_mins'], nq_data['highs'], nq_data['lows'], nq_data['closes'], nq_data['num_sessions'], window_size=window_size, step=step)
        es_res = calc_probs(es_data['session_ids'], es_data['session_mins'], es_data['highs'], es_data['lows'], es_data['closes'], es_data['num_sessions'], window_size=window_size, step=step)
        t1 = time.time()
        
        output_data = []
        num_windows = len(nq_res)
        
        for w in range(num_windows):
            nq_hf_tot = nq_res[w, 0]
            nq_hf_lb = nq_res[w, 1]
            nq_hf_hb = nq_res[w, 2]
            nq_lf_tot = nq_res[w, 3]
            nq_lf_hb = nq_res[w, 4]
            nq_lf_lb = nq_res[w, 5]
            
            nq_hf_cbm_tot = nq_res[w, 6]
            nq_hf_cbm_lb = nq_res[w, 7]
            nq_lf_cam_tot = nq_res[w, 8]
            nq_lf_cam_hb = nq_res[w, 9]
            
            es_hf_tot = es_res[w, 0]
            es_hf_lb = es_res[w, 1]
            es_hf_hb = es_res[w, 2]
            es_lf_tot = es_res[w, 3]
            es_lf_hb = es_res[w, 4]
            es_lf_lb = es_res[w, 5]
            
            es_hf_cbm_tot = es_res[w, 6]
            es_hf_cbm_lb = es_res[w, 7]
            es_lf_cam_tot = es_res[w, 8]
            es_lf_cam_hb = es_res[w, 9]
            
            nq_hf_lb_prob = (nq_hf_lb / nq_hf_tot * 100) if nq_hf_tot > 0 else 0
            nq_hf_hb_prob = (nq_hf_hb / nq_hf_tot * 100) if nq_hf_tot > 0 else 0
            nq_lf_hb_prob = (nq_lf_hb / nq_lf_tot * 100) if nq_lf_tot > 0 else 0
            nq_lf_lb_prob = (nq_lf_lb / nq_lf_tot * 100) if nq_lf_tot > 0 else 0
            
            nq_hf_cbm_prob = (nq_hf_cbm_lb / nq_hf_cbm_tot * 100) if nq_hf_cbm_tot > 0 else 0
            nq_lf_cam_prob = (nq_lf_cam_hb / nq_lf_cam_tot * 100) if nq_lf_cam_tot > 0 else 0
            
            es_hf_lb_prob = (es_hf_lb / es_hf_tot * 100) if es_hf_tot > 0 else 0
            es_hf_hb_prob = (es_hf_hb / es_hf_tot * 100) if es_hf_tot > 0 else 0
            es_lf_hb_prob = (es_lf_hb / es_lf_tot * 100) if es_lf_tot > 0 else 0
            es_lf_lb_prob = (es_lf_lb / es_lf_tot * 100) if es_lf_tot > 0 else 0
            
            es_hf_cbm_prob = (es_hf_cbm_lb / es_hf_cbm_tot * 100) if es_hf_cbm_tot > 0 else 0
            es_lf_cam_prob = (es_lf_cam_hb / es_lf_cam_tot * 100) if es_lf_cam_tot > 0 else 0
            
            win_str = format_window(w, step, window_size)
            
            output_data.append({
                "Window": win_str,
                "NQ_HF_Total": nq_hf_tot,
                "NQ_HF_LowBrokenFirst_Prob": round(nq_hf_lb_prob, 2),
                "NQ_HF_HighBrokenFirst_Prob": round(nq_hf_hb_prob, 2),
                "NQ_HF_CBM_Total": nq_hf_cbm_tot,
                "NQ_HF_CBM_Prob": round(nq_hf_cbm_prob, 2),
                "NQ_LF_Total": nq_lf_tot,
                "NQ_LF_HighBrokenFirst_Prob": round(nq_lf_hb_prob, 2),
                "NQ_LF_LowBrokenFirst_Prob": round(nq_lf_lb_prob, 2),
                "NQ_LF_CAM_Total": nq_lf_cam_tot,
                "NQ_LF_CAM_Prob": round(nq_lf_cam_prob, 2),
                "ES_HF_Total": es_hf_tot,
                "ES_HF_LowBrokenFirst_Prob": round(es_hf_lb_prob, 2),
                "ES_HF_HighBrokenFirst_Prob": round(es_hf_hb_prob, 2),
                "ES_HF_CBM_Total": es_hf_cbm_tot,
                "ES_HF_CBM_Prob": round(es_hf_cbm_prob, 2),
                "ES_LF_Total": es_lf_tot,
                "ES_LF_HighBrokenFirst_Prob": round(es_lf_hb_prob, 2),
                "ES_LF_LowBrokenFirst_Prob": round(es_lf_lb_prob, 2),
                "ES_LF_CAM_Total": es_lf_cam_tot,
                "ES_LF_CAM_Prob": round(es_lf_cam_prob, 2)
            })
            
        df_out = pd.DataFrame(output_data)
        out_csv = os.path.join(out_dir, f"{name}.csv")
        df_out.to_csv(out_csv, index=False)
        print(f"Saved to {out_csv} (took {t1-t0:.2f}s)")

if __name__ == "__main__":
    main()
