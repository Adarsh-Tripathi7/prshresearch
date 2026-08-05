"""
Strategy: 9:23-9:29 Pre-Market Range Breakdown (Short Only)
-------------------------------------------------------------
Rules:
  1. Mark the High and Low of 9:23 to 9:29 AM candles (inclusive).
  2. After 9:29, if price breaks BELOW the range Low first -> SELL SHORT.
  3. If the High is broken first -> NO TRADE (invalidated).
  4. Entry = Range Low (on break below).
  5. Stop Loss = Range High.
  6. Risk (R) = Range High - Range Low.
  7. Take Profit = Entry - 0.25 * R  (targeting 0.25R reward).
  8. Same risk per trade.

Edge Cases:
  - If both High and Low are broken on the same candle -> Entry Clash -> no trade.
  - If TP and SL are hit on the same candle -> Exit Clash -> SL assumed (conservative).
  - If neither TP nor SL hit by EOD -> trade closed at last close (mark-to-market).

Output:
  - Headline statistics
  - Breakdown by Year, Month, Day of Week
  - Full trade log CSV
  - Equity curve data
"""

import pandas as pd
import numpy as np
from numba import njit
import time
import os
import warnings
warnings.filterwarnings('ignore')


# --- Numba-optimized core engine -----------------------------------------------

