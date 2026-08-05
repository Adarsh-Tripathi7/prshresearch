"""
PDR Early Entry Test
====================
Hypothesis: Instead of entering at PDH/PDL, enter 20% inside the range.
  - PDH entry: price = PDH - 0.20 * PDR  (20% below PDH)
  - PDL entry: price = PDL + 0.20 * PDR  (20% above PDL)

For each day where PDH or PDL is broken:
  - Record the max extension from PDH (or PDL) in R-multiples (original baseline)
  - Record the max extension from the early entry point in R-multiples (adjusted)

Outputs percentile distributions + comparison summary.

Uses RTH 1-minute parquet data for NQ and ES.
"""

import pandas as pd
import numpy as np
from numba import njit
import time

NQ_PATH = r"d:\Antigravity\Historical data\NQ Futures Datasets\RTH Data\parquet\NQ_1m_RTH_data.parquet"
ES_PATH = r"d:\Antigravity\Historical data\ES Futures Datasets\RTH Data\parquet\ES_1m_RTH_data.parquet"

ENTRY_OFFSET = 0.20  # 20% inside the range

# ---------------------------------------------------------------------------
# Numba core
# ---------------------------------------------------------------------------

@njit
def run_test(
    session_starts, session_ends, session_weekdays,
    nq_h, nq_l, es_h, es_l,
    offset_frac
):
    N = len(session_starts)
    MAX_RES = N

    nq_up_base = np.full(MAX_RES, -1.0, dtype=np.float32)
    nq_up_adj  = np.full(MAX_RES, -1.0, dtype=np.float32)
    nq_dn_base = np.full(MAX_RES, -1.0, dtype=np.float32)
    nq_dn_adj  = np.full(MAX_RES, -1.0, dtype=np.float32)

    es_up_base = np.full(MAX_RES, -1.0, dtype=np.float32)
    es_up_adj  = np.full(MAX_RES, -1.0, dtype=np.float32)
    es_dn_base = np.full(MAX_RES, -1.0, dtype=np.float32)
    es_dn_adj  = np.full(MAX_RES, -1.0, dtype=np.float32)

    for curr in range(1, N):
        prev = curr - 1
        ps = session_starts[prev]; pe = session_ends[prev]
        cs = session_starts[curr]; ce = session_ends[curr]

        if ps > pe or cs > ce:
            continue
        wd = session_weekdays[curr]
        if wd < 0 or wd > 4:
            continue

        # Previous day H/L
        p_nq_h = -1e10; p_nq_l = 1e10
        p_es_h = -1e10; p_es_l = 1e10
        for i in range(ps, pe + 1):
            if nq_h[i] > p_nq_h: p_nq_h = nq_h[i]
            if nq_l[i] < p_nq_l: p_nq_l = nq_l[i]
            if es_h[i] > p_es_h: p_es_h = es_h[i]
            if es_l[i] < p_es_l: p_es_l = es_l[i]

        nq_pdr = p_nq_h - p_nq_l
        es_pdr = p_es_h - p_es_l
        if nq_pdr <= 0.0 or es_pdr <= 0.0:
            continue

        # Early entry levels (20% inside)
        nq_up_entry = p_nq_h - offset_frac * nq_pdr
        nq_dn_entry = p_nq_l + offset_frac * nq_pdr
        es_up_entry = p_es_h - offset_frac * es_pdr
        es_dn_entry = p_es_l + offset_frac * es_pdr

        # Scan current day
        nq_pdh_broken = False; nq_pdl_broken = False
        es_pdh_broken = False; es_pdl_broken = False
        nq_max_up = -1e10; nq_max_dn = 1e10
        es_max_up = -1e10; es_max_dn = 1e10

        for i in range(cs, ce + 1):
            if not nq_pdh_broken and nq_h[i] > p_nq_h:
                nq_pdh_broken = True
            if nq_pdh_broken:
                if nq_h[i] > nq_max_up: nq_max_up = nq_h[i]

            if not nq_pdl_broken and nq_l[i] < p_nq_l:
                nq_pdl_broken = True
            if nq_pdl_broken:
                if nq_l[i] < nq_max_dn: nq_max_dn = nq_l[i]

            if not es_pdh_broken and es_h[i] > p_es_h:
                es_pdh_broken = True
            if es_pdh_broken:
                if es_h[i] > es_max_up: es_max_up = es_h[i]

            if not es_pdl_broken and es_l[i] < p_es_l:
                es_pdl_broken = True
            if es_pdl_broken:
                if es_l[i] < es_max_dn: es_max_dn = es_l[i]

        # Store results (only when break actually occurred)
        if nq_pdh_broken:
            nq_up_base[curr] = (nq_max_up - p_nq_h) / nq_pdr
            nq_up_adj[curr]  = (nq_max_up - nq_up_entry) / nq_pdr

        if nq_pdl_broken:
            nq_dn_base[curr] = (p_nq_l - nq_max_dn) / nq_pdr
            nq_dn_adj[curr]  = (nq_dn_entry - nq_max_dn) / nq_pdr

        if es_pdh_broken:
            es_up_base[curr] = (es_max_up - p_es_h) / es_pdr
            es_up_adj[curr]  = (es_max_up - es_up_entry) / es_pdr

        if es_pdl_broken:
            es_dn_base[curr] = (p_es_l - es_max_dn) / es_pdr
            es_dn_adj[curr]  = (es_dn_entry - es_max_dn) / es_pdr

    return (nq_up_base, nq_up_adj, nq_dn_base, nq_dn_adj,
            es_up_base, es_up_adj, es_dn_base, es_dn_adj)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PCTS = [10, 25, 50, 75, 90]


