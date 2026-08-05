"""
Strategy Comparison: 9:23-9:29 Range Breakdown SHORT
=====================================================
4 Scenarios:
  A) Invalidate if H first + NO costs     (original)
  B) Invalidate if H first + WITH costs
  C) No invalidation       + NO costs      (user request)
  D) No invalidation       + WITH costs

Costs (NQ Futures, 1 contract):
  Slippage: 1 tick entry + 1 tick exit = 0.50 pts ($10)
  Commission: ~$4.50 RT = 0.225 pts equivalent
  Total friction: 0.725 pts per trade
"""

import pandas as pd
import numpy as np
from numba import njit
import time
import os


@njit
def backtest_core(dates_int, times_min, highs, lows, closes,
                  day_starts, day_ends, n_days,
                  w_start=1140, w_end=1199, target_r=0.25,
                  invalidate_on_low=True, friction_pts=0.0):
    """
    Core backtest with configurable invalidation and friction.
    friction_pts: total round-trip cost in points (slippage + commission)
    """
    trade_date     = np.empty(n_days, dtype=np.int64)
    trade_pnl      = np.empty(n_days, dtype=np.float64)
    trade_r_mult   = np.empty(n_days, dtype=np.float64)
    trade_entry    = np.empty(n_days, dtype=np.float64)
    trade_sl       = np.empty(n_days, dtype=np.float64)
    trade_tp       = np.empty(n_days, dtype=np.float64)
    trade_exit_px  = np.empty(n_days, dtype=np.float64)
    trade_type     = np.empty(n_days, dtype=np.int32)
    trade_range    = np.empty(n_days, dtype=np.float64)
    trade_entry_time = np.empty(n_days, dtype=np.int32)
    trade_exit_time  = np.empty(n_days, dtype=np.int32)
    
    t_idx = 0
    
    for d in range(n_days):
        si = day_starts[d]
        ei = day_ends[d]
        
        w_high = -1e18
        w_low  =  1e18
        has_range = False
        
        for i in range(si, ei):
            m = times_min[i]
            if m >= w_start and m <= w_end:
                if highs[i] > w_high: w_high = highs[i]
                if lows[i] < w_low:   w_low = lows[i]
                has_range = True
        
        if not has_range or w_high <= w_low:
            trade_date[t_idx] = dates_int[si]
            trade_pnl[t_idx] = 0.0; trade_r_mult[t_idx] = 0.0
            trade_entry[t_idx] = 0.0; trade_sl[t_idx] = 0.0
            trade_tp[t_idx] = 0.0; trade_exit_px[t_idx] = 0.0
            trade_type[t_idx] = 0; trade_range[t_idx] = 0.0
            trade_entry_time[t_idx] = 0; trade_exit_time[t_idx] = 0
            t_idx += 1
            continue
        
        R = w_high - w_low
        entry_px = w_high
        sl_px    = w_low
        tp_px    = entry_px + target_r * R
        
        entered = False
        invalidated = False
        resolved = False
        pnl = 0.0; r_mult = 0.0; exit_px = 0.0
        ttype = 0; entry_min = 0; exit_min = 0
        
        for i in range(si, ei):
            m = times_min[i]
            if m <= w_end:
                continue
            
            h = highs[i]; l = lows[i]
            
            if not entered and not invalidated:
                breaks_low  = l < w_low
                breaks_high = h > w_high
                
                if breaks_low and breaks_high:
                    if invalidate_on_low:
                        ttype = 5; invalidated = True; resolved = True; break
                    else:
                        # No invalidation: still enter short even if both break
                        entered = True; entry_min = m
                        hits_tp = h >= tp_px; hits_sl = l <= sl_px
                        if hits_tp and hits_sl:
                            ttype = 6; pnl = (sl_px - entry_px) - friction_pts
                            r_mult = pnl / R; exit_px = sl_px; exit_min = m
                            resolved = True; break
                        elif hits_tp:
                            ttype = 1; pnl = (tp_px - entry_px) - friction_pts
                            r_mult = pnl / R; exit_px = tp_px; exit_min = m
                            resolved = True; break
                        elif hits_sl:
                            ttype = 2; pnl = (sl_px - entry_px) - friction_pts
                            r_mult = pnl / R; exit_px = sl_px; exit_min = m
                            resolved = True; break
                elif breaks_low and invalidate_on_low:
                    ttype = 4; invalidated = True; resolved = True; break
                elif breaks_high:
                    entered = True; entry_min = m
                    hits_tp = h >= tp_px; hits_sl = l <= sl_px
                    if hits_tp and hits_sl:
                        ttype = 6; pnl = (sl_px - entry_px) - friction_pts
                        r_mult = pnl / R; exit_px = sl_px; exit_min = m
                        resolved = True; break
                    elif hits_tp:
                        ttype = 1; pnl = (tp_px - entry_px) - friction_pts
                        r_mult = pnl / R; exit_px = tp_px; exit_min = m
                        resolved = True; break
                    elif hits_sl:
                        ttype = 2; pnl = (sl_px - entry_px) - friction_pts
                        r_mult = pnl / R; exit_px = sl_px; exit_min = m
                        resolved = True; break
            elif entered:
                hits_tp = h >= tp_px; hits_sl = l <= sl_px
                if hits_tp and hits_sl:
                    ttype = 6; pnl = (sl_px - entry_px) - friction_pts
                    r_mult = pnl / R; exit_px = sl_px; exit_min = m
                    resolved = True; break
                elif hits_tp:
                    ttype = 1; pnl = (tp_px - entry_px) - friction_pts
                    r_mult = pnl / R; exit_px = tp_px; exit_min = m
                    resolved = True; break
                elif hits_sl:
                    ttype = 2; pnl = (sl_px - entry_px) - friction_pts
                    r_mult = pnl / R; exit_px = sl_px; exit_min = m
                    resolved = True; break
        
        if entered and not resolved:
            eod_close = closes[ei - 1]
            pnl = (eod_close - entry_px) - friction_pts
            r_mult = pnl / R; exit_px = eod_close
            ttype = 3; exit_min = times_min[ei - 1]
        
        trade_date[t_idx] = dates_int[si]
        trade_pnl[t_idx] = pnl; trade_r_mult[t_idx] = r_mult
        trade_entry[t_idx] = entry_px if entered else 0.0
        trade_sl[t_idx] = sl_px; trade_tp[t_idx] = tp_px
        trade_exit_px[t_idx] = exit_px; trade_type[t_idx] = ttype
        trade_range[t_idx] = R
        trade_entry_time[t_idx] = entry_min; trade_exit_time[t_idx] = exit_min
        t_idx += 1
    
    return (trade_date[:t_idx], trade_pnl[:t_idx], trade_r_mult[:t_idx],
            trade_entry[:t_idx], trade_sl[:t_idx], trade_tp[:t_idx],
            trade_exit_px[:t_idx], trade_type[:t_idx], trade_range[:t_idx],
            trade_entry_time[:t_idx], trade_exit_time[:t_idx])


