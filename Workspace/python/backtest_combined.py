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
def backtest_strat_1(session_starts, session_ends, mins_arr, high_arr, low_arr, close_arr):
    # Strat 1: 20:01 to 20:07, Target 1R
    start_m = (20 - 17) * 60 + 1   # 181
    end_m = (20 - 17) * 60 + 7     # 187
    rth_close_m = 1380             # 16:00
    
    num_sessions = len(session_starts)
    session_pnls = np.zeros(num_sessions, dtype=np.float64)
    trades_taken = np.zeros(num_sessions, dtype=np.bool_)
    
    for s in range(num_sessions):
        idx_start = session_starts[s]
        idx_end = session_ends[s]
        
        ib_high = -1.0
        ib_low = 1e9
        has_ib = False
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= start_m and m <= end_m:
                if high_arr[i] > ib_high: ib_high = high_arr[i]
                if low_arr[i] < ib_low: ib_low = low_arr[i]
                has_ib = True
            elif m > end_m:
                break
                
        if not has_ib: continue
        ib_range = ib_high - ib_low
        if ib_range <= 0: continue
            
        entry_price = ib_high
        entry_time = -1
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > end_m and m <= rth_close_m:
                if high_arr[i] > ib_high and low_arr[i] < ib_low: break
                elif high_arr[i] > ib_high:
                    entry_time = m
                    break
                elif low_arr[i] < ib_low: break
                    
        if entry_time == -1: continue
            
        sl_price = ib_low
        tp_price = entry_price + (1.0 * ib_range) 
        
        exit_price = -1.0
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= entry_time and m <= rth_close_m:
                if low_arr[i] <= sl_price:
                    exit_price = sl_price
                    break
                elif high_arr[i] >= tp_price:
                    exit_price = tp_price
                    break
                    
        if exit_price == -1.0:
            last_c = entry_price
            for i in range(idx_start, idx_end):
                if mins_arr[i] >= entry_time and mins_arr[i] <= rth_close_m:
                    last_c = close_arr[i]
                    if mins_arr[i] == rth_close_m: break
            exit_price = last_c
            
        pnl_pts = exit_price - entry_price
        session_pnls[s] = pnl_pts / ib_range
        trades_taken[s] = True
        
    return session_pnls, trades_taken

@njit
def backtest_strat_2(session_starts, session_ends, mins_arr, high_arr, low_arr, close_arr):
    # Strat 2: 18:50 to 18:59, Target 0.5R
    start_m = (18 - 17) * 60 + 50   # 110
    end_m = (18 - 17) * 60 + 59     # 119
    rth_close_m = 1380             # 16:00
    
    num_sessions = len(session_starts)
    session_pnls = np.zeros(num_sessions, dtype=np.float64)
    trades_taken = np.zeros(num_sessions, dtype=np.bool_)
    
    for s in range(num_sessions):
        idx_start = session_starts[s]
        idx_end = session_ends[s]
        
        ib_high = -1.0
        ib_low = 1e9
        has_ib = False
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= start_m and m <= end_m:
                if high_arr[i] > ib_high: ib_high = high_arr[i]
                if low_arr[i] < ib_low: ib_low = low_arr[i]
                has_ib = True
            elif m > end_m:
                break
                
        if not has_ib: continue
        ib_range = ib_high - ib_low
        if ib_range <= 0: continue
            
        entry_price = ib_high
        entry_time = -1
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > end_m and m <= rth_close_m:
                if high_arr[i] > ib_high and low_arr[i] < ib_low: break
                elif high_arr[i] > ib_high:
                    entry_time = m
                    break
                elif low_arr[i] < ib_low: break
                    
        if entry_time == -1: continue
            
        sl_price = ib_low
        tp_price = entry_price + (0.5 * ib_range) 
        
        exit_price = -1.0
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= entry_time and m <= rth_close_m:
                if low_arr[i] <= sl_price:
                    exit_price = sl_price
                    break
                elif high_arr[i] >= tp_price:
                    exit_price = tp_price
                    break
                    
        if exit_price == -1.0:
            last_c = entry_price
            for i in range(idx_start, idx_end):
                if mins_arr[i] >= entry_time and mins_arr[i] <= rth_close_m:
                    last_c = close_arr[i]
                    if mins_arr[i] == rth_close_m: break
            exit_price = last_c
            
        pnl_pts = exit_price - entry_price
        session_pnls[s] = pnl_pts / ib_range
        trades_taken[s] = True
        
    return session_pnls, trades_taken

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

print('Running Backtests...')
pnls_1, trades_1 = backtest_strat_1(nq_starts, nq_ends, nq_mins, nq_h, nq_l, nq_c)
pnls_2, trades_2 = backtest_strat_2(nq_starts, nq_ends, nq_mins, nq_h, nq_l, nq_c)

# Combine daily PnL
combined_pnls = pnls_1 + pnls_2
trades_taken_combined = trades_1 | trades_2

# Now create a flattened list of individual trade PnLs to calculate averages and win rates
all_trades = []
for s in range(len(combined_pnls)):
    if trades_2[s]: all_trades.append(pnls_2[s])
    if trades_1[s]: all_trades.append(pnls_1[s])

all_trades = np.array(all_trades)

trades = len(all_trades)
if trades > 0:
    wins = np.sum(all_trades > 0)
    losses = np.sum(all_trades <= 0)
    win_rate = wins / trades * 100
    
    gross_profit = np.sum(all_trades[all_trades > 0])
    gross_loss = np.abs(np.sum(all_trades[all_trades <= 0]))
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf
    
    avg_win = gross_profit / wins if wins > 0 else 0
    avg_loss = gross_loss / losses if losses > 0 else 0
    
    total_pnl = np.sum(all_trades)
    
    # Calculate Max Drawdown based on chronological DAILY closing balance
    # (Since we do multiple trades a day sometimes, calculating from combined daily pnl is highly accurate for EOD drawdown, 
    # but let's do trade-by-trade for Max Drawdown)
    cumulative_pnl = np.cumsum(all_trades)
    peak = np.maximum.accumulate(cumulative_pnl)
    drawdown = peak - cumulative_pnl
    max_drawdown = np.max(drawdown)

    print(f"\n--- COMBINED RESULTS (18:50 & 20:01 SETUPS) ---")
    print(f"Total Trades:        {trades}")
    print(f"Wins:                {wins}")
    print(f"Losses:              {losses}")
    print(f"Win Rate:            {win_rate:.2f}%")
    print(f"Total PnL:           {total_pnl:.2f} R")
    print(f"Profit Factor:       {profit_factor:.2f}")
    print(f"Max Drawdown:        {max_drawdown:.2f} R")
    print(f"Average Win:         {avg_win:.2f} R")
    print(f"Average Loss:        {avg_loss:.2f} R")
    
    print("\n--- APEX EVALUATION PROJECTION ($50k Account) ---")
    # Assuming Risk = $100 per trade
    risk = 100
    print(f"Assumed Risk per Trade:  ${risk}")
    print(f"Projected Max Drawdown:  ${max_drawdown * risk:.2f} (Apex Limit is $2,500)")
    print(f"Average Yearly Trades:   {trades / 10.5:.0f}") # Approx 10.5 years in dataset
    yearly_r = total_pnl / 10.5
    print(f"Expected Yearly Return:  ${yearly_r * risk:.2f}")
    print(f"Months to Pass Eval:     {3000 / (yearly_r * risk / 12):.1f} months")
    
else:
    print("No trades found.")
