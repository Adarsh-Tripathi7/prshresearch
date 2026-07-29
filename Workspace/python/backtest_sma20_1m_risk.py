import pandas as pd
import numpy as np
from numba import njit
import time

print("Loading 1-min data...")
df = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")

df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
df = df.sort_values('Datetime').reset_index(drop=True)

df['SMA20'] = df['Last'].rolling(20).mean()

df['SMA20_prev'] = df['SMA20'].shift(1)
df['Last_prev'] = df['Last'].shift(1)

o = df['Open'].values.astype(np.float64)
c_prev = df['Last_prev'].values.astype(np.float64)
sma_prev = df['SMA20_prev'].values.astype(np.float64)

@njit
def backtest_sma20_pts(o, c_prev, sma_prev, cost):
    n = len(o)
    pos = 0 
    trades = 0
    wins = 0
    total_pts = 0.0
    gross_pos_pts = 0.0
    gross_neg_pts = 0.0
    
    entry_price = 0.0
    
    for i in range(1, n):
        if np.isnan(sma_prev[i]) or np.isnan(c_prev[i]):
            continue
            
        if c_prev[i] > sma_prev[i]:
            if pos != 1:
                if pos == -1:
                    exit_price = o[i]
                    pnl = entry_price - exit_price - cost
                    trades += 1
                    total_pts += pnl
                    if pnl > 0:
                        wins += 1
                        gross_pos_pts += pnl
                    else:
                        gross_neg_pts += abs(pnl)
                
                pos = 1
                entry_price = o[i]
                
        elif c_prev[i] < sma_prev[i]:
            if pos != -1:
                if pos == 1:
                    exit_price = o[i]
                    pnl = exit_price - entry_price - cost
                    trades += 1
                    total_pts += pnl
                    if pnl > 0:
                        wins += 1
                        gross_pos_pts += pnl
                    else:
                        gross_neg_pts += abs(pnl)
                
                pos = -1
                entry_price = o[i]

    return trades, total_pts, gross_pos_pts, gross_neg_pts, wins

trades, total_pts, gross_pos_pts, gross_neg_pts, wins = backtest_sma20_pts(o, c_prev, sma_prev, 0.5)

print(f"Total Trades: {trades:,}")
if trades > 0:
    print(f"Win Rate:     {wins/trades*100:.1f}%")
    print(f"Total Pts:    {total_pts:.2f} pts (${total_pts*20:,.2f})")
    print(f"Avg Pts/Trade:{total_pts/trades:.4f} pts")
    pf_pts = gross_pos_pts / gross_neg_pts if gross_neg_pts > 0 else float('inf')
    print(f"Profit Factor (Pts):{pf_pts:.2f}")