def build_trades_df(results):
    (trade_date, trade_pnl, trade_r_mult, trade_entry, trade_sl,
     trade_tp, trade_exit_px, trade_type, trade_range,
     trade_entry_time, trade_exit_time) = results
    
    trades = pd.DataFrame({
        'date_int': trade_date, 'pnl': trade_pnl, 'r_mult': trade_r_mult,
        'entry': trade_entry, 'sl': trade_sl, 'tp': trade_tp,
        'exit_px': trade_exit_px, 'type': trade_type, 'range': trade_range,
        'entry_time': trade_entry_time, 'exit_time': trade_exit_time,
    })
    trades['date'] = pd.to_datetime(trades['date_int'].astype(str), format='%Y%m%d')
    trades['year']  = trades['date'].dt.year
    trades['month'] = trades['date'].dt.month
    trades['dow']   = trades['date'].dt.dayofweek
    trades['dow_name'] = trades['date'].dt.day_name()
    type_map = {0:'No Setup', 1:'TP Hit', 2:'SL Hit', 3:'EOD Close',
                4:'Invalidated', 5:'Entry Clash', 6:'Exit Clash->SL'}
    trades['type_label'] = trades['type'].map(type_map)
    return trades


def compute_stats(trades_df, label="Overall"):
    actual = trades_df[trades_df['type'].isin([1, 2, 3, 6])].copy()
    if len(actual) == 0:
        return None
    
    r = actual['r_mult']
    n = len(actual)
    wins = actual[r > 0]; losses = actual[r <= 0]
    n_w = len(wins); n_l = len(losses)
    
    total_r = r.sum(); avg_r = r.mean()
    std_r = r.std() if n > 1 else 0
    win_rate = n_w / n * 100
    
    gp = wins['r_mult'].sum() if n_w > 0 else 0
    gl = abs(losses['r_mult'].sum()) if n_l > 0 else 0
    pf = gp / gl if gl > 0 else float('inf')
    
    avg_w = wins['r_mult'].mean() if n_w > 0 else 0
    avg_l = losses['r_mult'].mean() if n_l > 0 else 0
    payoff = abs(avg_w / avg_l) if avg_l != 0 else float('inf')
    
    eq = r.cumsum(); dd = (eq - eq.cummax()).min()
    sharpe = (avg_r / std_r * np.sqrt(252)) if std_r > 0 else 0
    
    # Streaks
    s = r.apply(lambda x: 1 if x > 0 else 0).values
    mws = mls = cw = cl = 0
    for v in s:
        if v == 1: cw += 1; cl = 0; mws = max(mws, cw)
        else: cl += 1; cw = 0; mls = max(mls, cl)
    
    return {
        'label': label, 'n': n, 'n_w': n_w, 'n_l': n_l,
        'win_rate': win_rate, 'total_r': total_r, 'avg_r': avg_r,
        'pf': pf, 'payoff': payoff, 'sharpe': sharpe, 'max_dd_r': dd,
        'gp': gp, 'gl': gl, 'avg_w': avg_w, 'avg_l': avg_l,
        'mws': mws, 'mls': mls, 'avg_range': actual['range'].mean(),
        'total_pnl_pts': actual['pnl'].sum(),
        'invalidated': len(trades_df[trades_df['type'] == 4]),
        'entry_clashes': len(trades_df[trades_df['type'] == 5]),
        'no_setup': len(trades_df[trades_df['type'] == 0]),
        'total_sessions': len(trades_df),
        'skew': r.skew() if n > 2 else 0,
        'kurt': r.kurtosis() if n > 3 else 0,
    }


