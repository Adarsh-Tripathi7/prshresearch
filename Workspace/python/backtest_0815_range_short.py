"""
STRATEGY: 08:15-08:29 NQ Range Short Breakout
==============================================
Rules:
  - Mark the High/Low of the 08:15-08:29 ET window (pre-RTH open range).
  - SHORT ONLY: Enter only if price breaks the RANGE LOW first.
  - If High breaks first (or both break in the same candle) -> invalidated, no trade.
  - Target  : range_low - 0.80 * range_size  (80% extension to the downside)
  - Stop    : range_high  (above range)
  - One trade per session max.
  - EOD exit at 16:00 ET (session_min = 1320) if neither TP nor SL is hit.

Session-min encoding (matching existing codebase):
  hours >= 18  -> (hours - 18) * 60 + minutes
  hours <  18  -> (hours +  6) * 60 + minutes

  08:15 ET -> (8+6)*60+15  = 855
  08:29 ET -> (8+6)*60+29  = 869
  16:00 ET -> (16+6)*60+0  = 1320
"""

import pandas as pd
import numpy as np
from numba import njit
import time
import os

# ─── session_min constants ─────────────────────────────────────────────────────
W_START = (7 + 6) * 60 + 0    # 780  = 07:00 ET
W_END   = (7 + 6) * 60 + 14   # 794  = 07:14 ET
EOD_MIN = (16 + 6) * 60 + 0   # 1320 = 16:00 ET  (RTH close)

# Target multiplier
TGT_MULT = 1.30   # 130% extension

# ── Fixed risk per trade ──────────────────────────────────────────────────────
FIXED_RISK_USD = 1000.0   # dollars risked per trade
NQ_PT_VALUE    = 20.0     # $20 per full point on NQ

# ── Date filter ───────────────────────────────────────────────────────────────
START_DATE = '2018-01-01'

# ─── numba core ────────────────────────────────────────────────────────────────
@njit
def backtest_core(session_ids, session_mins, highs, lows, closes,
                  w_start, w_end, eod_min, tgt_mult):
    """
    Returns a 2-D float64 array of per-trade records:
      col 0: session index
      col 1: entry price (= range low, short entry)
      col 2: stop price  (= range high)
      col 3: target price
      col 4: exit price
      col 5: pnl in points  (entry - exit, positive = profit for short)
      col 6: outcome flag   1=win / -1=loss / 0=time-exit
    Max trades = num_sessions (one per session).
    """
    n = len(session_ids)
    # Worst case one trade per session
    max_trades = 10000
    records = np.full((max_trades, 7), np.nan)
    trade_count = 0

    # Counters
    total_sessions = 0
    sessions_with_range = 0
    invalidated_count = 0

    idx = 0
    while idx < n:
        current_session = session_ids[idx]

        # Find bounds of this session
        start_idx = idx
        while idx < n and session_ids[idx] == current_session:
            idx += 1
        end_idx = idx  # exclusive

        total_sessions += 1

        # ── 1. Build range (08:15 – 08:29) ─────────────────────────────────
        r_high = -1e18
        r_low  =  1e18
        has_range = False

        for i in range(start_idx, end_idx):
            m = session_mins[i]
            if m >= w_start and m <= w_end:
                if highs[i] > r_high:
                    r_high = highs[i]
                if lows[i]  < r_low:
                    r_low  = lows[i]
                has_range = True
            elif m > w_end:
                break

        if not has_range:
            continue

        sessions_with_range += 1
        r_size   = r_high - r_low
        if r_size <= 0.0:
            continue

        sl_price  = r_high                        # stop above range
        tgt_price = r_low - tgt_mult * r_size     # 80% ext downside
        entry_px  = r_low                         # short at range low break

        # ── 2. Look for breakout after range window ──────────────────────────
        entered     = False
        invalidated = False

        for i in range(start_idx, end_idx):
            m = session_mins[i]
            if m <= w_end:
                continue

            h = highs[i]
            l = lows[i]

            # ── Entry logic ────────────────────────────────────────────────
            if not entered and not invalidated:
                breaks_low  = l < r_low
                breaks_high = h > r_high

                if breaks_high and breaks_low:
                    # Both in same candle – skip (we can't determine which first)
                    invalidated = True
                    invalidated_count += 1
                    break

                elif breaks_high:
                    # High broke first -> invalidate, no short
                    invalidated = True
                    invalidated_count += 1
                    break

                elif breaks_low:
                    # Low broke first -> enter short
                    entered = True
                    # Check intra-bar resolution (conservative: if SL also hit, count as loss)
                    if h >= sl_price and l <= tgt_price:
                        # Both hit same candle -> pessimistic = loss
                        outcome   = -1
                        exit_px   = sl_price
                        pnl_pts   = entry_px - exit_px
                    elif h >= sl_price:
                        outcome   = -1
                        exit_px   = sl_price
                        pnl_pts   = entry_px - exit_px
                    elif l <= tgt_price:
                        outcome   = 1
                        exit_px   = tgt_price
                        pnl_pts   = entry_px - exit_px
                    else:
                        # Still open – continue monitoring
                        outcome   = 0
                        exit_px   = np.nan
                        pnl_pts   = np.nan

                    if outcome != 0:
                        records[trade_count, 0] = current_session
                        records[trade_count, 1] = entry_px
                        records[trade_count, 2] = sl_price
                        records[trade_count, 3] = tgt_price
                        records[trade_count, 4] = exit_px
                        records[trade_count, 5] = pnl_pts
                        records[trade_count, 6] = outcome
                        trade_count += 1
                        break  # done for this session

            # ── Post-entry monitoring ──────────────────────────────────────
            elif entered:
                hits_sl  = h >= sl_price
                hits_tgt = l <= tgt_price

                if hits_sl and hits_tgt:
                    outcome = -1
                    exit_px = sl_price
                elif hits_sl:
                    outcome = -1
                    exit_px = sl_price
                elif hits_tgt:
                    outcome = 1
                    exit_px = tgt_price
                else:
                    # EOD check
                    if m >= eod_min:
                        outcome = 0   # time exit at last close seen
                        exit_px = closes[i]
                    else:
                        continue

                pnl_pts = entry_px - exit_px
                records[trade_count, 0] = current_session
                records[trade_count, 1] = entry_px
                records[trade_count, 2] = sl_price
                records[trade_count, 3] = tgt_price
                records[trade_count, 4] = exit_px
                records[trade_count, 5] = pnl_pts
                records[trade_count, 6] = outcome
                trade_count += 1
                break  # done for this session

    return records[:trade_count], total_sessions, sessions_with_range, invalidated_count


