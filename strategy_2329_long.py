import pandas as pd
import numpy as np
from numba import njit
import time
import os

@njit
def backtest_strategy(session_ids, session_mins, highs, lows, closes, num_sessions, w_start_min=329, w_end_min=335):
    # Metrics:
    # 0: Total Sessions
    # 1: Setups Invalidated
    # 2: Total Entries
    # 3: Wins
    # 4: Losses
    # 5: Total PnL points
    # 6: Entry Clashes (High and Low broken in same candle)
    # 7: Exit Clashes (TP and SL hit in same candle)
    metrics = np.zeros(8, dtype=np.float64)
    
    n = len(session_ids)
    idx = 0
    
    while idx < n:
        start_idx = idx
        current_session = session_ids[idx]
        
        while idx < n and session_ids[idx] == current_session:
            idx += 1
        end_idx = idx
        
        w_high = -1e9
        w_low = 1e9
        has_data = False
        
        for i in range(start_idx, end_idx):
            m = session_mins[i]
            if m >= w_start_min and m <= w_end_min:
                if highs[i] > w_high: w_high = highs[i]
                if lows[i] < w_low: w_low = lows[i]
                has_data = True
            elif m > w_end_min:
                break
                
        if not has_data:
            continue
            
        metrics[0] += 1
        
        range_val = w_high - w_low
        target = w_high + 0.40 * range_val
        sl = w_low
        
        entered = False
        invalidated = False
        pnl = 0.0
        win = 0
        loss = 0
        
        for i in range(start_idx, end_idx):
            m = session_mins[i]
            if m > w_end_min:
                h = highs[i]
                l = lows[i]
                
                if not entered and not invalidated:
                    breaks_high = h > w_high
                    breaks_low = l < w_low
                    
                    if breaks_high and breaks_low:
                        metrics[6] += 1
                        invalidated = True
                    elif breaks_low:
                        invalidated = True
                    elif breaks_high:
                        entered = True
                        
                        hits_tp = h >= target
                        hits_sl = l <= sl
                        
                        if hits_tp and hits_sl:
                            metrics[7] += 1
                            loss = 1
                            pnl = sl - w_high
                            break
                        elif hits_tp:
                            win = 1
                            pnl = target - w_high
                            break
                        elif hits_sl:
                            loss = 1
                            pnl = sl - w_high
                            break
                elif entered:
                    hits_tp = h >= target
                    hits_sl = l <= sl
                    
                    if hits_tp and hits_sl:
                        metrics[7] += 1
                        loss = 1
                        pnl = sl - w_high
                        break
                    elif hits_tp:
                        win = 1
                        pnl = target - w_high
                        break
                    elif hits_sl:
                        loss = 1
                        pnl = sl - w_high
                        break
                        
        if invalidated:
            metrics[1] += 1
        elif entered:
            metrics[2] += 1
            if win == 0 and loss == 0:
                pnl = closes[end_idx - 1] - w_high
                if pnl > 0:
                    win = 1
                else:
                    loss = 1
            
            metrics[3] += win
            metrics[4] += loss
            metrics[5] += pnl
            
    return metrics

def process_asset(file_path, asset_name):
    print(f"Loading {asset_name} data...")
    df = pd.read_parquet(file_path)
    
    hours = df['Time'].str.slice(0, 2).astype(int)
    minutes = df['Time'].str.slice(3, 5).astype(int)
    
    session_min = np.where(hours >= 18, 
                           (hours - 18) * 60 + minutes, 
                           (hours + 6) * 60 + minutes)
    df['session_min'] = session_min
    
    df['dt'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['session_date'] = (df['dt'] - pd.Timedelta(hours=17)).dt.date
    
    session_ids = df.groupby('session_date').ngroup().values
    
    print(f"Running backtest for {asset_name}...")
    t0 = time.time()
    
    metrics = backtest_strategy(
        session_ids.astype(np.int32),
        df['session_min'].values.astype(np.int32),
        df['High'].values.astype(np.float64),
        df['Low'].values.astype(np.float64),
        df['Last'].values.astype(np.float64),
        num_sessions=session_ids.max() + 1
    )
    
    t1 = time.time()
    print(f"Done in {t1 - t0:.3f} seconds\n")
    
    return metrics

def print_results(asset_name, metrics):
    tot_sessions = int(metrics[0])
    invalidated = int(metrics[1])
    entries = int(metrics[2])
    wins = int(metrics[3])
    losses = int(metrics[4])
    pnl = metrics[5]
    entry_clashes = int(metrics[6])
    exit_clashes = int(metrics[7])
    
    win_rate = (wins / entries * 100) if entries > 0 else 0
    avg_trade = pnl / entries if entries > 0 else 0
    
    print(f"[{asset_name}] Strategy Results (23:29 - 23:35)")
    print("-" * 40)
    print(f"Total Valid Sessions : {tot_sessions}")
    print(f"Setups Invalidated   : {invalidated}")
    print(f"Total Trades Taken   : {entries}")
    print(f"Wins                 : {wins}")
    print(f"Losses               : {losses}")
    print(f"Win Rate             : {win_rate:.2f}%")
    print(f"Total PnL (Points)   : {pnl:.2f}")
    print(f"Avg PnL / Trade      : {avg_trade:.2f}")
    print(f"-> Entry Clashes     : {entry_clashes}")
    print(f"-> Exit Clashes      : {exit_clashes}\n")

def main():
    base_dir = r"d:\Antigravity\Historical data"
    nq_path = os.path.join(base_dir, "NQ Futures Datasets", "Full Data", "parquet", "NQ_1m_full_data.parquet")
    es_path = os.path.join(base_dir, "ES Futures Datasets", "Full Data", "parquet", "ES_1m_full_data.parquet")
    
    nq_metrics = process_asset(nq_path, "NQ")
    es_metrics = process_asset(es_path, "ES")
    
    print_results("NQ", nq_metrics)
    print_results("ES", es_metrics)

if __name__ == "__main__":
    main()
