import pandas as pd
import numpy as np
from numba import njit
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time

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
def run_backtest(
    session_starts, session_ends, mins_arr, 
    nq_h_arr, nq_l_arr, nq_c_arr, es_h_arr, es_l_arr, es_c_arr
):
    num_sessions = len(session_starts)
    
    # 20:30 to 21:29
    start_m = 210
    end_m = 269
    rth_close_m = 1380 # 16:00 EST
    
    nq_pnl = np.zeros(num_sessions, dtype=np.float32)
    nq_traded = np.zeros(num_sessions, dtype=np.int32)
    
    es_pnl = np.zeros(num_sessions, dtype=np.float32)
    es_traded = np.zeros(num_sessions, dtype=np.int32)
    
    for s in range(num_sessions):
        idx_start = session_starts[s]
        idx_end = session_ends[s]
        
        ib_nq_h = -1.0
        ib_nq_l = 1e9
        ib_es_h = -1.0
        ib_es_l = 1e9
        
        has_ib = False
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m >= start_m and m <= end_m:
                if nq_h_arr[i] > ib_nq_h: ib_nq_h = nq_h_arr[i]
                if nq_l_arr[i] < ib_nq_l: ib_nq_l = nq_l_arr[i]
                if es_h_arr[i] > ib_es_h: ib_es_h = es_h_arr[i]
                if es_l_arr[i] < ib_es_l: ib_es_l = es_l_arr[i]
                has_ib = True
            elif m > end_m:
                break
                
        if not has_ib:
            continue
            
        nq_r = ib_nq_h - ib_nq_l
        es_r = ib_es_h - ib_es_l
        if nq_r <= 0 or es_r <= 0:
            continue
            
        # NQ Trade Logic
        in_nq_trade = False
        nq_setup_valid = True
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > end_m and m <= rth_close_m:
                if not in_nq_trade and nq_setup_valid:
                    if nq_l_arr[i] < ib_nq_l:
                        nq_setup_valid = False
                    elif nq_h_arr[i] > ib_nq_h:
                        in_nq_trade = True
                        nq_tp = ib_nq_h + 1.34 * nq_r
                        nq_sl = ib_nq_l
                        
                        if nq_l_arr[i] <= nq_sl:
                            nq_pnl[s] = -1.0
                            nq_traded[s] = -1 # Loss
                            break
                        elif nq_h_arr[i] >= nq_tp:
                            nq_pnl[s] = 1.34
                            nq_traded[s] = 1 # Win
                            break
                elif in_nq_trade:
                    if nq_l_arr[i] <= nq_sl:
                        nq_pnl[s] = -1.0
                        nq_traded[s] = -1
                        break
                    elif nq_h_arr[i] >= nq_tp:
                        nq_pnl[s] = 1.34
                        nq_traded[s] = 1
                        break
            elif m > rth_close_m:
                if in_nq_trade and nq_traded[s] == 0:
                    # Time Stop
                    exit_price = nq_c_arr[i-1] # Close of 16:00 bar
                    pnl_r = (exit_price - ib_nq_h) / nq_r
                    nq_pnl[s] = pnl_r
                    nq_traded[s] = 2 # Time Stop
                break
                
        # ES Trade Logic
        in_es_trade = False
        es_setup_valid = True
        for i in range(idx_start, idx_end):
            m = mins_arr[i]
            if m > end_m and m <= rth_close_m:
                if not in_es_trade and es_setup_valid:
                    if es_l_arr[i] < ib_es_l:
                        es_setup_valid = False
                    elif es_h_arr[i] > ib_es_h:
                        in_es_trade = True
                        es_tp = ib_es_h + 1.34 * es_r
                        es_sl = ib_es_l
                        
                        if es_l_arr[i] <= es_sl:
                            es_pnl[s] = -1.0
                            es_traded[s] = -1
                            break
                        elif es_h_arr[i] >= es_tp:
                            es_pnl[s] = 1.34
                            es_traded[s] = 1
                            break
                elif in_es_trade:
                    if es_l_arr[i] <= es_sl:
                        es_pnl[s] = -1.0
                        es_traded[s] = -1
                        break
                    elif es_h_arr[i] >= es_tp:
                        es_pnl[s] = 1.34
                        es_traded[s] = 1
                        break
            elif m > rth_close_m:
                if in_es_trade and es_traded[s] == 0:
                    exit_price = es_c_arr[i-1]
                    pnl_r = (exit_price - ib_es_h) / es_r
                    es_pnl[s] = pnl_r
                    es_traded[s] = 2
                break
                
    return nq_pnl, nq_traded, es_pnl, es_traded