def get_percentiles(arr_raw):
    arr = arr_raw[arr_raw >= 0]
    if len(arr) == 0:
        return None, None, None, None
    vals = np.percentile(arr, PCTS)
    return vals, arr.mean(), arr.max(), len(arr)


def print_section(label, base_arr, adj_arr):
    b_vals, b_mean, b_max, b_n = get_percentiles(base_arr)
    a_vals, a_mean, a_max, a_n = get_percentiles(adj_arr)
    if b_vals is None:
        print(f"  {label}: No data")
        return

    col_w = 10
    header = f"{'Metric':<22}" + "".join(f"P{p:>3}{'':>4}" for p in PCTS) + f"{'Avg':>{col_w}}  {'Max':>{col_w}}  {'N':>{col_w}}"
    print(f"\n  {label}")
    print("  " + "-" * 80)
    print("  " + header)

    def fmt_row(name, vals, mean, mx, n):
        row = f"  {name:<22}"
        row += "".join(f"{v:>9.3f}R" for v in vals)
        row += f"  {mean:>8.3f}R  {mx:>8.3f}R  {n:>8,}"
        return row

    print(fmt_row("Baseline (from PDH/L):", b_vals, b_mean, b_max, b_n))
    print(fmt_row("Early Entry (-20% R):",  a_vals, a_mean, a_max, a_n))

    # Delta row
    delta = a_vals - b_vals
    row = f"  {'Delta (Adj - Base):':<22}"
    row += "".join(f"{d:>+9.3f}R" for d in delta)
    d_mean = a_mean - b_mean
    row += f"  {d_mean:>+8.3f}R"
    print(row)
    print(f"  {'Expected delta:':<22}" + "".join(f"{ENTRY_OFFSET:>9.3f}R" for _ in PCTS))


def build_sessions(df):
    sess_dates = df['SessionDate'].values
    unique_sessions, inv = np.unique(sess_dates, return_inverse=True)
    N = len(unique_sessions)
    sess_starts = np.zeros(N, dtype=np.int32)
    sess_ends   = np.zeros(N, dtype=np.int32)

    curr = inv[0]
    sess_starts[curr] = 0
    for i in range(1, len(inv)):
        if inv[i] != curr:
            sess_ends[curr] = i - 1
            curr = inv[i]
            sess_starts[curr] = i
    sess_ends[curr] = len(inv) - 1

    sess_df = pd.DataFrame({'SessionDate': pd.to_datetime(unique_sessions)})
    weekdays = sess_df['SessionDate'].dt.weekday.values.astype(np.int32)
    return sess_starts, sess_ends, weekdays