# ─── helpers ───────────────────────────────────────────────────────────────────
def load_and_prep(file_path, asset_name, start_date=None):
    print(f"Loading {asset_name} data from:\n  {file_path}")
    df = pd.read_parquet(file_path)

    hours   = df['Time'].str.slice(0, 2).astype(int)
    minutes = df['Time'].str.slice(3, 5).astype(int)

    session_min = np.where(
        hours >= 18,
        (hours - 18) * 60 + minutes,
        (hours +  6) * 60 + minutes
    )
    df['session_min'] = session_min

    df['dt']           = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df                 = df.sort_values('dt').reset_index(drop=True)
    df['session_date'] = (df['dt'] - pd.Timedelta(hours=17)).dt.date

    # ── Date filter ─────────────────────────────────────────────────────────
    if start_date is not None:
        cutoff = pd.to_datetime(start_date).date()
        df = df[df['session_date'] >= cutoff].reset_index(drop=True)
        print(f"  Filtered to {start_date}+: {len(df):,} rows remaining")

    session_ids        = df.groupby('session_date').ngroup().values
    session_dates_arr  = df['session_date'].values   # for yearly breakdown

    return (
        session_ids.astype(np.int32),
        df['session_min'].values.astype(np.int32),
        df['High'].values.astype(np.float64),
        df['Low'].values.astype(np.float64),
        df['Last'].values.astype(np.float64),
        session_dates_arr,
    )