@njit
def backtest_core(dates_int, times_min, highs, lows, closes,
                  day_starts, day_ends, n_days,
                  w_start=563, w_end=569, target_r=0.25):
    """
    Core backtest loop in Numba for maximum speed.
    
    times_min: minutes since midnight (e.g. 9:23 = 563, 9:29 = 569)
    w_start / w_end: window start/end in minutes since midnight
    
    Per-trade output arrays (pre-allocated for n_days max):
      trade_dates, trade_pnl, trade_r_multiple, trade_entry, trade_sl, trade_tp,
      trade_exit_price, trade_type (0=no_trade, 1=tp_hit, 2=sl_hit, 3=eod_close, 4=invalidated, 5=entry_clash, 6=exit_clash)
      trade_range_size
    """
    # Output arrays
    trade_date     = np.empty(n_days, dtype=np.int64)
    trade_pnl      = np.empty(n_days, dtype=np.float64)
    trade_r_mult   = np.empty(n_days, dtype=np.float64)
    trade_entry    = np.empty(n_days, dtype=np.float64)
    trade_sl       = np.empty(n_days, dtype=np.float64)
    trade_tp       = np.empty(n_days, dtype=np.float64)
    trade_exit_px  = np.empty(n_days, dtype=np.float64)
    trade_type     = np.empty(n_days, dtype=np.int32)   # 0=no_setup, 1=tp, 2=sl, 3=eod, 4=invalidated, 5=entry_clash, 6=exit_clash_sl
    trade_range    = np.empty(n_days, dtype=np.float64)
    trade_entry_time = np.empty(n_days, dtype=np.int32)  # minute of entry
    trade_exit_time  = np.empty(n_days, dtype=np.int32)  # minute of exit
    
    t_idx = 0  # trade counter
    
    for d in range(n_days):
        si = day_starts[d]
        ei = day_ends[d]
        
        # -- Step 1: Find range high/low in [w_start, w_end] --
        w_high = -1e18
        w_low  =  1e18
        has_range = False
        
        for i in range(si, ei):
            m = times_min[i]
            if m >= w_start and m <= w_end:
                if highs[i] > w_high:
                    w_high = highs[i]
                if lows[i] < w_low:
                    w_low = lows[i]
                has_range = True
        
        if not has_range or w_high <= w_low:
            trade_date[t_idx]    = dates_int[si]
            trade_pnl[t_idx]     = 0.0
            trade_r_mult[t_idx]  = 0.0
            trade_entry[t_idx]   = 0.0
            trade_sl[t_idx]      = 0.0
            trade_tp[t_idx]      = 0.0
            trade_exit_px[t_idx] = 0.0
            trade_type[t_idx]    = 0  # no setup
            trade_range[t_idx]   = 0.0
            trade_entry_time[t_idx] = 0
            trade_exit_time[t_idx]  = 0
            t_idx += 1
            continue
        
        R = w_high - w_low
        entry_px = w_low           # sell at range low break
        sl_px    = w_high          # SL above range high
        tp_px    = entry_px - target_r * R  # TP = 0.25R below entry
        
        # -- Step 2: Scan post-range candles --
        entered     = False
        invalidated = False
        resolved    = False
        pnl         = 0.0
        r_mult      = 0.0
        exit_px     = 0.0
        ttype       = 0
        entry_min   = 0
        exit_min    = 0
        
        for i in range(si, ei):
            m = times_min[i]
            if m <= w_end:
                continue  # still in range window
            
            h = highs[i]
            l = lows[i]
            
            if not entered and not invalidated:
                breaks_low  = l < w_low     # strictly below -> entry trigger
                breaks_high = h > w_high    # strictly above -> invalidation
                
                if breaks_low and breaks_high:
                    # Entry clash: both broken on same candle
                    ttype = 5
                    invalidated = True
                    resolved = True
                    break
                elif breaks_high:
                    # High broken first -> no trade
                    ttype = 4
                    invalidated = True
                    resolved = True
                    break
                elif breaks_low:
                    # Low broken -> SHORT ENTRY
                    entered = True
                    entry_min = m
                    
                    # Check if TP/SL also hit on this same candle
                    hits_tp = l <= tp_px
                    hits_sl = h >= sl_px
                    
                    if hits_tp and hits_sl:
                        # Exit clash -> conservative: assume SL
                        ttype   = 6
                        pnl     = -(sl_px - entry_px)  # loss for short
                        r_mult  = pnl / R
                        exit_px = sl_px
                        exit_min = m
                        resolved = True
                        break
                    elif hits_tp:
                        ttype   = 1
                        pnl     = entry_px - tp_px  # profit for short
                        r_mult  = pnl / R
                        exit_px = tp_px
                        exit_min = m
                        resolved = True
                        break
                    elif hits_sl:
                        ttype   = 2
                        pnl     = -(sl_px - entry_px)  # loss for short
                        r_mult  = pnl / R
                        exit_px = sl_px
                        exit_min = m
                        resolved = True
                        break
            
            elif entered:
                hits_tp = l <= tp_px
                hits_sl = h >= sl_px
                
                if hits_tp and hits_sl:
                    ttype   = 6
                    pnl     = -(sl_px - entry_px)
                    r_mult  = pnl / R
                    exit_px = sl_px
                    exit_min = m
                    resolved = True
                    break
                elif hits_tp:
                    ttype   = 1
                    pnl     = entry_px - tp_px
                    r_mult  = pnl / R
                    exit_px = tp_px
                    exit_min = m
                    resolved = True
                    break
                elif hits_sl:
                    ttype   = 2
                    pnl     = -(sl_px - entry_px)
                    r_mult  = pnl / R
                    exit_px = sl_px
                    exit_min = m
                    resolved = True
                    break
        
        # EOD close if still in trade
        if entered and not resolved:
            eod_close = closes[ei - 1]
            pnl     = entry_px - eod_close  # short P&L
            r_mult  = pnl / R
            exit_px = eod_close
            ttype   = 3
            exit_min = times_min[ei - 1]
        
        trade_date[t_idx]       = dates_int[si]
        trade_pnl[t_idx]        = pnl
        trade_r_mult[t_idx]     = r_mult
        trade_entry[t_idx]      = entry_px if entered else 0.0
        trade_sl[t_idx]         = sl_px
        trade_tp[t_idx]         = tp_px
        trade_exit_px[t_idx]    = exit_px
        trade_type[t_idx]       = ttype
        trade_range[t_idx]      = R
        trade_entry_time[t_idx] = entry_min
        trade_exit_time[t_idx]  = exit_min
        t_idx += 1
    
    return (trade_date[:t_idx], trade_pnl[:t_idx], trade_r_mult[:t_idx],
            trade_entry[:t_idx], trade_sl[:t_idx], trade_tp[:t_idx],
            trade_exit_px[:t_idx], trade_type[:t_idx], trade_range[:t_idx],
            trade_entry_time[:t_idx], trade_exit_time[:t_idx])


# --- Data Loading & Preparation -----------------------------------------------

