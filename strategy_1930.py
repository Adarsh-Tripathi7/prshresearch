import pandas as pd
import numpy as np
from numba import njit
import time
import os

@njit
def backtest_strategy(highs, lows, closes, session_mins, session_ids, use_time_exit, w_start=90, w_end=119):
    # Metrics
    metrics = np.zeros(6, dtype=np.float64) # entries, wins, losses, pnl, time_exits, invalidated
    
    n = len(highs)
    
    # State
    in_trade = False
    target = 0.0
    sl = 0.0
    trade_w_high = 0.0
    
    # Session tracking
    current_session = -1
    w_high = -1e9
    w_low = 1e9
    can_trade = False
    invalidated = False
    trade_taken_today = False
    
    for i in range(n):
        sess = session_ids[i]
        m = session_mins[i]
        
        # New session logic
        if sess != current_session:
            current_session = sess
            w_high = -1e9
            w_low = 1e9
            can_trade = False
            invalidated = False
            trade_taken_today = False
            
            # If time exit is ON and we are in a trade, close it at the end of the PREVIOUS session
            if in_trade and use_time_exit and i > 0:
                pnl = closes[i-1] - trade_w_high
                metrics[5] += 1 # time exit count
                if pnl > 0: metrics[1] += 1
                else: metrics[2] += 1
                metrics[3] += pnl
                in_trade = False
                
        # Window tracking
        if m >= w_start and m <= w_end:
            if highs[i] > w_high: w_high = highs[i]
            if lows[i] < w_low: w_low = lows[i]
            if m == w_end:
                can_trade = True
                
        # Trade logic
        if not in_trade:
            if can_trade and not trade_taken_today and m > w_end:
                # Invalidate if low breaks
                if lows[i] <= w_low:
                    invalidated = True
                    can_trade = False
                    metrics[4] += 1 # invalidated count
                    
                if not invalidated and highs[i] > w_high:
                    in_trade = True
                    trade_taken_today = True
                    metrics[0] += 1 # entries
                    range_val = w_high - w_low
                    target = w_high + 1.30 * range_val
                    sl = w_low
                    trade_w_high = w_high
                    
                    # Check intra-bar hit
                    hits_tp = highs[i] >= target
                    hits_sl = lows[i] <= sl
                    
                    if hits_tp and hits_sl:
                        # pessimistic: assume loss
                        metrics[2] += 1
                        metrics[3] += sl - trade_w_high
                        in_trade = False
                    elif hits_tp:
                        metrics[1] += 1
                        metrics[3] += target - trade_w_high
                        in_trade = False
                    elif hits_sl:
                        metrics[2] += 1
                        metrics[3] += sl - trade_w_high
                        in_trade = False
        else:
            # We are in a trade
            hits_tp = highs[i] >= target
            hits_sl = lows[i] <= sl
            
            if hits_tp and hits_sl:
                metrics[2] += 1
                metrics[3] += sl - trade_w_high
                in_trade = False
            elif hits_tp:
                metrics[1] += 1
                metrics[3] += target - trade_w_high
                in_trade = False
            elif hits_sl:
                metrics[2] += 1
                metrics[3] += sl - trade_w_high
                in_trade = False
                
    # Close any open trade at the very end
    if in_trade:
        pnl = closes[n-1] - trade_w_high
        if pnl > 0: metrics[1] += 1
        else: metrics[2] += 1
        metrics[3] += pnl
        
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
    df = df.sort_values('dt').reset_index(drop=True)
    df['session_date'] = (df['dt'] - pd.Timedelta(hours=17)).dt.date
    session_ids = df.groupby('session_date').ngroup().values
    
    highs = df['High'].values.astype(np.float64)
    lows = df['Low'].values.astype(np.float64)
    closes = df['Last'].values.astype(np.float64)
    session_mins = df['session_min'].values.astype(np.int32)
    session_ids = session_ids.astype(np.int32)
    
    print(f"Running 19:30 backtests for {asset_name}...")
    
    # 1. With Time Exit (Closes end of session 16:59)
    res_time = backtest_strategy(highs, lows, closes, session_mins, session_ids, True)
    
    # 2. Without Time Exit (Holds overnight until TP/SL hit)
    res_no_time = backtest_strategy(highs, lows, closes, session_mins, session_ids, False)
    
    return res_time, res_no_time

def print_results(asset_name, res_time, res_no_time):
    print(f"\\n[{asset_name}] Strategy Results (19:30 - 19:59) Target: 1.3R")
    print("=" * 60)
    
    for name, metrics in [("WITH Time Exit (Session Close)", res_time), ("WITHOUT Time Exit (Hold Overnights)", res_no_time)]:
        entries = int(metrics[0])
        wins = int(metrics[1])
        losses = int(metrics[2])
        pnl = metrics[3]
        invalidated = int(metrics[4])
        time_exits = int(metrics[5])
        
        win_rate = (wins / entries * 100) if entries > 0 else 0
        avg_trade = pnl / entries if entries > 0 else 0
        
        print(f"--- {name} ---")
        print(f"Setups Invalidated : {invalidated}")
        print(f"Total Trades       : {entries}")
        print(f"Wins               : {wins}")
        print(f"Losses             : {losses}")
        if name == "WITH Time Exit (Session Close)":
            print(f"Time Exits (EOD)   : {time_exits}")
        print(f"Win Rate           : {win_rate:.2f}%")
        print(f"Total PnL (Points) : {pnl:.2f}")
        print(f"Avg PnL / Trade    : {avg_trade:.2f}\\n")

def main():
    base_dir = r"d:\Antigravity\Historical data"
    nq_path = os.path.join(base_dir, "NQ Futures Datasets", "Full Data", "parquet", "NQ_1m_full_data.parquet")
    es_path = os.path.join(base_dir, "ES Futures Datasets", "Full Data", "parquet", "ES_1m_full_data.parquet")
    
    nq_time, nq_no_time = process_asset(nq_path, "NQ")
    es_time, es_no_time = process_asset(es_path, "ES")
    
    print_results("NQ", nq_time, nq_no_time)
    print_results("ES", es_time, es_no_time)

if __name__ == "__main__":
    main()