def calc_stats(records, total_sessions, sessions_with_range, invalidated_count,
               asset_name, fixed_risk_usd=1000.0, nq_pt_value=20.0,
               trade_years=None):
    print(f"\n{'='*65}")
    print(f"  STRATEGY: 07:00-07:14 NQ Range Short  |  Asset: {asset_name}")
    print(f"  Target: 1.3R ext down  |  SL: Above range high  |  From: 2018")
    print(f"  Fixed Risk: ${fixed_risk_usd:,.0f}/trade  |  NQ: ${nq_pt_value}/pt")
    print(f"{'='*65}")

    print(f"\n-- SESSION SUMMARY -----------------------------------------")
    print(f"  Total Sessions          : {total_sessions}")
    print(f"  Sessions w/ Range Data  : {sessions_with_range}")
    print(f"  Setups Invalidated      : {invalidated_count}  (high broke first / ambiguous)")

    n_trades = len(records)
    if n_trades == 0:
        print("  NO TRADES FOUND.")
        return

    pnl_pts   = records[:, 5]
    outcomes  = records[:, 6]

    # ── R-multiples (pnl / range_size) ──────────────────────────────────────
    entry_prices = records[:, 1]
    sl_prices    = records[:, 2]
    range_sizes  = sl_prices - entry_prices   # r_high - r_low
    r_multiples  = pnl_pts / range_sizes      # +0.8 win / -1.0 loss

    # ── Fixed-risk dollar PnL: risk $fixed_risk_usd, size by range ──────────
    # contracts = fixed_risk_usd / (range_size * nq_pt_value)
    # dollar_pnl = pnl_pts * contracts * nq_pt_value = r_multiple * fixed_risk_usd
    dollar_pnl = r_multiples * fixed_risk_usd

    wins       = int(np.sum(outcomes == 1))
    losses     = int(np.sum(outcomes == -1))
    time_exits = int(np.sum(outcomes == 0))

    d_wins   = dollar_pnl[outcomes == 1]
    d_losses = dollar_pnl[outcomes == -1]
    d_te     = dollar_pnl[outcomes == 0]

    gross_profit_d = float(np.sum(d_wins))   if wins       > 0 else 0.0
    gross_loss_d   = float(np.sum(d_losses)) if losses     > 0 else 0.0
    te_pnl_d       = float(np.sum(d_te))     if time_exits > 0 else 0.0
    total_pnl_d    = gross_profit_d + gross_loss_d + te_pnl_d

    win_rate   = wins / n_trades * 100
    avg_win_d  = gross_profit_d / wins   if wins   > 0 else 0.0
    avg_loss_d = gross_loss_d   / losses if losses > 0 else 0.0
    avg_te_d   = te_pnl_d / time_exits   if time_exits > 0 else 0.0
    avg_trade_d = total_pnl_d / n_trades

    pf = gross_profit_d / abs(gross_loss_d) if gross_loss_d != 0 else float('inf')

    # ── Drawdown in dollars ──────────────────────────────────────────────────
    cum_d  = np.cumsum(dollar_pnl)
    peak_d = np.maximum.accumulate(cum_d)
    dd_d   = peak_d - cum_d
    max_dd_d = float(np.max(dd_d)) if len(dd_d) > 0 else 0.0

    # ── Streaks ──────────────────────────────────────────────────────────────
    max_win_streak  = 0
    max_loss_streak = 0
    cur_win  = 0
    cur_loss = 0
    for o in outcomes:
        if o == 1:
            cur_win += 1; cur_loss = 0
            if cur_win > max_win_streak: max_win_streak = cur_win
        elif o == -1:
            cur_loss += 1; cur_win = 0
            if cur_loss > max_loss_streak: max_loss_streak = cur_loss
        else:
            cur_win = 0; cur_loss = 0

    avg_range = float(np.mean(range_sizes))
    avg_r     = float(np.mean(r_multiples))
    total_r   = float(np.sum(r_multiples))

    print(f"\n-- TRADE STATISTICS ----------------------------------------")
    print(f"  Total Trades            : {n_trades}")
    print(f"  Wins                    : {wins}")
    print(f"  Losses                  : {losses}")
    print(f"  Time Exits (EOD)        : {time_exits}")
    print(f"  Win Rate                : {win_rate:.2f}%")
    print(f"\n-- DOLLAR P&L  (Fixed ${fixed_risk_usd:,.0f} risk/trade) ----------")
    print(f"  Total Net PnL           : ${total_pnl_d:+,.2f}")
    print(f"  Gross Profit            : ${gross_profit_d:+,.2f}")
    print(f"  Gross Loss              : ${gross_loss_d:+,.2f}")
    print(f"  Time-Exit PnL           : ${te_pnl_d:+,.2f}")
    print(f"  Avg PnL / Trade         : ${avg_trade_d:+,.2f}")
    print(f"  Avg Win                 : ${avg_win_d:+,.2f}")
    print(f"  Avg Loss                : ${avg_loss_d:+,.2f}")
    print(f"  Avg Time Exit           : ${avg_te_d:+,.2f}")
    print(f"\n-- R-MULTIPLES ---------------------------------------------")
    print(f"  Total Net R             : {total_r:+.2f} R")
    print(f"  Avg R / Trade           : {avg_r:+.4f} R")
    print(f"  Avg Range Size          : {avg_range:.2f} pts")
    print(f"\n-- RISK METRICS --------------------------------------------")
    print(f"  Profit Factor           : {pf:.2f}")
    print(f"  Max Drawdown (dollar)   : ${max_dd_d:,.2f}")
    print(f"  Max Winning Streak      : {max_win_streak}")
    print(f"  Max Losing Streak       : {max_loss_streak}")

    # ── Yearly Breakdown ─────────────────────────────────────────────────────
    if trade_years is not None and len(trade_years) == n_trades:
        print(f"\n-- YEARLY BREAKDOWN (Fixed ${fixed_risk_usd:,.0f} risk/trade) ------")
        print(f"  {'Year':<6} {'Trades':>7} {'Wins':>6} {'Losses':>7} {'WR%':>7} {'Net $':>11} {'PF':>6}")
        print(f"  {'-'*55}")
        unique_years = sorted(set(trade_years))
        for yr in unique_years:
            mask      = trade_years == yr
            yr_d      = dollar_pnl[mask]
            yr_out    = outcomes[mask]
            yr_tr     = int(np.sum(mask))
            yr_w      = int(np.sum(yr_out == 1))
            yr_l      = int(np.sum(yr_out == -1))
            yr_wr     = yr_w / yr_tr * 100 if yr_tr > 0 else 0
            yr_net    = float(np.sum(yr_d))
            yr_gp     = float(np.sum(yr_d[yr_out == 1]))  if yr_w > 0 else 0.0
            yr_gl     = float(np.sum(yr_d[yr_out == -1])) if yr_l > 0 else 0.0
            yr_pf     = yr_gp / abs(yr_gl) if yr_gl != 0 else float('inf')
            pf_str    = f"{yr_pf:.2f}" if yr_pf != float('inf') else "inf"
            print(f"  {yr:<6} {yr_tr:>7} {yr_w:>6} {yr_l:>7} {yr_wr:>6.1f}% {yr_net:>+11,.2f} {pf_str:>6}")
        print(f"  {'-'*55}")
        print(f"  {'TOTAL':<6} {n_trades:>7} {wins:>6} {losses:>7} {win_rate:>6.1f}% {total_pnl_d:>+11,.2f} {pf:.2f}")

    print(f"\n{'='*65}\n")


