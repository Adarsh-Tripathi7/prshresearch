import pandas as pd
import numpy as np
from numba import njit
import time

print("Loading 1-min data...")
t0 = time.time()
df = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")

df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
df = df.sort_values('Datetime').reset_index(drop=True)
df.set_index('Datetime', inplace=True)

df_5m = df.resample('5min').agg({
    'Open': 'first', 'High': 'max', 'Low': 'min', 'Last': 'last', 'Volume': 'sum'
}).dropna()

df_5m['DonH'] = df_5m['High'].rolling(2).max().shift(1)
df_5m['DonL'] = df_5m['Low'].rolling(2).min().shift(1)

df['floor_5m'] = df.index.floor('5min')
df_joined = df.join(df_5m[['DonH', 'DonL']], on='floor_5m')

c = df_joined['Last'].values.astype(np.float64)
h = df_joined['High'].values.astype(np.float64)
l = df_joined['Low'].values.astype(np.float64)
o = df_joined['Open'].values.astype(np.float64)
don_h = df_joined['DonH'].values.astype(np.float64)
don_l = df_joined['DonL'].values.astype(np.float64)

@njit
def backtest_donchian_pts(o, h, l, c, don_h, don_l, cost):
    n = len(c)
    pos = 0 
    trades = 0
    wins = 0
    total_pts = 0.0
    gross_pos_pts = 0.0
    gross_neg_pts = 0.0
    
    entry_price = 0.0
    
    for i in range(1, n):
        if np.isnan(don_h[i]) or np.isnan(don_l[i]):
            continue
            
        if pos == 0:
            if h[i] > don_h[i]:
                pos = 1
                entry_price = max(o[i], don_h[i])
            elif l[i] < don_l[i]:
                pos = -1
                entry_price = min(o[i], don_l[i])
        
        elif pos == 1:
            if l[i] <= don_l[i]:
                exit_price = min(o[i], don_l[i])
                pnl = exit_price - entry_price - cost
                
                trades += 1
                total_pts += pnl
                if pnl > 0:
                    wins += 1
                    gross_pos_pts += pnl
                else:
                    gross_neg_pts += abs(pnl)
                
                pos = -1
                entry_price = exit_price
                
        elif pos == -1:
            if h[i] >= don_h[i]:
                exit_price = max(o[i], don_h[i])
                pnl = entry_price - exit_price - cost
                
                trades += 1
                total_pts += pnl
                if pnl > 0:
                    wins += 1
                    gross_pos_pts += pnl
                else:
                    gross_neg_pts += abs(pnl)
                
                pos = 1
                entry_price = exit_price

    return trades, total_pts, gross_pos_pts, gross_neg_pts, wins

trades, total_pts, gross_pos_pts, gross_neg_pts, wins = backtest_donchian_pts(o, h, l, c, don_h, don_l, 0.5)

print(f"Total Trades: {trades:,}")
if trades > 0:
    print(f"Win Rate:     {wins/trades*100:.1f}%")
    print(f"Total Pts:    {total_pts:.2f} pts (${total_pts*20:,.2f})")
    print(f"Avg Pts/Trade:{total_pts/trades:.4f} pts")
    pf_pts = gross_pos_pts / gross_neg_pts if gross_neg_pts > 0 else float('inf')
    print(f"Profit Factor (Pts):{pf_pts:.2f}")