def load_and_prepare(file_path):
    """Load parquet and compute time/session fields."""
    print(f"  Loading data from {os.path.basename(file_path)}...")
    df = pd.read_parquet(file_path)
    
    # Parse time to minutes since midnight
    hours   = df['Time'].str[:2].astype(int)
    minutes = df['Time'].str[3:5].astype(int)
    df['time_min'] = hours * 60 + minutes
    
    # Create datetime for session grouping
    df['dt'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    
    # Session date: roll overnight bars to the next trading day
    # For this strategy we only care about 9:23+ so we can use the calendar date
    df['session_date'] = df['Date'].dt.date
    
    # Integer date for Numba (YYYYMMDD)
    df['date_int'] = (df['Date'].dt.year * 10000 + 
                      df['Date'].dt.month * 100 + 
                      df['Date'].dt.day).astype(np.int64)
    
    # Sort
    df = df.sort_values(['session_date', 'time_min']).reset_index(drop=True)
    
    # Compute day start/end indices
    day_groups = df.groupby('session_date')
    day_starts = day_groups.apply(lambda x: x.index[0]).values.astype(np.int64)
    day_ends   = day_groups.apply(lambda x: x.index[-1] + 1).values.astype(np.int64)
    n_days     = len(day_starts)
    
    print(f"  {len(df):,} bars | {n_days:,} trading days | "
          f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")
    
    return df, day_starts, day_ends, n_days


# --- Statistics Computation ----------------------------------------------------

def compute_stats(trades_df, label="Overall"):
    """Compute comprehensive trading statistics using R-multiples (same risk per trade)."""
    # Filter to actual trades only (type 1,2,3,6 = tp, sl, eod, exit_clash)
    actual = trades_df[trades_df['type'].isin([1, 2, 3, 6])].copy()
    
    if len(actual) == 0:
        return {}
    
    total_sessions = len(trades_df)
    invalidated    = len(trades_df[trades_df['type'] == 4])
    entry_clashes  = len(trades_df[trades_df['type'] == 5])
    no_setup       = len(trades_df[trades_df['type'] == 0])
    
    # Use R-multiples for all P&L calculations (same risk per trade)
    r = actual['r_mult']
    
    n_trades  = len(actual)
    wins      = actual[r > 0]
    losses    = actual[r <= 0]
    n_wins    = len(wins)
    n_losses  = len(losses)
    
    total_r     = r.sum()
    avg_r       = r.mean()
    median_r    = r.median()
    std_r       = r.std() if n_trades > 1 else 0
    
    win_rate    = n_wins / n_trades * 100 if n_trades > 0 else 0
    avg_win_r   = wins['r_mult'].mean() if n_wins > 0 else 0
    avg_loss_r  = losses['r_mult'].mean() if n_losses > 0 else 0
    
    # Profit Factor (in R)
    gross_profit_r = wins['r_mult'].sum() if n_wins > 0 else 0
    gross_loss_r   = abs(losses['r_mult'].sum()) if n_losses > 0 else 0
    profit_factor  = gross_profit_r / gross_loss_r if gross_loss_r > 0 else float('inf')
    
    # Payoff Ratio (avg win R / avg loss R)
    payoff_ratio = abs(avg_win_r / avg_loss_r) if avg_loss_r != 0 else float('inf')
    
    # Max consecutive wins/losses
    streaks = r.apply(lambda x: 1 if x > 0 else 0).values
    max_win_streak = 0
    max_loss_streak = 0
    cur_w = 0
    cur_l = 0
    for s in streaks:
        if s == 1:
            cur_w += 1
            cur_l = 0
            if cur_w > max_win_streak:
                max_win_streak = cur_w
        else:
            cur_l += 1
            cur_w = 0
            if cur_l > max_loss_streak:
                max_loss_streak = cur_l
    
    # Drawdown (in R)
    equity_r = r.cumsum()
    peak_r   = equity_r.cummax()
    dd_r     = equity_r - peak_r
    max_dd_r = dd_r.min()
    
    # Sharpe (annualized, assuming ~252 trading days)
    sharpe = (avg_r / std_r * np.sqrt(252)) if std_r > 0 else 0
    
    # Sortino
    downside_r = actual[r < 0]['r_mult'].std()
    sortino    = (avg_r / downside_r * np.sqrt(252)) if downside_r and downside_r > 0 else 0
    
    # Calmar
    calmar = (total_r / abs(max_dd_r)) if max_dd_r != 0 else 0
    
    # Exit type counts
    tp_trades    = len(actual[actual['type'] == 1])
    sl_trades    = len(actual[actual['type'] == 2])
    eod_trades   = len(actual[actual['type'] == 3])
    clash_trades = len(actual[actual['type'] == 6])
    
    # Avg range size (raw points, for reference)
    avg_range = actual['range'].mean()
    
    # Avg holding time (minutes)
    actual_with_time = actual[(actual['entry_time'] > 0) & (actual['exit_time'] > 0)]
    avg_hold = (actual_with_time['exit_time'] - actual_with_time['entry_time']).mean() if len(actual_with_time) > 0 else 0
    
    # Best / Worst trade (in R)
    best_trade_r  = r.max()
    worst_trade_r = r.min()
    
    # Skewness & Kurtosis
    skew = r.skew() if n_trades > 2 else 0
    kurt = r.kurtosis() if n_trades > 3 else 0
    
    # Also keep raw point P&L for reference
    total_pnl_pts = actual['pnl'].sum()
    avg_pnl_pts   = actual['pnl'].mean()
    
    return {
        'label': label,
        'total_sessions': total_sessions,
        'no_setup': no_setup,
        'invalidated': invalidated,
        'entry_clashes': entry_clashes,
        'n_trades': n_trades,
        'n_wins': n_wins,
        'n_losses': n_losses,
        'win_rate': win_rate,
        'total_r': total_r,
        'avg_r': avg_r,
        'median_r': median_r,
        'std_r': std_r,
        'avg_win_r': avg_win_r,
        'avg_loss_r': avg_loss_r,
        'profit_factor': profit_factor,
        'payoff_ratio': payoff_ratio,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'max_drawdown_r': max_dd_r,
        'sharpe': sharpe,
        'sortino': sortino,
        'calmar': calmar,
        'tp_exits': tp_trades,
        'sl_exits': sl_trades,
        'eod_exits': eod_trades,
        'exit_clashes': clash_trades,
        'avg_range': avg_range,
        'avg_hold_min': avg_hold,
        'best_trade_r': best_trade_r,
        'worst_trade_r': worst_trade_r,
        'gross_profit_r': gross_profit_r,
        'gross_loss_r': gross_loss_r,
        'skewness': skew,
        'kurtosis': kurt,
        'total_pnl_pts': total_pnl_pts,
        'avg_pnl_pts': avg_pnl_pts,
    }


def print_stats(s):
    """Pretty-print a stats dictionary (all P&L in R-multiples = same risk per trade)."""
    if not s:
        print("  No trades to display.\n")
        return
    
    print(f"\n{'=' * 65}")
    print(f"  {s['label']}")
    print(f"  [All P&L in R-multiples | 1R = risk per trade]")
    print(f"{'=' * 65}")
    print(f"  Sessions Analyzed    : {s['total_sessions']:>8,}")
    print(f"  No Setup (no data)   : {s['no_setup']:>8,}")
    print(f"  Invalidated (H first): {s['invalidated']:>8,}")
    print(f"  Entry Clashes        : {s['entry_clashes']:>8,}")
    print(f"{'-' * 65}")
    print(f"  Total Trades Taken   : {s['n_trades']:>8,}")
    print(f"  Wins                 : {s['n_wins']:>8,}   ({s['win_rate']:.1f}%)")
    print(f"  Losses               : {s['n_losses']:>8,}   ({100 - s['win_rate']:.1f}%)")
    print(f"{'-' * 65}")
    print(f"  Total P&L (R)        : {s['total_r']:>10.2f}R")
    print(f"  Avg P&L / Trade (R)  : {s['avg_r']:>10.4f}R")
    print(f"  Median P&L (R)       : {s['median_r']:>10.4f}R")
    print(f"  Std Dev (R)          : {s['std_r']:>10.4f}R")
    print(f"  Best Trade (R)       : {s['best_trade_r']:>10.4f}R")
    print(f"  Worst Trade (R)      : {s['worst_trade_r']:>10.4f}R")
    print(f"{'-' * 65}")
    print(f"  Avg Win (R)          : {s['avg_win_r']:>10.4f}R")
    print(f"  Avg Loss (R)         : {s['avg_loss_r']:>10.4f}R")
    print(f"  Payoff Ratio         : {s['payoff_ratio']:>10.2f}")
    print(f"  Profit Factor        : {s['profit_factor']:>10.2f}")
    print(f"{'-' * 65}")
    print(f"  Gross Profit (R)     : {s['gross_profit_r']:>10.2f}R")
    print(f"  Gross Loss (R)       : {s['gross_loss_r']:>10.2f}R")
    print(f"  Max Drawdown (R)     : {s['max_drawdown_r']:>10.2f}R")
    print(f"{'-' * 65}")
    print(f"  Sharpe (ann.)        : {s['sharpe']:>10.2f}")
    print(f"  Sortino (ann.)       : {s['sortino']:>10.2f}")
    print(f"  Calmar Ratio         : {s['calmar']:>10.2f}")
    print(f"  Skewness             : {s['skewness']:>10.2f}")
    print(f"  Kurtosis             : {s['kurtosis']:>10.2f}")
    print(f"{'-' * 65}")
    print(f"  Max Win Streak       : {s['max_win_streak']:>8,}")
    print(f"  Max Loss Streak      : {s['max_loss_streak']:>8,}")
    print(f"  Avg Range Size (pts) : {s['avg_range']:>10.2f}")
    print(f"  Avg Hold Time (min)  : {s['avg_hold_min']:>10.1f}")
    print(f"{'-' * 65}")
    print(f"  Ref: Total PnL (pts) : {s['total_pnl_pts']:>10.2f}")
    print(f"  Ref: Avg PnL (pts)   : {s['avg_pnl_pts']:>10.2f}")
    print(f"{'-' * 65}")
    print(f"  Exit Breakdown:")
    print(f"    TP Hit             : {s['tp_exits']:>8,}")
    print(f"    SL Hit             : {s['sl_exits']:>8,}")
    print(f"    EOD Close          : {s['eod_exits']:>8,}")
    print(f"    Exit Clashes (->SL): {s['exit_clashes']:>8,}")
    print(f"{'=' * 65}\n")


def stats_to_row(s):
    """Convert stats dict to a flat row for tabular output (R-multiples)."""
    if not s:
        return {}
    return {
        'Period': s['label'],
        'Trades': s['n_trades'],
        'Wins': s['n_wins'],
        'Losses': s['n_losses'],
        'Win%': round(s['win_rate'], 1),
        'TotalR': round(s['total_r'], 2),
        'AvgR': round(s['avg_r'], 4),
        'PF': round(s['profit_factor'], 2),
        'Payoff': round(s['payoff_ratio'], 2),
        'Sharpe': round(s['sharpe'], 2),
        'MaxDD_R': round(s['max_drawdown_r'], 2),
        'AvgRange': round(s['avg_range'], 2),
    }


# --- Main ---------------------------------------------------------------------

def main():
    print("\n" + "=" * 65)
    print("  NQ 9:23-9:29 Pre-Market Range Breakdown -- SHORT ONLY")
    print("  SAME RISK PER TRADE (All P&L in R-multiples)")
    print("  Target: 0.25R | SL: Range High | Entry: Break Below Low")
    print("=" * 65 + "\n")
    
    # -- Load Data --
    nq_path = r"D:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet"
    df, day_starts, day_ends, n_days = load_and_prepare(nq_path)
    
    # -- Run Backtest --
    print("\n  Running Numba-optimized backtest...")
    t0 = time.time()
    
    results = backtest_core(
        df['date_int'].values,
        df['time_min'].values.astype(np.int32),
        df['High'].values.astype(np.float64),
        df['Low'].values.astype(np.float64),
        df['Last'].values.astype(np.float64),
        day_starts.astype(np.int64),
        day_ends.astype(np.int64),
        n_days,
        w_start=563,  # 9:23 = 9*60+23
        w_end=569,    # 9:29 = 9*60+29
        target_r=0.25
    )
    
    t1 = time.time()
    print(f"  [OK] Backtest completed in {t1 - t0:.3f}s\n")
    
    # -- Build Trade Log DataFrame --
    (trade_date, trade_pnl, trade_r_mult, trade_entry, trade_sl,
     trade_tp, trade_exit_px, trade_type, trade_range,
     trade_entry_time, trade_exit_time) = results
    
    trades = pd.DataFrame({
        'date_int':   trade_date,
        'pnl':        trade_pnl,
        'r_mult':     trade_r_mult,
        'entry':      trade_entry,
        'sl':         trade_sl,
        'tp':         trade_tp,
        'exit_px':    trade_exit_px,
        'type':       trade_type,
        'range':      trade_range,
        'entry_time': trade_entry_time,
        'exit_time':  trade_exit_time,
    })
    
    # Parse date
    trades['date'] = pd.to_datetime(trades['date_int'].astype(str), format='%Y%m%d')
    trades['year']  = trades['date'].dt.year
    trades['month'] = trades['date'].dt.month
    trades['dow']   = trades['date'].dt.dayofweek  # 0=Mon, 4=Fri
    trades['dow_name'] = trades['date'].dt.day_name()
    
    # Type labels
    type_map = {0: 'No Setup', 1: 'TP Hit', 2: 'SL Hit', 3: 'EOD Close',
                4: 'Invalidated', 5: 'Entry Clash', 6: 'Exit Clash->SL'}
    trades['type_label'] = trades['type'].map(type_map)
    
    # -- Overall Stats --
    overall = compute_stats(trades, "OVERALL -- NQ 9:23-9:29 Short (0.25R Target)")
    print_stats(overall)
    
    # -- By Year --
    print("\n" + "#" * 60)
    print("  BREAKDOWN BY YEAR")
    print("#" * 60)
    year_rows = []
    for yr in sorted(trades['year'].unique()):
        s = compute_stats(trades[trades['year'] == yr], f"Year {yr}")
        if s:
            print_stats(s)
            year_rows.append(stats_to_row(s))
    
    if year_rows:
        yr_df = pd.DataFrame(year_rows)
        print("\n  -- Year Summary Table --")
        print(yr_df.to_string(index=False))
    
    # -- By Month --
    print("\n\n" + "#" * 60)
    print("  BREAKDOWN BY MONTH")
    print("#" * 60)
    month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                   7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    month_rows = []
    for mo in range(1, 13):
        subset = trades[trades['month'] == mo]
        if len(subset) > 0:
            s = compute_stats(subset, f"Month: {month_names[mo]}")
            if s:
                month_rows.append(stats_to_row(s))
    
    if month_rows:
        mo_df = pd.DataFrame(month_rows)
        print("\n  -- Month Summary Table --")
        print(mo_df.to_string(index=False))
    
    # -- By Day of Week --
    print("\n\n" + "#" * 60)
    print("  BREAKDOWN BY DAY OF WEEK")
    print("#" * 60)
    dow_rows = []
    for dow in range(5):  # Mon-Fri
        subset = trades[trades['dow'] == dow]
        if len(subset) > 0:
            day_name = ['Monday','Tuesday','Wednesday','Thursday','Friday'][dow]
            s = compute_stats(subset, f"Day: {day_name}")
            if s:
                dow_rows.append(stats_to_row(s))
    
    if dow_rows:
        dow_df = pd.DataFrame(dow_rows)
        print("\n  -- Day of Week Summary Table --")
        print(dow_df.to_string(index=False))
    
    # -- Save Trade Log --
    results_dir = r"D:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Full trade log
    log_path = os.path.join(results_dir, "strategy_0923_0929_short_trades.csv")
    actual_trades = trades[trades['type'].isin([1, 2, 3, 6])].copy()
    actual_trades['cum_pnl'] = actual_trades['pnl'].cumsum()
    actual_trades['cum_r'] = actual_trades['r_mult'].cumsum()
    save_cols = ['date', 'type_label', 'entry', 'sl', 'tp', 'exit_px',
                 'pnl', 'r_mult', 'range', 'entry_time', 'exit_time', 'cum_pnl', 'cum_r']
    actual_trades[save_cols].to_csv(log_path, index=False, float_format='%.4f')
    print(f"\n  [OK] Trade log saved -> {log_path}")
    
    # Summary tables
    summary_path = os.path.join(results_dir, "strategy_0923_0929_short_summary.csv")
    all_rows = []
    if overall:
        all_rows.append(stats_to_row(overall))
    all_rows.extend(year_rows)
    all_rows.extend(month_rows)
    all_rows.extend(dow_rows)
    pd.DataFrame(all_rows).to_csv(summary_path, index=False)
    print(f"  [OK] Summary saved  -> {summary_path}")
    
    # All sessions log (including invalidated, no-setup)
    full_log_path = os.path.join(results_dir, "strategy_0923_0929_short_all_sessions.csv")
    trades[['date', 'type_label', 'entry', 'sl', 'tp', 'exit_px',
            'pnl', 'r_mult', 'range', 'entry_time', 'exit_time']].to_csv(
        full_log_path, index=False, float_format='%.2f')
    print(f"  [OK] Full session log -> {full_log_path}")
    
    print("\n  Done.\n")


if __name__ == "__main__":
    main()