def main():
    results_dir = r"d:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    
    t0 = time.time()
    print("Loading datasets (via pyarrow)...")
    nq_1m = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
    es_1m = pd.read_parquet(r"d:\Antigravity\Historical data\ES Futures Datasets\Full Data\parquet\ES_1m_full_data.parquet")

    nq_1m = nq_1m[['Date', 'Time', 'High', 'Low', 'Last']].rename(
        columns={'High': 'NQ_High', 'Low': 'NQ_Low', 'Last': 'NQ_Close'})
    es_1m = es_1m[['Date', 'Time', 'High', 'Low', 'Last']].rename(
        columns={'High': 'ES_High', 'Low': 'ES_Low', 'Last': 'ES_Close'})
        
    print("Merging datasets...")
    df = pd.merge(nq_1m, es_1m, on=['Date', 'Time'], how='inner')
    
    df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['SessionDate'] = pd.to_datetime(df['Datetime'].apply(get_session_date))
    df['Mins'] = df['Datetime'].apply(calc_mins_from_start)
    
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    print("Preparing arrays for Numba JIT compilation...")
    unique_sessions = df['SessionDate'].unique()
    session_map = {sess: i for i, sess in enumerate(unique_sessions)}
    session_idx_arr = df['SessionDate'].map(session_map).values.astype(np.int32)

    mins_arr = df['Mins'].values.astype(np.int32)
    nq_h_arr = df['NQ_High'].values.astype(np.float32)
    nq_l_arr = df['NQ_Low'].values.astype(np.float32)
    nq_c_arr = df['NQ_Close'].values.astype(np.float32)
    es_h_arr = df['ES_High'].values.astype(np.float32)
    es_l_arr = df['ES_Low'].values.astype(np.float32)
    es_c_arr = df['ES_Close'].values.astype(np.float32)

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
    
    print("Running Backtest Engine (Numba JIT)...")
    t_numba_start = time.time()
    nq_pnl, nq_traded, es_pnl, es_traded = run_backtest(
        session_starts, session_ends, mins_arr, 
        nq_h_arr, nq_l_arr, nq_c_arr, es_h_arr, es_l_arr, es_c_arr
    )
    t_numba_end = time.time()
    print(f"Numba computation took: {t_numba_end - t_numba_start:.4f} seconds!")

    # ---------------------------------------------------------
    # BUILD RESULTS
    # ---------------------------------------------------------
    res_df = pd.DataFrame({
        'Date': unique_sessions,
        'NQ_PnL': nq_pnl,
        'NQ_Traded': nq_traded,
        'ES_PnL': es_pnl,
        'ES_Traded': es_traded
    }).sort_values('Date').reset_index(drop=True)
    
    res_df['NQ_Cumulative_R'] = res_df['NQ_PnL'].cumsum()
    res_df['ES_Cumulative_R'] = res_df['ES_PnL'].cumsum()
    
    # Calculate Stats
    def get_stats(pnl, traded):
        total_trades = (traded != 0).sum()
        if total_trades == 0: return {}
        
        wins = (traded == 1).sum()
        losses = (traded == -1).sum()
        time_stops = (traded == 2).sum()
        
        win_rate = (wins / total_trades) * 100
        gross_profit = pnl[pnl > 0].sum()
        gross_loss = abs(pnl[pnl < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        ev = pnl.sum() / total_trades
        
        return {
            'Total Trades': total_trades,
            'Wins (Hit TP)': wins,
            'Losses (Hit SL)': losses,
            'Time Stops (16:00)': time_stops,
            'Win Rate (%)': f"{win_rate:.2f}%",
            'Total Profit (R)': f"{pnl.sum():.2f}R",
            'Profit Factor': f"{profit_factor:.2f}",
            'Expected Value per Trade': f"{ev:.2f}R"
        }
        
    nq_stats = get_stats(res_df['NQ_PnL'], res_df['NQ_Traded'])
    es_stats = get_stats(res_df['ES_PnL'], res_df['ES_Traded'])
    
    # Plot Equity Curve
    plt.figure(figsize=(12, 6))
    plt.plot(res_df['Date'], res_df['NQ_Cumulative_R'], label='NQ Equity', color='blue')
    plt.plot(res_df['Date'], res_df['ES_Cumulative_R'], label='ES Equity', color='orange')
    plt.title('20:30 IB Breakout Strategy: Cumulative Equity (in R-Multiples)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Profit (R)')
    plt.legend()
    plt.grid(True)
    
    plots_path = os.path.join(results_dir, "strategy_2030_equity_curve.png")
    plt.savefig(plots_path, dpi=300)
    plt.close()
    
    report = f"""# 🚀 Backtest Results: 20:30 IB Long-Only Breakout
*Testing a pure structural system over the last decade on the Asian Session (20:30-21:29) Initial Balance.*

## ⚙️ Strategy Rules
- **Entry:** Long when price breaks IB High.
- **Stop Loss:** Placed exactly at IB Low (Risk = `1R`).
- **Take Profit:** Fixed at 134% Extension above IB High (Reward = `1.34R`).
- **Time Stop:** Exit at 16:00 EST close if neither TP nor SL hit.

## 📊 NQ Performance Metrics
- **Total Trades:** {nq_stats['Total Trades']}
- **Wins (Hit TP):** {nq_stats['Wins (Hit TP)']}
- **Losses (Hit SL):** {nq_stats['Losses (Hit SL)']}
- **Time Stops (16:00):** {nq_stats['Time Stops (16:00)']}
- **Win Rate:** **{nq_stats['Win Rate (%)']}**
- **Profit Factor:** **{nq_stats['Profit Factor']}**
- **Expected Value (per trade):** `{nq_stats['Expected Value per Trade']}`
- **Total Net Profit:** **{nq_stats['Total Profit (R)']}**

## 📊 ES Performance Metrics
- **Total Trades:** {es_stats['Total Trades']}
- **Wins (Hit TP):** {es_stats['Wins (Hit TP)']}
- **Losses (Hit SL):** {es_stats['Losses (Hit SL)']}
- **Time Stops (16:00):** {es_stats['Time Stops (16:00)']}
- **Win Rate:** **{es_stats['Win Rate (%)']}**
- **Profit Factor:** **{es_stats['Profit Factor']}**
- **Expected Value (per trade):** `{es_stats['Expected Value per Trade']}`
- **Total Net Profit:** **{es_stats['Total Profit (R)']}**

## 📈 Equity Curve
*Assuming exact same risk (1R) on every single trade.*
![Equity Curve](file:///{plots_path.replace('\\', '/')})

## 💡 Quantitative Conclusion
If the Equity Curve goes down, this proves the 20:30 IB is prone to fake-outs (Double Breaks) and you should **never** buy the breakout, but instead FADE the breakout. If the curve goes up, it proves the Asian session initiates true structural trends! Let's look at the chart above to find out.
"""

    dashboard_path = os.path.join(results_dir, "strategy_2030_dashboard.md")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Dashboard saved to {dashboard_path}")

if __name__ == "__main__":
    main()