# ─── main ──────────────────────────────────────────────────────────────────────
def main():
    base_dir = r"d:\Antigravity\Historical data"
    nq_path  = os.path.join(base_dir, "NQ Futures Datasets", "Full Data", "parquet", "NQ_1m_full_data.parquet")

    # ── NQ (filtered from 2018) ──────────────────────────────────────────────
    sess_ids, sess_mins, highs, lows, closes, sess_dates = load_and_prep(
        nq_path, "NQ", start_date=START_DATE
    )

    print("Running backtest (NQ, 2018+)...")
    t0 = time.time()
    records, tot_sess, sess_range, inv_count = backtest_core(
        sess_ids, sess_mins, highs, lows, closes,
        W_START, W_END, EOD_MIN, TGT_MULT
    )
    t1 = time.time()
    print(f"Done in {t1 - t0:.3f}s")

    # ── Map each trade to its calendar year ─────────────────────────────────
    # records[:, 0] = session index within the filtered df
    # Build session_index -> year lookup from sess_dates
    import datetime
    unique_sess_ids = np.unique(sess_ids)
    # For each session id, get the first date entry
    sess_id_to_year = {}
    for sid in unique_sess_ids:
        mask = sess_ids == sid
        d = sess_dates[mask][0]
        if hasattr(d, 'year'):
            sess_id_to_year[int(sid)] = d.year
        else:
            sess_id_to_year[int(sid)] = int(str(d)[:4])

    trade_years = np.array([sess_id_to_year.get(int(r), 0) for r in records[:, 0]])

    calc_stats(records, tot_sess, sess_range, inv_count, "NQ",
               fixed_risk_usd=FIXED_RISK_USD, nq_pt_value=NQ_PT_VALUE,
               trade_years=trade_years)

    # ── Save trade log ───────────────────────────────────────────────────────
    if len(records) > 0:
        entry_prices = records[:, 1]
        sl_prices    = records[:, 2]
        range_sizes  = sl_prices - entry_prices
        r_mults      = records[:, 5] / range_sizes
        dollar_pnl   = r_mults * FIXED_RISK_USD

        df_trades = pd.DataFrame(records, columns=[
            'session_idx', 'entry_price', 'sl_price', 'target_price',
            'exit_price', 'pnl_pts', 'outcome'
        ])
        df_trades['range_size']   = range_sizes
        df_trades['r_multiple']   = r_mults
        df_trades['dollar_pnl']   = dollar_pnl
        df_trades['year']         = trade_years
        df_trades['outcome_label'] = df_trades['outcome'].map(
            {1.0: 'WIN', -1.0: 'LOSS', 0.0: 'TIME_EXIT'}
        )
        out_csv = r"d:\Antigravity\Results\backtest_0700_range_short_NQ_2018_1p3R.csv"
        df_trades.to_csv(out_csv, index=False)
        print(f"Trade log saved -> {out_csv}")


if __name__ == "__main__":
    main()
