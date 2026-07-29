import pandas as pd
import numpy as np
from numba import njit
import os

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
def backtest_p50(session_starts, session_ends, mins_arr, high_arr, low_arr, close_arr, p50_val, is_fade=False, sl_multiplier=1.0):
    start_m = 60 # 19:00
    end_m = 119  # 19:59
    rth_close_m = 1380 # 16:00
    
    total_trades = 0
    wins = 0
    losses = 0
    total_pnl = 0.0
    
    for s in range(len(session_starts)):
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
                
        if not has_ib:
            continue
            
        ib_range = ib_high - ib_low
        if ib_range <= 0:
            continue
            
        # Find first break
        break_dir = 0 # 1 for high broke first, -1 for low broke first
        break_time = -1
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > end_m and m <= rth_close_m:
                if high_arr[i] > ib_high and break_dir == 0:
                    break_dir = 1
                    break_time = m
                if low_arr[i] < ib_low and break_dir == 0:
                    break_dir = -1
                    break_time = m
                    
                if break_dir != 0:
                    break
                    
        if break_dir == 0:
            continue
            
        wait_until = break_time + p50_val
        if wait_until > rth_close_m:
            wait_until = rth_close_m
            
        double_break_before_wait = False
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > break_time and m <= wait_until:
                if break_dir == 1 and low_arr[i] < ib_low:
                    double_break_before_wait = True
                    break
                if break_dir == -1 and high_arr[i] > ib_high:
                    double_break_before_wait = True
                    break
                    
        if double_break_before_wait:
            continue
            
        if wait_until >= rth_close_m:
            continue
            
        entry_price = -1.0
        entry_time = -1
        trade_dir = 0
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > wait_until and m <= rth_close_m:
                if break_dir == 1: # high broke first, looking at ib_low
                    if low_arr[i] <= ib_low:
                        entry_price = ib_low
                        entry_time = m
                        trade_dir = 1 if is_fade else -1
                        break
                else: # low broke first, looking at ib_high
                    if high_arr[i] >= ib_high:
                        entry_price = ib_high
                        entry_time = m
                        trade_dir = -1 if is_fade else 1
                        break
                        
        if entry_time == -1:
            continue
            
        sl_dist = sl_multiplier * ib_range
        sl_price = entry_price + sl_dist if trade_dir == -1 else entry_price - sl_dist
        
        tp_dist = 1.0 * ib_range
        tp_price = entry_price + tp_dist if trade_dir == 1 else entry_price - tp_dist
        
        exit_price = -1.0
        
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= entry_time and m <= rth_close_m:
                if trade_dir == 1: # Long
                    if low_arr[i] <= sl_price:
                        exit_price = sl_price
                        break
                    if high_arr[i] >= tp_price:
                        exit_price = tp_price
                        break
                else: # Short
                    if high_arr[i] >= sl_price:
                        exit_price = sl_price
                        break
                    if low_arr[i] <= tp_price:
                        exit_price = tp_price
                        break
                        
        if exit_price == -1.0:
            last_c = entry_price
            for i in range(idx_start, idx_end):
                if mins_arr[i] >= entry_time and mins_arr[i] <= rth_close_m:
                    last_c = close_arr[i]
                    if mins_arr[i] == rth_close_m:
                        break
            exit_price = last_c
            
        pnl = (exit_price - entry_price) * trade_dir
        total_pnl += pnl
        total_trades += 1
        if pnl > 0: wins += 1
        elif pnl <= 0: losses += 1
        
    return total_trades, wins, losses, total_pnl

print('Loading datasets...')
nq_1m = pd.read_parquet(r'd:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet')
es_1m = pd.read_parquet(r'd:\Antigravity\Historical data\ES Futures Datasets\Full Data\parquet\ES_1m_full_data.parquet')

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
print('Preparing ES...')
es_starts, es_ends, es_mins, es_h, es_l, es_c = prep_data(es_1m)

nq_p50 = 261.5
es_p50 = 292.0

print('--- BREAKOUT STRATEGY (SL = 1.0x Range) ---')
nq_trades, nq_wins, nq_losses, nq_pnl = backtest_p50(nq_starts, nq_ends, nq_mins, nq_h, nq_l, nq_c, nq_p50, is_fade=False, sl_multiplier=1.0)
es_trades, es_wins, es_losses, es_pnl = backtest_p50(es_starts, es_ends, es_mins, es_h, es_l, es_c, es_p50, is_fade=False, sl_multiplier=1.0)
print(f"NQ Breakout | Trades: {nq_trades} | Wins: {nq_wins} | Win Rate: {nq_wins/nq_trades*100:.2f}% | PnL: {nq_pnl:.2f} pts")
print(f"ES Breakout | Trades: {es_trades} | Wins: {es_wins} | Win Rate: {es_wins/es_trades*100:.2f}% | PnL: {es_pnl:.2f} pts")

print('\n--- FADE STRATEGY (SL = 1.0x Range) ---')
nq_trades, nq_wins, nq_losses, nq_pnl = backtest_p50(nq_starts, nq_ends, nq_mins, nq_h, nq_l, nq_c, nq_p50, is_fade=True, sl_multiplier=1.0)
es_trades, es_wins, es_losses, es_pnl = backtest_p50(es_starts, es_ends, es_mins, es_h, es_l, es_c, es_p50, is_fade=True, sl_multiplier=1.0)
print(f"NQ Fade     | Trades: {nq_trades} | Wins: {nq_wins} | Win Rate: {nq_wins/nq_trades*100:.2f}% | PnL: {nq_pnl:.2f} pts")
print(f"ES Fade     | Trades: {es_trades} | Wins: {es_wins} | Win Rate: {es_wins/es_trades*100:.2f}% | PnL: {es_pnl:.2f} pts")
