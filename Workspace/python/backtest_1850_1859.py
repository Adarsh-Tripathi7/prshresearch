import pandas as pd
import numpy as np
from numba import njit

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
def backtest_strategy(session_starts, session_ends, mins_arr, high_arr, low_arr, close_arr):
    # 18:50 to 18:59
    start_m = (19 - 17) * 60 + 10   # 110
    end_m = (19- 17) * 60 + 16    # 119
    rth_close_m = 1380             # 16:00
    
    num_sessions = len(session_starts)
    pnls = np.zeros(num_sessions, dtype=np.float64)
    trade_count = 0
    
    for s in range(num_sessions):
        idx_start = session_starts[s]
        idx_end = session_ends[s]
        
        ib_high = -1.0
        ib_low = 1e9
        has_ib = False
        
        # 1. Find IB High and IB Low
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= start_m and m <= end_m:
                if high_arr[i] > ib_high: ib_high = high_arr[i]
                if low_arr[i] < ib_low: ib_low = low_arr[i]
                has_ib = True
            elif m > end_m:
                break
                
        if not has_ib:
            continue
            
        ib_range = ib_high - ib_low
        if ib_range <= 0:
            continue
            
        # 2. Wait for Long Entry (Crosses above IB High FIRST)
        entry_price = ib_high
        entry_time = -1
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > end_m and m <= rth_close_m:
                if high_arr[i] > ib_high and low_arr[i] < ib_low:
                    # Broke both in the same minute, we don't know which was first, skip
                    break
                elif high_arr[i] > ib_high:
                    entry_time = m
                    break
                elif low_arr[i] < ib_low:
                    # Broke low first, so we don't take a long
                    break
                    
        if entry_time == -1:
            continue
            
        # 3. Monitor Trade for TP/SL
        sl_price = ib_low
        tp_price = entry_price + (0.5 * ib_range) # 0.5R target
        
        exit_price = -1.0
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= entry_time and m <= rth_close_m:
                # To be conservative, if both happen in same minute, count as loss
                if low_arr[i] <= sl_price:
                    exit_price = sl_price
                    break
                elif high_arr[i] >= tp_price:
                    exit_price = tp_price
                    break
                    
        # 4. End of day exit
        if exit_price == -1.0:
            last_c = entry_price
            for i in range(idx_start, idx_end):
                if mins_arr[i] >= entry_time and mins_arr[i] <= rth_close_m:
                    last_c = close_arr[i]
                    if mins_arr[i] == rth_close_m:
                        break
            exit_price = last_c
            
        pnl_pts = exit_price - entry_price
        pnl_r = pnl_pts / ib_range
        pnls[trade_count] = pnl_r
        trade_count += 1
        
    return pnls[:trade_count]

print('Loading datasets...')
nq_1m = pd.read_parquet(r'd:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet')

def prep_data(df):
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    df['Mins'] = df['Datetime'].apply(calc_mins_from_start)
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    unique_sessions = df['SessionDate'].unique()
    session_map = {sess: i for i, sess in enumerate(unique_sessions)}
    session_idx_arr = df['SessionDate'].map(session_map).values.astype(np.int32)
    
    mins_arr = df['Mins'].values.astype(np.int32)
    high_arr = df['High'].values.astype(np.float32)
    low_arr = df['Low'].values.astype(np.float32)
    close_arr = df['Last'].values.astype(np.float32)
    
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
    
    return session_starts, session_ends, mins_arr, high_arr, low_arr, close_arr

print('Preparing NQ...')
nq_starts, nq_ends, nq_mins, nq_h, nq_l, nq_c = prep_data(nq_1m)

print('--- BACKTEST RESULTS FOR 18:50-18:59 NQ BREAKOUT (0.5R TARGET, LONG ONLY) ---')
pnls = backtest_strategy(nq_starts, nq_ends, nq_mins, nq_h, nq_l, nq_c)

trades = len(pnls)
if trades > 0:
    wins = np.sum(pnls > 0)
    losses = np.sum(pnls <= 0)
    win_rate = wins / trades * 100
    
    gross_profit = np.sum(pnls[pnls > 0])
    gross_loss = np.abs(np.sum(pnls[pnls <= 0]))
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf
    
    avg_win = gross_profit / wins if wins > 0 else 0
    avg_loss = gross_loss / losses if losses > 0 else 0
    
    total_pnl = np.sum(pnls)
    
    # Calculate Max Drawdown
    cumulative_pnl = np.cumsum(pnls)
    peak = np.maximum.accumulate(cumulative_pnl)
    drawdown = peak - cumulative_pnl
    max_drawdown = np.max(drawdown)
    
    # Streaks
    is_win = pnls > 0
    streak = 0
    max_win_streak = 0
    for w in is_win:
        if w:
            streak += 1
            max_win_streak = max(max_win_streak, streak)
        else:
            streak = 0
            
    streak = 0
    max_loss_streak = 0
    for w in is_win:
        if not w:
            streak += 1
            max_loss_streak = max(max_loss_streak, streak)
        else:
            streak = 0

    print(f"Total Trades:        {trades}")
    print(f"Wins:                {wins}")
    print(f"Losses:              {losses}")
    print(f"Win Rate:            {win_rate:.2f}%")
    print(f"Total PnL:           {total_pnl:.2f} R")
    print(f"Profit Factor:       {profit_factor:.2f}")
    print(f"Max Drawdown:        {max_drawdown:.2f} R")
    print(f"Average Win:         {avg_win:.2f} R")
    print(f"Average Loss:        {avg_loss:.2f} R")
    print(f"Max Winning Streak:  {max_win_streak}")
    print(f"Max Losing Streak:   {max_loss_streak}")
else:
    print("No trades found.")
