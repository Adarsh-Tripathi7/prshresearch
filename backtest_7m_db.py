import pandas as pd
import numpy as np
from numba import njit
import time
import os

@njit
def calc_double_breaks(session_ids, session_mins, highs, lows, num_sessions, max_minute=1380, window_size=7):
    # Determine number of full windows
    num_windows = max_minute // window_size
    
    # Store results: [window, 0=total_sessions, 1=double_breaks]
    results = np.zeros((num_windows, 2), dtype=np.int32)
    
    # Pre-allocate durations matrix (initialized to -1)
    # sizes: num_windows x num_sessions
    durations = np.full((num_windows, num_sessions), -1, dtype=np.int32)
    
    # To iterate fast, we can find boundaries of each session
    # Assuming the data is sorted by session_id, then by session_min
    n = len(session_ids)
    
    idx = 0
    while idx < n:
        start_idx = idx
        current_session = session_ids[idx]
        
        # Find end of session
        while idx < n and session_ids[idx] == current_session:
            idx += 1
        end_idx = idx # exclusive
        
        # Now we process this session
        for w in range(num_windows):
            w_start_min = w * window_size
            w_end_min = w_start_min + window_size - 1
            
            w_high = -1e9
            w_low = 1e9
            has_data = False
            
            # 1. Find window high and low
            for i in range(start_idx, end_idx):
                m = session_mins[i]
                if m >= w_start_min and m <= w_end_min:
                    if highs[i] > w_high: w_high = highs[i]
                    if lows[i] < w_low: w_low = lows[i]
                    has_data = True
                elif m > w_end_min:
                    # Since mins are sorted, we can stop early
                    break
                    
            if not has_data:
                continue
                
            results[w, 0] += 1 # Total valid sessions for this window
            
            # 2. Check for double break in remainder of session
            broken_high = False
            broken_low = False
            break_minute = -1
            
            for i in range(start_idx, end_idx):
                m = session_mins[i]
                if m > w_end_min:
                    if highs[i] > w_high:
                        broken_high = True
                    if lows[i] < w_low:
                        broken_low = True
                        
                    if broken_high and broken_low:
                        break_minute = m
                        break # Both broken, no need to check further
                        
            if broken_high and broken_low:
                results[w, 1] += 1
                durations[w, current_session] = break_minute - w_end_min
                
    return results, durations

def process_asset(file_path):
    print(f"Loading {file_path}...")
    df = pd.read_parquet(file_path)
    
    # Fast convert Time (HH:MM:SS) to session minutes
    print("Computing session minutes...")
    hours = df['Time'].str.slice(0, 2).astype(int)
    minutes = df['Time'].str.slice(3, 5).astype(int)
    
    session_min = np.where(hours >= 18, 
                           (hours - 18) * 60 + minutes, 
                           (hours + 6) * 60 + minutes)
    df['session_min'] = session_min
    
    print("Grouping by session...")
    df['dt'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['session_date'] = (df['dt'] - pd.Timedelta(hours=17)).dt.date
    
    session_ids = df.groupby('session_date').ngroup().values
    
    print("Running Numba backtest...")
    t0 = time.time()
    res, durs = calc_double_breaks(
        session_ids.astype(np.int32),
        df['session_min'].values.astype(np.int32),
        df['High'].values.astype(np.float64),
        df['Low'].values.astype(np.float64),
        num_sessions=session_ids.max() + 1
    )
    t1 = time.time()
    print(f"Numba execution took {t1 - t0:.3f} seconds")
    
    return res, durs

def format_window(w, window_size=7):
    start_min = w * window_size
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
    
    nq_res, nq_durs = process_asset(nq_path)
    es_res, es_durs = process_asset(es_path)
    
    print("\n--- RESULTS (First 10 Windows) ---")
    print(f"{'Window':<15} | {'NQ DB %':<10} | {'NQ P50 (min)':<12} | {'ES DB %':<10} | {'ES P50 (min)':<12}")
    print("-" * 70)
    
    output_data = []
    
    num_windows = len(nq_res)
    for w in range(num_windows):
        nq_tot, nq_db = nq_res[w]
        es_tot, es_db = es_res[w]
        
        nq_pct = (nq_db / nq_tot * 100) if nq_tot > 0 else 0
        es_pct = (es_db / es_tot * 100) if es_tot > 0 else 0
        
        # Calculate percentiles for durations
        nq_valid_durs = nq_durs[w][nq_durs[w] != -1]
        es_valid_durs = es_durs[w][es_durs[w] != -1]
        
        nq_p10 = nq_p25 = nq_p50 = nq_p75 = nq_p90 = np.nan
        if len(nq_valid_durs) > 0:
            nq_p10, nq_p25, nq_p50, nq_p75, nq_p90 = np.percentile(nq_valid_durs, [10, 25, 50, 75, 90])
            
        es_p10 = es_p25 = es_p50 = es_p75 = es_p90 = np.nan
        if len(es_valid_durs) > 0:
            es_p10, es_p25, es_p50, es_p75, es_p90 = np.percentile(es_valid_durs, [10, 25, 50, 75, 90])

        win_str = format_window(w)
        
        row_data = {
            "Window": win_str,
            "NQ_Total": nq_tot,
            "NQ_DB_Prob": round(nq_pct, 2),
            "NQ_P10_min": round(nq_p10, 1) if not np.isnan(nq_p10) else None,
            "NQ_P25_min": round(nq_p25, 1) if not np.isnan(nq_p25) else None,
            "NQ_P50_min": round(nq_p50, 1) if not np.isnan(nq_p50) else None,
            "NQ_P75_min": round(nq_p75, 1) if not np.isnan(nq_p75) else None,
            "NQ_P90_min": round(nq_p90, 1) if not np.isnan(nq_p90) else None,
            "ES_Total": es_tot,
            "ES_DB_Prob": round(es_pct, 2),
            "ES_P10_min": round(es_p10, 1) if not np.isnan(es_p10) else None,
            "ES_P25_min": round(es_p25, 1) if not np.isnan(es_p25) else None,
            "ES_P50_min": round(es_p50, 1) if not np.isnan(es_p50) else None,
            "ES_P75_min": round(es_p75, 1) if not np.isnan(es_p75) else None,
            "ES_P90_min": round(es_p90, 1) if not np.isnan(es_p90) else None,
        }
        
        output_data.append(row_data)
        
        if w < 10:
            nq_med = f"{nq_p50:.1f}m" if not np.isnan(nq_p50) else "N/A"
            es_med = f"{es_p50:.1f}m" if not np.isnan(es_p50) else "N/A"
            print(f"{win_str:<15} | {nq_pct:>8.2f}% | {nq_med:<12} | {es_pct:>8.2f}% | {es_med:<12}")
            
    df_out = pd.DataFrame(output_data)
    out_csv = r"d:\Antigravity\Results\7m_double_break_with_time.csv"
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df_out.to_csv(out_csv, index=False)
    print(f"\nSaved full results to {out_csv}")

if __name__ == "__main__":
    main()
