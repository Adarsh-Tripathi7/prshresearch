import pandas as pd
import numpy as np
from numba import njit
import time
import os
import json

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

@njit
def compute_detailed_stats(session_ids, session_mins, highs, lows, closes, window_size=60, step=30, max_minute=1320):
    num_windows = (max_minute - window_size) // step + 1
    
    # top_stats: [num_windows, 6, 12]
    # 0: top_total, 1: top_hb_first, 2: top_hb_ever, 3: top_lb_first
    # 4: lf_total, 5: lf_hb_first, 6: lf_hb_ever, 7: lf_lb_first
    # 8: hf_total, 9: hf_hb_first, 10: hf_hb_ever, 11: hf_lb_first
    top_stats = np.zeros((num_windows, 6, 12), dtype=np.int32)
    
    # bot_stats: [num_windows, 6, 12]
    # 0: bot_total, 1: bot_lb_first, 2: bot_lb_ever, 3: bot_hb_first
    # 4: hf_total, 5: hf_lb_first, 6: hf_lb_ever, 7: hf_hb_first
    # 8: lf_total, 9: lf_lb_first, 10: lf_lb_ever, 11: lf_hb_first
    bot_stats = np.zeros((num_windows, 6, 12), dtype=np.int32)
    
    # extreme_stats: [num_windows, 8]
    # 0: hf_total, 1: hf_lb_first, 2: hf_hb_first, 3: hf_lb_ever
    # 4: lf_total, 5: lf_hb_first, 6: lf_lb_first, 7: lf_hb_ever
    extreme_stats = np.zeros((num_windows, 8), dtype=np.int32)
    
    top_thresholds = np.array([0.75, 0.70, 0.65, 0.60, 0.55, 0.50])
    bot_thresholds = np.array([0.25, 0.30, 0.35, 0.40, 0.45, 0.50])
    
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
            
            for i in range(start_idx, end_idx):
                m = session_mins[i]
                if m >= w_start_min and m <= w_end_min:
                    if highs[i] > w_high:
                        w_high = highs[i]
                        high_time = m
                    if lows[i] < w_low:
                        w_low = lows[i]
                        low_time = m
                    w_close = closes[i]
                    has_data = True
                elif m > w_end_min:
                    break
                    
            if not has_data or high_time == low_time or (w_high - w_low) <= 0:
                continue
                
            w_range = w_high - w_low
            close_pos = (w_close - w_low) / w_range
            high_first = high_time < low_time
            low_first = not high_first
            
            # Post window outcome
            hb_first = False
            lb_first = False
            first_break_found = False
            hb_ever = False
            lb_ever = False
            
            for i in range(start_idx, end_idx):
                m = session_mins[i]
                if m > w_end_min:
                    b_high = highs[i] > w_high
                    b_low = lows[i] < w_low
                    
                    if b_high: hb_ever = True
                    if b_low: lb_ever = True
                    
                    if not first_break_found:
                        if b_high and b_low:
                            # Simultaneous break in same 1m bar: tie
                            first_break_found = True
                        elif b_high:
                            hb_first = True
                            first_break_found = True
                        elif b_low:
                            lb_first = True
                            first_break_found = True
                            
            # Record extreme stats
            if high_first:
                extreme_stats[w, 0] += 1
                if lb_first: extreme_stats[w, 1] += 1
                if hb_first: extreme_stats[w, 2] += 1
                if lb_ever:  extreme_stats[w, 3] += 1
            else:
                extreme_stats[w, 4] += 1
                if hb_first: extreme_stats[w, 5] += 1
                if lb_first: extreme_stats[w, 6] += 1
                if hb_ever:  extreme_stats[w, 7] += 1
                
            # Record Top close stats across 6 thresholds
            for t in range(6):
                th = top_thresholds[t]
                if close_pos >= th:
                    top_stats[w, t, 0] += 1
                    if hb_first: top_stats[w, t, 1] += 1
                    if hb_ever:  top_stats[w, t, 2] += 1
                    if lb_first: top_stats[w, t, 3] += 1
                    
                    if low_first:
                        top_stats[w, t, 4] += 1
                        if hb_first: top_stats[w, t, 5] += 1
                        if hb_ever:  top_stats[w, t, 6] += 1
                        if lb_first: top_stats[w, t, 7] += 1
                    else:
                        top_stats[w, t, 8] += 1
                        if hb_first: top_stats[w, t, 9] += 1
                        if hb_ever:  top_stats[w, t, 10] += 1
                        if lb_first: top_stats[w, t, 11] += 1
                        
            # Record Bottom close stats across 6 thresholds
            for t in range(6):
                th = bot_thresholds[t]
                if close_pos <= th:
                    bot_stats[w, t, 0] += 1
                    if lb_first: bot_stats[w, t, 1] += 1
                    if lb_ever:  bot_stats[w, t, 2] += 1
                    if hb_first: bot_stats[w, t, 3] += 1
                    
                    if high_first:
                        bot_stats[w, t, 4] += 1
                        if lb_first: bot_stats[w, t, 5] += 1
                        if lb_ever:  bot_stats[w, t, 6] += 1
                        if hb_first: bot_stats[w, t, 7] += 1
                    else:
                        bot_stats[w, t, 8] += 1
                        if lb_first: bot_stats[w, t, 9] += 1
                        if lb_ever:  bot_stats[w, t, 10] += 1
                        if hb_first: bot_stats[w, t, 11] += 1
                        
    return top_stats, bot_stats, extreme_stats

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
    
    nq_data = load_data(nq_path)
    es_data = load_data(es_path)
    
    configs = [
        (7, 7, '7m'),
        (7, 1, '7m_1m_step'),
        (10, 10, '10m'),
        (15, 15, '15m'),
        (15, 1, '15m_step'),
        (30, 30, '30m'),
        (30, 15, '30m_15m_step'),
        (45, 45, '45m'),
        (60, 30, '60m'),
        (120, 60, '120m')
    ]
    
    out_dir = r"d:\Antigravity\Results\ClosePositionAnalysis"
    os.makedirs(out_dir, exist_ok=True)
    
    summary_rows = []
    th_labels = ['25%', '30%', '35%', '40%', '45%', '50%']
    
    for window_size, step, name in configs:
        print(f"\n=======================================================")
        print(f"Analyzing {name} (Window: {window_size}m, Step: {step}m)...")
        
        t0 = time.time()
        nq_top, nq_bot, nq_ext = compute_detailed_stats(nq_data['session_ids'], nq_data['session_mins'], nq_data['highs'], nq_data['lows'], nq_data['closes'], window_size=window_size, step=step)
        es_top, es_bot, es_ext = compute_detailed_stats(es_data['session_ids'], es_data['session_mins'], es_data['highs'], es_data['lows'], es_data['closes'], window_size=window_size, step=step)
        t1 = time.time()
        print(f"Computation completed in {t1-t0:.2f}s")
        
        # Summary row across all sessions & windows
        for t, label in enumerate(th_labels):
            # NQ Top
            nq_t_tot = int(nq_top[:, t, 0].sum())
            nq_t_hb_f = int(nq_top[:, t, 1].sum())
            nq_t_hb_ev = int(nq_top[:, t, 2].sum())
            nq_t_lb_f = int(nq_top[:, t, 3].sum())
            
            nq_t_lf_tot = int(nq_top[:, t, 4].sum())
            nq_t_lf_hb_f = int(nq_top[:, t, 5].sum())
            nq_t_lf_hb_ev = int(nq_top[:, t, 6].sum())
            
            nq_t_hf_tot = int(nq_top[:, t, 8].sum())
            nq_t_hf_hb_f = int(nq_top[:, t, 9].sum())
            
            # NQ Bot
            nq_b_tot = int(nq_bot[:, t, 0].sum())
            nq_b_lb_f = int(nq_bot[:, t, 1].sum())
            nq_b_lb_ev = int(nq_bot[:, t, 2].sum())
            nq_b_hb_f = int(nq_bot[:, t, 3].sum())
            
            nq_b_hf_tot = int(nq_bot[:, t, 4].sum())
            nq_b_hf_lb_f = int(nq_bot[:, t, 5].sum())
            nq_b_hf_lb_ev = int(nq_bot[:, t, 6].sum())
            
            nq_b_lf_tot = int(nq_bot[:, t, 8].sum())
            nq_b_lf_lb_f = int(nq_bot[:, t, 9].sum())
            
            # ES Top
            es_t_tot = int(es_top[:, t, 0].sum())
            es_t_hb_f = int(es_top[:, t, 1].sum())
            es_t_hb_ev = int(es_top[:, t, 2].sum())
            es_t_lb_f = int(es_top[:, t, 3].sum())
            
            es_t_lf_tot = int(es_top[:, t, 4].sum())
            es_t_lf_hb_f = int(es_top[:, t, 5].sum())
            es_t_lf_hb_ev = int(es_top[:, t, 6].sum())
            
            # ES Bot
            es_b_tot = int(es_bot[:, t, 0].sum())
            es_b_lb_f = int(es_bot[:, t, 1].sum())
            es_b_lb_ev = int(es_bot[:, t, 2].sum())
            es_b_hb_f = int(es_bot[:, t, 3].sum())
            
            es_b_hf_tot = int(es_bot[:, t, 4].sum())
            es_b_hf_lb_f = int(es_bot[:, t, 5].sum())
            es_b_hf_lb_ev = int(es_bot[:, t, 6].sum())
            
            summary_rows.append({
                'TimeRange': name,
                'Threshold': label,
                'NQ_TopClose_Count': nq_t_tot,
                'NQ_TopClose_BreakHighFirst_Prob': round((nq_t_hb_f / nq_t_tot * 100) if nq_t_tot > 0 else 0, 2),
                'NQ_TopClose_BreakHighEver_Prob': round((nq_t_hb_ev / nq_t_tot * 100) if nq_t_tot > 0 else 0, 2),
                'NQ_TopClose_BreakLowFirst_Prob': round((nq_t_lb_f / nq_t_tot * 100) if nq_t_tot > 0 else 0, 2),
                'NQ_LowFirst_TopClose_Count': nq_t_lf_tot,
                'NQ_LowFirst_TopClose_BreakHighFirst_Prob': round((nq_t_lf_hb_f / nq_t_lf_tot * 100) if nq_t_lf_tot > 0 else 0, 2),
                'NQ_LowFirst_TopClose_BreakHighEver_Prob': round((nq_t_lf_hb_ev / nq_t_lf_tot * 100) if nq_t_lf_tot > 0 else 0, 2),
                'NQ_HighFirst_TopClose_BreakHighFirst_Prob': round((nq_t_hf_hb_f / nq_t_hf_tot * 100) if nq_t_hf_tot > 0 else 0, 2),
                
                'NQ_BotClose_Count': nq_b_tot,
                'NQ_BotClose_BreakLowFirst_Prob': round((nq_b_lb_f / nq_b_tot * 100) if nq_b_tot > 0 else 0, 2),
                'NQ_BotClose_BreakLowEver_Prob': round((nq_b_lb_ev / nq_b_tot * 100) if nq_b_tot > 0 else 0, 2),
                'NQ_BotClose_BreakHighFirst_Prob': round((nq_b_hb_f / nq_b_tot * 100) if nq_b_tot > 0 else 0, 2),
                'NQ_HighFirst_BotClose_Count': nq_b_hf_tot,
                'NQ_HighFirst_BotClose_BreakLowFirst_Prob': round((nq_b_hf_lb_f / nq_b_hf_tot * 100) if nq_b_hf_tot > 0 else 0, 2),
                'NQ_HighFirst_BotClose_BreakLowEver_Prob': round((nq_b_hf_lb_ev / nq_b_hf_tot * 100) if nq_b_hf_tot > 0 else 0, 2),
                'NQ_LowFirst_BotClose_BreakLowFirst_Prob': round((nq_b_lf_lb_f / nq_b_lf_tot * 100) if nq_b_lf_tot > 0 else 0, 2),
                
                'ES_TopClose_Count': es_t_tot,
                'ES_TopClose_BreakHighFirst_Prob': round((es_t_hb_f / es_t_tot * 100) if es_t_tot > 0 else 0, 2),
                'ES_TopClose_BreakHighEver_Prob': round((es_t_hb_ev / es_t_tot * 100) if es_t_tot > 0 else 0, 2),
                'ES_LowFirst_TopClose_BreakHighFirst_Prob': round((es_t_lf_hb_f / es_t_lf_tot * 100) if es_t_lf_tot > 0 else 0, 2),
                
                'ES_BotClose_Count': es_b_tot,
                'ES_BotClose_BreakLowFirst_Prob': round((es_b_lb_f / es_b_tot * 100) if es_b_tot > 0 else 0, 2),
                'ES_BotClose_BreakLowEver_Prob': round((es_b_lb_ev / es_b_tot * 100) if es_b_tot > 0 else 0, 2),
                'ES_HighFirst_BotClose_BreakLowFirst_Prob': round((es_b_hf_lb_f / es_b_hf_tot * 100) if es_b_hf_tot > 0 else 0, 2)
            })
            
        # Export per-window CSV for this timeframe
        num_windows = len(nq_top)
        # Export per-window CSV for this timeframe
        num_windows = len(nq_top)
        window_rows = []
        for w in range(num_windows):
            win_label = format_window(w, step=step, window_size=window_size)
            row_dict = {'Window': win_label}
            
            # NQ Extreme stats alone
            nq_hf_tot = int(nq_ext[w, 0])
            nq_hf_lb_f = int(nq_ext[w, 1])
            nq_hf_hb_f = int(nq_ext[w, 2])
            nq_lf_tot = int(nq_ext[w, 4])
            nq_lf_hb_f = int(nq_ext[w, 5])
            nq_lf_lb_f = int(nq_ext[w, 6])
            
            row_dict['NQ_Total'] = nq_hf_tot + nq_lf_tot
            row_dict['NQ_HF_Total'] = nq_hf_tot
            row_dict['NQ_LF_Total'] = nq_lf_tot
            row_dict['NQ_HighFirst_BreakLowFirst_Prob'] = round((nq_hf_lb_f / nq_hf_tot * 100) if nq_hf_tot > 0 else 0, 2)
            row_dict['NQ_HighFirst_BreakHighFirst_Prob'] = round((nq_hf_hb_f / nq_hf_tot * 100) if nq_hf_tot > 0 else 0, 2)
            row_dict['NQ_LowFirst_BreakHighFirst_Prob'] = round((nq_lf_hb_f / nq_lf_tot * 100) if nq_lf_tot > 0 else 0, 2)
            row_dict['NQ_LowFirst_BreakLowFirst_Prob'] = round((nq_lf_lb_f / nq_lf_tot * 100) if nq_lf_tot > 0 else 0, 2)
            
            # ES Extreme stats alone
            es_hf_tot = int(es_ext[w, 0])
            es_hf_lb_f = int(es_ext[w, 1])
            es_hf_hb_f = int(es_ext[w, 2])
            es_lf_tot = int(es_ext[w, 4])
            es_lf_hb_f = int(es_ext[w, 5])
            es_lf_lb_f = int(es_ext[w, 6])
            
            row_dict['ES_Total'] = es_hf_tot + es_lf_tot
            row_dict['ES_HF_Total'] = es_hf_tot
            row_dict['ES_LF_Total'] = es_lf_tot
            row_dict['ES_HighFirst_BreakLowFirst_Prob'] = round((es_hf_lb_f / es_hf_tot * 100) if es_hf_tot > 0 else 0, 2)
            row_dict['ES_HighFirst_BreakHighFirst_Prob'] = round((es_hf_hb_f / es_hf_tot * 100) if es_hf_tot > 0 else 0, 2)
            row_dict['ES_LowFirst_BreakHighFirst_Prob'] = round((es_lf_hb_f / es_lf_tot * 100) if es_lf_tot > 0 else 0, 2)
            row_dict['ES_LowFirst_BreakLowFirst_Prob'] = round((es_lf_lb_f / es_lf_tot * 100) if es_lf_tot > 0 else 0, 2)

            for t, label in enumerate(th_labels):
                # NQ Top
                n_t_tot = int(nq_top[w, t, 0])
                n_t_hb_f = int(nq_top[w, t, 1])
                n_t_hb_ev = int(nq_top[w, t, 2])
                n_t_lf_tot = int(nq_top[w, t, 4])
                n_t_lf_hb_f = int(nq_top[w, t, 5])
                
                row_dict[f'NQ_Top{label}_Total'] = n_t_tot
                row_dict[f'NQ_Top{label}_BreakHighFirst_Prob'] = round((n_t_hb_f / n_t_tot * 100) if n_t_tot > 0 else 0, 2)
                row_dict[f'NQ_Top{label}_BreakHighEver_Prob'] = round((n_t_hb_ev / n_t_tot * 100) if n_t_tot > 0 else 0, 2)
                row_dict[f'NQ_LowFirst_Top{label}_Total'] = n_t_lf_tot
                row_dict[f'NQ_LowFirst_Top{label}_BreakHighFirst_Prob'] = round((n_t_lf_hb_f / n_t_lf_tot * 100) if n_t_lf_tot > 0 else 0, 2)
                
                # NQ Bottom
                n_b_tot = int(nq_bot[w, t, 0])
                n_b_lb_f = int(nq_bot[w, t, 1])
                n_b_lb_ev = int(nq_bot[w, t, 2])
                n_b_hf_tot = int(nq_bot[w, t, 4])
                n_b_hf_lb_f = int(nq_bot[w, t, 5])
                
                row_dict[f'NQ_Bot{label}_Total'] = n_b_tot
                row_dict[f'NQ_Bot{label}_BreakLowFirst_Prob'] = round((n_b_lb_f / n_b_tot * 100) if n_b_tot > 0 else 0, 2)
                row_dict[f'NQ_Bot{label}_BreakLowEver_Prob'] = round((n_b_lb_ev / n_b_tot * 100) if n_b_tot > 0 else 0, 2)
                row_dict[f'NQ_HighFirst_Bot{label}_Total'] = n_b_hf_tot
                row_dict[f'NQ_HighFirst_Bot{label}_BreakLowFirst_Prob'] = round((n_b_hf_lb_f / n_b_hf_tot * 100) if n_b_hf_tot > 0 else 0, 2)
                
                # ES Top
                e_t_tot = int(es_top[w, t, 0])
                e_t_hb_f = int(es_top[w, t, 1])
                e_t_hb_ev = int(es_top[w, t, 2])
                e_t_lf_tot = int(es_top[w, t, 4])
                e_t_lf_hb_f = int(es_top[w, t, 5])
                
                row_dict[f'ES_Top{label}_Total'] = e_t_tot
                row_dict[f'ES_Top{label}_BreakHighFirst_Prob'] = round((e_t_hb_f / e_t_tot * 100) if e_t_tot > 0 else 0, 2)
                row_dict[f'ES_Top{label}_BreakHighEver_Prob'] = round((e_t_hb_ev / e_t_tot * 100) if e_t_tot > 0 else 0, 2)
                row_dict[f'ES_LowFirst_Top{label}_Total'] = e_t_lf_tot
                row_dict[f'ES_LowFirst_Top{label}_BreakHighFirst_Prob'] = round((e_t_lf_hb_f / e_t_lf_tot * 100) if e_t_lf_tot > 0 else 0, 2)
                
                # ES Bottom
                e_b_tot = int(es_bot[w, t, 0])
                e_b_lb_f = int(es_bot[w, t, 1])
                e_b_lb_ev = int(es_bot[w, t, 2])
                e_b_hf_tot = int(es_bot[w, t, 4])
                e_b_hf_lb_f = int(es_bot[w, t, 5])
                
                row_dict[f'ES_Bot{label}_Total'] = e_b_tot
                row_dict[f'ES_Bot{label}_BreakLowFirst_Prob'] = round((e_b_lb_f / e_b_tot * 100) if e_b_tot > 0 else 0, 2)
                row_dict[f'ES_Bot{label}_BreakLowEver_Prob'] = round((e_b_lb_ev / e_b_tot * 100) if e_b_tot > 0 else 0, 2)
                row_dict[f'ES_HighFirst_Bot{label}_Total'] = e_b_hf_tot
                row_dict[f'ES_HighFirst_Bot{label}_BreakLowFirst_Prob'] = round((e_b_hf_lb_f / e_b_hf_tot * 100) if e_b_hf_tot > 0 else 0, 2)

            window_rows.append(row_dict)
            
        df_win = pd.DataFrame(window_rows)
        csv_path = os.path.join(out_dir, f"{name}_by_window.csv")
        df_win.to_csv(csv_path, index=False)
        print(f"Saved {csv_path} ({len(window_rows)} windows)")
        
        # Also inject into imobile dashboard data JSON if existing
        dash_data_json = os.path.join(r"d:\Antigravity\imobile ib dashboard\data", f"time_range_{name}.json")
        if os.path.exists(dash_data_json):
            try:
                with open(dash_data_json, 'r', encoding='utf-8') as df:
                    d_obj = json.load(df)
                d_obj['close_pos'] = window_rows
                with open(dash_data_json, 'w', encoding='utf-8') as df:
                    json.dump(d_obj, df)
                print(f"Injected close_pos data into {dash_data_json}")
            except Exception as ex:
                print(f"Failed injecting into {dash_data_json}: {ex}")
        
    df_summary = pd.DataFrame(summary_rows)
    sum_csv = os.path.join(out_dir, "overall_summary_all_ranges.csv")
    df_summary.to_csv(sum_csv, index=False)
    print(f"\nAll analyses complete! Summary saved to {sum_csv} ({len(summary_rows)} rows)")
    
    # Also save as JSON for easy embedding / dashboard loading
    sum_json = os.path.join(out_dir, "overall_summary_all_ranges.json")
    with open(sum_json, 'w') as f:
        json.dump(summary_rows, f, indent=2)
    print(f"Saved {sum_json}")

if __name__ == "__main__":
    main()