def stats_row(s):
    if not s: return {}
    return {
        'Period': s['label'], 'Trades': s['n'], 'Wins': s['n_w'],
        'Losses': s['n_l'], 'Win%': round(s['win_rate'], 1),
        'TotalR': round(s['total_r'], 2), 'AvgR': round(s['avg_r'], 4),
        'PF': round(s['pf'], 2), 'Payoff': round(s['payoff'], 2),
        'Sharpe': round(s['sharpe'], 2), 'MaxDD_R': round(s['max_dd_r'], 2),
    }


def print_scenario(label, trades):
    s = compute_stats(trades, label)
    if not s: return s
    
    print(f"\n{'=' * 70}")
    print(f"  {s['label']}")
    print(f"  [Same Risk Per Trade | 1R = risk per trade]")
    print(f"{'=' * 70}")
    print(f"  Sessions: {s['total_sessions']:,} | No Setup: {s['no_setup']:,} | "
          f"Invalidated: {s['invalidated']:,} | Entry Clash: {s['entry_clashes']:,}")
    print(f"{'-' * 70}")
    print(f"  Trades: {s['n']:,}  |  Wins: {s['n_w']:,} ({s['win_rate']:.1f}%)  |  "
          f"Losses: {s['n_l']:,} ({100-s['win_rate']:.1f}%)")
    print(f"{'-' * 70}")
    print(f"  Total P&L    : {s['total_r']:>8.2f}R   |  Avg Win (R)  : {s['avg_w']:>+8.4f}R")
    print(f"  Avg P&L      : {s['avg_r']:>8.4f}R   |  Avg Loss (R) : {s['avg_l']:>+8.4f}R")
    print(f"  Profit Factor: {s['pf']:>8.2f}    |  Payoff Ratio : {s['payoff']:>8.2f}")
    print(f"  Sharpe (ann) : {s['sharpe']:>8.2f}    |  Max DD (R)   : {s['max_dd_r']:>8.2f}R")
    print(f"  Gross Profit : {s['gp']:>8.2f}R   |  Gross Loss   : {s['gl']:>8.2f}R")
    print(f"  Win Streak   : {s['mws']:>8}    |  Loss Streak  : {s['mls']:>8}")
    print(f"  Avg Range    : {s['avg_range']:>8.2f}pts |  Ref PnL (pts): {s['total_pnl_pts']:>+8.2f}")
    print(f"  Skewness     : {s['skew']:>8.2f}    |  Kurtosis     : {s['kurt']:>8.2f}")
    print(f"{'=' * 70}")
    return s


def print_breakdown(trades, by='year'):
    rows = []
    if by == 'year':
        for yr in sorted(trades['year'].unique()):
            s = compute_stats(trades[trades['year'] == yr], f"{yr}")
            if s: rows.append(stats_row(s))
    elif by == 'month':
        mnames = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                  7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
        for mo in range(1, 13):
            sub = trades[trades['month'] == mo]
            if len(sub) > 0:
                s = compute_stats(sub, mnames[mo])
                if s: rows.append(stats_row(s))
    elif by == 'dow':
        for d in range(5):
            sub = trades[trades['dow'] == d]
            if len(sub) > 0:
                s = compute_stats(sub, ['Mon','Tue','Wed','Thu','Fri'][d])
                if s: rows.append(stats_row(s))
    
    if rows:
        df = pd.DataFrame(rows)
        print(df.to_string(index=False))
    return rows