def normalise(df, sym):
    df.columns = [c.strip() for c in df.columns]
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
    elif 'Date' in df.columns and 'Time' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    else:
        raise ValueError(f"Cannot find datetime columns in {sym}: {df.columns.tolist()}")

    df = df.sort_values('Datetime').reset_index(drop=True)
    # RTH session: 09:30 – 16:00
    mask = (df['Datetime'].dt.hour > 9) | \
           ((df['Datetime'].dt.hour == 9) & (df['Datetime'].dt.minute >= 30))
    mask &= df['Datetime'].dt.hour < 16
    df = df[mask].copy()
    df['SessionDate'] = df['Datetime'].dt.date
    return df[['Datetime', 'SessionDate', 'High', 'Low']].rename(
        columns={'High': f'{sym}_H', 'Low': f'{sym}_L'})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t0 = time.time()
    print("=" * 70)
    print(f"  PDR EARLY ENTRY TEST  |  Offset = {ENTRY_OFFSET:.0%} inside the range")
    print(f"  PDH entry = PDH - {ENTRY_OFFSET:.0%}*PDR   |   PDL entry = PDL + {ENTRY_OFFSET:.0%}*PDR")
    print("=" * 70)

    print("\nLoading NQ 1m RTH parquet...")
    nq = pd.read_parquet(NQ_PATH)
    print(f"  {len(nq):,} rows | columns: {list(nq.columns)}")

    print("Loading ES 1m RTH parquet...")
    es = pd.read_parquet(ES_PATH)
    print(f"  {len(es):,} rows | columns: {list(es.columns)}")

    nq = normalise(nq, 'NQ')
    es = normalise(es, 'ES')

    df = pd.merge(nq, es, on=['Datetime', 'SessionDate'], how='inner')
    df = df.sort_values('Datetime').reset_index(drop=True)
    n_sess = df['SessionDate'].nunique()
    print(f"\nMerged: {len(df):,} rows | {n_sess} trading sessions")

    sess_starts, sess_ends, weekdays = build_sessions(df)

    nq_h = df['NQ_H'].values.astype(np.float32)
    nq_l = df['NQ_L'].values.astype(np.float32)
    es_h = df['ES_H'].values.astype(np.float32)
    es_l = df['ES_L'].values.astype(np.float32)

    print("\nRunning Numba computation (JIT compiles on first call)...")
    t1 = time.time()
    results = run_test(sess_starts, sess_ends, weekdays,
                       nq_h, nq_l, es_h, es_l,
                       np.float32(ENTRY_OFFSET))
    nq_ub, nq_ua, nq_db, nq_da, es_ub, es_ua, es_db, es_da = results
    print(f"  Completed in {time.time()-t1:.2f}s")

    # -----------------------------------------------------------------------
    # Print results
    # -----------------------------------------------------------------------
    SEP = "=" * 70

    print(f"\n{SEP}")
    print("NQ  |  UPSIDE — broke above PDH")
    print_section("All upside breaks:", nq_ub, nq_ua)

    print(f"\n{SEP}")
    print("NQ  |  DOWNSIDE — broke below PDL")
    print_section("All downside breaks:", nq_db, nq_da)

    print(f"\n{SEP}")
    print("ES  |  UPSIDE — broke above PDH")
    print_section("All upside breaks:", es_ub, es_ua)

    print(f"\n{SEP}")
    print("ES  |  DOWNSIDE — broke below PDL")
    print_section("All downside breaks:", es_db, es_da)

    # -----------------------------------------------------------------------
    # Combined stats
    # -----------------------------------------------------------------------
    print(f"\n{SEP}")
    print("COMBINED (NQ + ES, both directions)")
    comb_base = np.concatenate([
        nq_ub[nq_ub >= 0], nq_db[nq_db >= 0],
        es_ub[es_ub >= 0], es_db[es_db >= 0]
    ])
    comb_adj = np.concatenate([
        nq_ua[nq_ua >= 0], nq_da[nq_da >= 0],
        es_ua[es_ua >= 0], es_da[es_da >= 0]
    ])
    print_section("All breaks combined:", comb_base, comb_adj)

    # -----------------------------------------------------------------------
    # Risk note
    # -----------------------------------------------------------------------
    print(f"\n{SEP}")
    print("NOTES")
    print("-" * 70)
    print(f"  - Results only include sessions where PDH/PDL WAS eventually broken.")
    print(f"  - Break probabilities: NQ ~87.8%  ES ~87.5% (from dashboard data).")
    print(f"  - If entering early and PDH/PDL is NOT broken, the trade fails.")
    print(f"  - Delta should be ~+{ENTRY_OFFSET:.2f}R at every percentile.")
    print(f"    Any deviation from +{ENTRY_OFFSET:.2f}R reveals path dependency.")
    print(f"    (e.g. if P50 delta < 0.20 => price often reverses before extending)")
    print(f"  - Stop placement for early entry: consider placing stop at PDL/PDH")
    print(f"    (opposing side), risk = 1.00 + {ENTRY_OFFSET:.2f} = 1.{int(ENTRY_OFFSET*100):02d}R")

    print(f"\n{'='*70}")
    print(f"  Total time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