def main():
    print("\n" + "=" * 70)
    print("  NQ 19:00-19:59 RANGE BREAKOUT LONG -- TARGET SIZE COMPARISON")
    print("  All scenarios: Invalidate if Low breaks first | WITH COSTS (0.725 pts)")
    print("=" * 70)
    
    # Load data
    nq_path = r"D:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet"
    print("\n  Loading data...")
    df = pd.read_parquet(nq_path)
    hours = df['Time'].str[:2].astype(int)
    minutes = df['Time'].str[3:5].astype(int)
    df['time_min'] = hours * 60 + minutes
    df['session_date'] = df['Date'].dt.date
    df['date_int'] = (df['Date'].dt.year * 10000 + df['Date'].dt.month * 100 + df['Date'].dt.day).astype(np.int64)
    df = df.sort_values(['session_date', 'time_min']).reset_index(drop=True)
    
    day_groups = df.groupby('session_date')
    day_starts = day_groups.apply(lambda x: x.index[0]).values.astype(np.int64)
    day_ends   = day_groups.apply(lambda x: x.index[-1] + 1).values.astype(np.int64)
    n_days = len(day_starts)
    print(f"  {len(df):,} bars | {n_days:,} days | {df['Date'].min().date()} to {df['Date'].max().date()}")
    
    # Common args
    args = dict(
        dates_int=df['date_int'].values,
        times_min=df['time_min'].values.astype(np.int32),
        highs=df['High'].values.astype(np.float64),
        lows=df['Low'].values.astype(np.float64),
        closes=df['Last'].values.astype(np.float64),
        day_starts=day_starts, day_ends=day_ends, n_days=n_days,
        w_start=1140, w_end=1199,
        invalidate_on_low=True, friction_pts=0.0
    )
    
    # ── Scenario A: 0.25R ──
    print("\n  Running Scenario A (0.25R Target)...")
    res_a = backtest_core(**args, target_r=0.25)
    trades_a = build_trades_df(res_a)
    
    # ── Scenario B: 0.50R ──
    print("  Running Scenario B (0.50R Target)...")
    res_b = backtest_core(**args, target_r=0.50)
    trades_b = build_trades_df(res_b)
    
    # ── Scenario C: 0.75R ──
    print("  Running Scenario C (0.75R Target)...")
    res_c = backtest_core(**args, target_r=0.75)
    trades_c = build_trades_df(res_c)
    
    # ── Scenario D: 1.00R ──
    print("  Running Scenario D (1.00R Target)...")
    res_d = backtest_core(**args, target_r=1.00)
    trades_d = build_trades_df(res_d)
    
    # ── Print Overall ──
    sa = print_scenario("A) 0.25R TARGET | WITH COSTS", trades_a)
    sb = print_scenario("B) 0.50R TARGET | WITH COSTS", trades_b)
    sc = print_scenario("C) 0.75R TARGET | WITH COSTS", trades_c)
    sd = print_scenario("D) 1.00R TARGET | WITH COSTS", trades_d)
    
    # ── Comparison Table ──
    print("\n\n" + "=" * 70)
    print("  TARGET COMPARISON (ALL WITH COSTS)")
    print("=" * 70)
    comp = pd.DataFrame([stats_row(s) for s in [sa, sb, sc, sd] if s])
    print(comp.to_string(index=False))
    
    # ── Save ──
    results_dir = r"D:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    
    for tag, trades in [("target_025", trades_a), ("target_050", trades_b),
                         ("target_075", trades_c), ("target_100", trades_d)]:
        actual = trades[trades['type'].isin([1, 2, 3, 6])].copy()
        actual['cum_r'] = actual['r_mult'].cumsum()
        actual['cum_pnl'] = actual['pnl'].cumsum()
        path = os.path.join(results_dir, f"strategy_1900_long_{tag}.csv")
        actual[['date','type_label','entry','sl','tp','exit_px','pnl','r_mult','range','cum_pnl','cum_r']].to_csv(
            path, index=False, float_format='%.4f')
    
    pd.DataFrame([stats_row(s) for s in [sa, sb, sc, sd] if s]).to_csv(
        os.path.join(results_dir, "strategy_1900_target_comparison.csv"), index=False)
    print("\n  Done.\n")


if __name__ == "__main__":
    main()
