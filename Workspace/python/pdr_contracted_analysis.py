"""
PDR Contracted Level Analysis
==============================
Same analysis as pdr_analysis.html, but with modified reference levels:
  - New "PDH" = actual PDH - 0.20 * actual PDR   (20% below the high)
  - New "PDL" = actual PDL + 0.20 * actual PDR   (20% above the low)
  - New PDR   = New PDH - New PDL                (= 0.60 * actual PDR)

All extensions and probabilities are computed relative to these new contracted levels.
Outputs:
  1. A side-by-side comparison of break probabilities (original vs contracted)
  2. Full extension percentile tables by break type + day + direction
  3. A ready-to-use JSON blob matching pdr_analysis.html data format

Uses RTH 1-minute parquet data.
"""

import pandas as pd
import numpy as np
from numba import njit
import json
import time
import os

NQ_PATH = r"d:\Antigravity\Historical data\NQ Futures Datasets\RTH Data\parquet\NQ_1m_RTH_data.parquet"
ES_PATH = r"d:\Antigravity\Historical data\ES Futures Datasets\RTH Data\parquet\ES_1m_RTH_data.parquet"

OFFSET = 0.20  # 20% inside the range => contracted levels


# ============================================================================
# NUMBA CORE  — runs in one pass over all sessions
# ============================================================================

@njit
def compute_all(
    session_starts, session_ends, session_weekdays,
    nq_h, nq_l, es_h, es_l,
    offset_frac,
    # output arrays (pre-allocated)
    out_nq_ext,   # extension R from contracted PDH/L
    out_nq_type,  # 1=single, 2=double
    out_nq_dir,   # 1=up (contracted PDH broken first), -1=down
    out_nq_wd,    # weekday 0=Mon..4=Fri
    out_es_ext,
    out_es_type,
    out_es_dir,
    out_es_wd,
):
    N = len(session_starts)

    # Probability counters [weekday 0-4] + [5 = all-days combined]
    # cols: 0=valid, 1=nq_db, 2=nq_sb, 3=nq_nb, 4=es_db, 5=es_sb, 6=es_nb
    prob = np.zeros((6, 7), dtype=np.int32)

    nq_cnt = 0
    es_cnt = 0

    for curr in range(1, N):
        prev = curr - 1
        ps = session_starts[prev]; pe = session_ends[prev]
        cs = session_starts[curr]; ce = session_ends[curr]

        if ps > pe or cs > ce:
            continue

        wd = session_weekdays[curr]
        if wd < 0 or wd > 4:
            continue

        # ------- Previous day actual H/L -------
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

        # ------- Contracted reference levels -------
        nq_ref_h = p_nq_h - offset_frac * nq_pdr   # "new PDH"
        nq_ref_l = p_nq_l + offset_frac * nq_pdr   # "new PDL"
        nq_ref_r = nq_ref_h - nq_ref_l              # new PDR = 0.60 * original

        es_ref_h = p_es_h - offset_frac * es_pdr
        es_ref_l = p_es_l + offset_frac * es_pdr
        es_ref_r = es_ref_h - es_ref_l

        # ------- Scan current day -------
        nq_broken_h = False; nq_broken_l = False
        es_broken_h = False; es_broken_l = False
        nq_first_dir = 0; es_first_dir = 0
        nq_max_up = -1e10; nq_min_dn = 1e10
        es_max_up = -1e10; es_min_dn = 1e10
        nq_is_double = False; es_is_double = False

        for i in range(cs, ce + 1):
            # NQ
            if not nq_broken_h and nq_h[i] > nq_ref_h:
                nq_broken_h = True
                if nq_first_dir == 0: nq_first_dir = 1
                else: nq_is_double = True
            if not nq_broken_l and nq_l[i] < nq_ref_l:
                nq_broken_l = True
                if nq_first_dir == 0: nq_first_dir = -1
                else: nq_is_double = True

            if nq_broken_h and nq_h[i] > nq_max_up: nq_max_up = nq_h[i]
            if nq_broken_l and nq_l[i] < nq_min_dn: nq_min_dn = nq_l[i]

            # ES
            if not es_broken_h and es_h[i] > es_ref_h:
                es_broken_h = True
                if es_first_dir == 0: es_first_dir = 1
                else: es_is_double = True
            if not es_broken_l and es_l[i] < es_ref_l:
                es_broken_l = True
                if es_first_dir == 0: es_first_dir = -1
                else: es_is_double = True

            if es_broken_h and es_h[i] > es_max_up: es_max_up = es_h[i]
            if es_broken_l and es_l[i] < es_min_dn: es_min_dn = es_l[i]

        # ------- Probability accounting -------
        prob[wd, 0] += 1
        prob[5,  0] += 1   # combined

        if nq_broken_h and nq_broken_l:
            prob[wd, 1] += 1; prob[5, 1] += 1
        elif nq_broken_h or nq_broken_l:
            prob[wd, 2] += 1; prob[5, 2] += 1
        else:
            prob[wd, 3] += 1; prob[5, 3] += 1

        if es_broken_h and es_broken_l:
            prob[wd, 4] += 1; prob[5, 4] += 1
        elif es_broken_h or es_broken_l:
            prob[wd, 5] += 1; prob[5, 5] += 1
        else:
            prob[wd, 6] += 1; prob[5, 6] += 1

        # ------- Extension accounting -------
        if nq_first_dir != 0 and nq_ref_r > 0:
            if nq_first_dir == 1:
                ext_r = (nq_max_up - nq_ref_h) / nq_ref_r
            else:
                ext_r = (nq_ref_l - nq_min_dn) / nq_ref_r

            btype = 2 if nq_is_double else 1
            out_nq_ext[nq_cnt] = ext_r
            out_nq_type[nq_cnt] = btype
            out_nq_dir[nq_cnt] = nq_first_dir
            out_nq_wd[nq_cnt] = wd
            nq_cnt += 1

        if es_first_dir != 0 and es_ref_r > 0:
            if es_first_dir == 1:
                ext_r = (es_max_up - es_ref_h) / es_ref_r
            else:
                ext_r = (es_ref_l - es_min_dn) / es_ref_r

            btype = 2 if es_is_double else 1
            out_es_ext[es_cnt] = ext_r
            out_es_type[es_cnt] = btype
            out_es_dir[es_cnt] = es_first_dir
            out_es_wd[es_cnt] = wd
            es_cnt += 1

    return prob, nq_cnt, es_cnt


# ============================================================================
# HELPERS
# ============================================================================

PCTS_CDF    = list(range(95, -5, -5))    # [95,90,85,...,5,0]  — for CDF curve
PCTS_TABLE  = [10, 25, 50, 75, 90]       # for percentile table

WD_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'All']
WD_IDX   = [0, 1, 2, 3, 4, -1]  # -1 = all days


def calc_cdf_vals(arr, pcts=PCTS_CDF):
    """Return list of values corresponding to survival function P(X>=val)=pct%."""
    if len(arr) == 0:
        return [0.0] * len(pcts)
    return [round(float(np.percentile(arr, 100 - p)), 2) for p in pcts]


def calc_table_vals(arr):
    if len(arr) == 0:
        return {"p10": 0, "p25": 0, "p50": 0, "p75": 0, "p90": 0, "max": 0}
    return {
        "p10": round(float(np.percentile(arr, 10)), 2),
        "p25": round(float(np.percentile(arr, 25)), 2),
        "p50": round(float(np.percentile(arr, 50)), 2),
        "p75": round(float(np.percentile(arr, 75)), 2),
        "p90": round(float(np.percentile(arr, 90)), 2),
        "max": round(float(arr.max()), 2),
    }


def build_ext_block(ext, types, dirs, wds):
    """
    Build the extension JSON matching pdr_analysis.html structure:
      break_type -> day -> direction -> {probs, vals, table_vals}
    """
    break_types = {
        "all_breaks":    None,        # type 1 or 2
        "single_break":  np.array([1]),
        "double_break":  np.array([2]),
    }
    directions = {
        "Up":       1,
        "Down":    -1,
        "Combined": 0,   # 0 = ignore direction
    }
    days = {
        "All":       None,    # None = all weekdays
        "Monday":    0,
        "Tuesday":   1,
        "Wednesday": 2,
        "Thursday":  3,
        "Friday":    4,
    }

    result = {}
    for bt_name, bt_vals in break_types.items():
        result[bt_name] = {}
        for day_name, day_val in days.items():
            result[bt_name][day_name] = {}
            for dir_name, dir_val in directions.items():
                # Build mask
                mask = np.ones(len(ext), dtype=bool)
                if bt_vals is not None:
                    mask &= np.isin(types, bt_vals)
                if day_val is not None:
                    mask &= (wds == day_val)
                if dir_val != 0:
                    mask &= (dirs == dir_val)

                arr = ext[mask]
                result[bt_name][day_name][dir_name] = {
                    "probs":      PCTS_CDF,
                    "vals":       calc_cdf_vals(arr),
                    "table_vals": calc_table_vals(arr) if len(arr) > 0 else {},
                }
    return result


def build_prob_block(prob_row):
    """prob_row: [valid, nq_db, nq_sb, nq_nb, es_db, es_sb, es_nb]"""
    v = int(prob_row[0])
    if v == 0:
        return {"nq": {}, "es": {}}
    nq_db = int(prob_row[1]); nq_sb = int(prob_row[2]); nq_nb = int(prob_row[3])
    es_db = int(prob_row[4]); es_sb = int(prob_row[5]); es_nb = int(prob_row[6])
    return {
        "nq": {
            "atleast_one": round((nq_db + nq_sb) / v * 100, 2),
            "single":      round(nq_sb / v * 100, 2),
            "double":      round(nq_db / v * 100, 2),
            "inside":      round(nq_nb / v * 100, 2),
        },
        "es": {
            "atleast_one": round((es_db + es_sb) / v * 100, 2),
            "single":      round(es_sb / v * 100, 2),
            "double":      round(es_db / v * 100, 2),
            "inside":      round(es_nb / v * 100, 2),
        },
    }


def build_sessions(df):
    sess_dates = df['SessionDate'].values
    unique_sessions, inv = np.unique(sess_dates, return_inverse=True)
    N = len(unique_sessions)
    sess_starts = np.zeros(N, dtype=np.int32)
    sess_ends   = np.zeros(N, dtype=np.int32)
    curr = inv[0]; sess_starts[curr] = 0
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
        raise ValueError(f"No datetime cols in {sym}: {df.columns.tolist()}")
    df = df.sort_values('Datetime').reset_index(drop=True)
    mask = ((df['Datetime'].dt.hour > 9) |
            ((df['Datetime'].dt.hour == 9) & (df['Datetime'].dt.minute >= 30))) & \
           (df['Datetime'].dt.hour < 16)
    df = df[mask].copy()
    df['SessionDate'] = df['Datetime'].dt.date
    return df[['Datetime', 'SessionDate', 'High', 'Low']].rename(
        columns={'High': f'{sym}_H', 'Low': f'{sym}_L'})


def print_comparison_table(label, orig, cont):
    """Print side-by-side break probability comparison."""
    print(f"\n  {label}")
    print(f"  {'Metric':<20} {'Original':>12} {'Contracted':>12} {'Delta':>10}")
    print(f"  {'-'*56}")
    keys = [("atleast_one", "Atleast One Break"),
            ("single",      "Single Break"),
            ("double",      "Double Break"),
            ("inside",      "Inside (No Break)")]
    for k, name in keys:
        o = orig.get(k, 0)
        c = cont.get(k, 0)
        d = c - o
        print(f"  {name:<20} {o:>11.2f}%  {c:>11.2f}%  {d:>+9.2f}%")


def print_ext_comparison(asset, break_type, day, direction,
                         orig_block, cont_block):
    try:
        o = orig_block[break_type][day][direction]
        c = cont_block[break_type][day][direction]
    except KeyError:
        return

    ot = o["table_vals"]; ct = c["table_vals"]
    if not ot or not ct:
        return

    pcts = ["p10", "p25", "p50", "p75", "p90", "max"]
    print(f"\n  {asset} | {break_type} | {day} | {direction}")
    print(f"  {'Pct':<8}", end="")
    for p in pcts:
        print(f"  {p:>8}", end="")
    print()
    print(f"  {'Orig':<8}", end="")
    for p in pcts:
        print(f"  {ot.get(p,0):>7.3f}R", end="")
    print()
    print(f"  {'Cont':<8}", end="")
    for p in pcts:
        print(f"  {ct.get(p,0):>7.3f}R", end="")
    print()
    print(f"  {'Delta':<8}", end="")
    for p in pcts:
        d = ct.get(p, 0) - ot.get(p, 0)
        print(f"  {d:>+7.3f}R", end="")
    print()


# ============================================================================
# ORIGINAL DATA from pdr_analysis.html (for comparison)
# ============================================================================
ORIGINAL_PROB = {
    "nq": {"atleast_one": 87.76, "single": 75.12, "double": 12.64, "inside": 12.24},
    "es": {"atleast_one": 87.53, "single": 75.52, "double": 12.01, "inside": 12.47},
}


# ============================================================================
# MAIN
# ============================================================================

def main():
    t0 = time.time()
    SEP = "=" * 70
    print(SEP)
    print(f"  PDR CONTRACTED LEVEL ANALYSIS  |  Offset = {OFFSET:.0%}")
    print(f"  New PDH = actual PDH - {OFFSET:.0%}*PDR")
    print(f"  New PDL = actual PDL + {OFFSET:.0%}*PDR")
    print(f"  New PDR = {1 - 2*OFFSET:.0%} of original PDR")
    print(SEP)

    # --- Load ---
    print("\nLoading NQ 1m RTH...")
    nq = pd.read_parquet(NQ_PATH)
    print(f"  {len(nq):,} rows")
    print("Loading ES 1m RTH...")
    es = pd.read_parquet(ES_PATH)
    print(f"  {len(es):,} rows")

    nq = normalise(nq, 'NQ')
    es = normalise(es, 'ES')
    df = pd.merge(nq, es, on=['Datetime', 'SessionDate'], how='inner')
    df = df.sort_values('Datetime').reset_index(drop=True)
    n_sess = df['SessionDate'].nunique()
    print(f"\nMerged: {len(df):,} rows | {n_sess} sessions")

    sess_starts, sess_ends, weekdays = build_sessions(df)

    nq_h_arr = df['NQ_H'].values.astype(np.float32)
    nq_l_arr = df['NQ_L'].values.astype(np.float32)
    es_h_arr = df['ES_H'].values.astype(np.float32)
    es_l_arr = df['ES_L'].values.astype(np.float32)

    MAX = n_sess * 2
    nq_ext = np.zeros(MAX, np.float32); nq_type = np.zeros(MAX, np.int32)
    nq_dir = np.zeros(MAX, np.int32);  nq_wd   = np.zeros(MAX, np.int32)
    es_ext = np.zeros(MAX, np.float32); es_type = np.zeros(MAX, np.int32)
    es_dir = np.zeros(MAX, np.int32);  es_wd   = np.zeros(MAX, np.int32)

    print("\nRunning Numba computation (JIT on first call)...")
    t1 = time.time()
    prob, nq_cnt, es_cnt = compute_all(
        sess_starts, sess_ends, weekdays,
        nq_h_arr, nq_l_arr, es_h_arr, es_l_arr,
        np.float32(OFFSET),
        nq_ext, nq_type, nq_dir, nq_wd,
        es_ext, es_type, es_dir, es_wd,
    )
    print(f"  Done in {time.time()-t1:.2f}s")

    # Trim arrays
    nq_ext = nq_ext[:nq_cnt]; nq_type = nq_type[:nq_cnt]
    nq_dir = nq_dir[:nq_cnt]; nq_wd   = nq_wd[:nq_cnt]
    es_ext = es_ext[:es_cnt]; es_type = es_type[:es_cnt]
    es_dir = es_dir[:es_cnt]; es_wd   = es_wd[:es_cnt]

    # ----------------------------------------------------------------
    # BREAK PROBABILITIES
    # ----------------------------------------------------------------
    prob_all = build_prob_block(prob[5])   # combined all days

    print(f"\n{SEP}")
    print("BREAK PROBABILITIES  (Original pdr_analysis.html vs Contracted)")
    print(SEP)
    print_comparison_table("NQ", ORIGINAL_PROB["nq"], prob_all["nq"])
    print_comparison_table("ES", ORIGINAL_PROB["es"], prob_all["es"])

    # ----------------------------------------------------------------
    # EXTENSION BLOCKS
    # ----------------------------------------------------------------
    nq_ext_block = build_ext_block(nq_ext, nq_type, nq_dir, nq_wd)
    es_ext_block = build_ext_block(es_ext, es_type, es_dir, es_wd)

    print(f"\n{SEP}")
    print("EXTENSION R-MULTIPLES  —  All Days Combined")
    print(SEP)
    print("(Extension is measured in units of the CONTRACTED PDR = 60% of original)")

    for asset, block in [("NQ", nq_ext_block), ("ES", es_ext_block)]:
        for bt in ["all_breaks", "single_break", "double_break"]:
            for d in ["Up", "Down", "Combined"]:
                print_ext_comparison(asset, bt, "All", d, block, block)
                # (comparing to itself here since orig block not reloaded — see JSON output)

    # ----------------------------------------------------------------
    # BUILD FINAL JSON  (same structure as pdr_analysis.html _D.pdr)
    # ----------------------------------------------------------------
    out_data = {
        "pdr_contracted": {
            "note": f"PDH/PDL contracted by {OFFSET:.0%} each side. New PDR = {1-2*OFFSET:.0%} of original.",
            "offset": OFFSET,
            "prob": prob_all,
            "ext": {
                "nq": nq_ext_block,
                "es": es_ext_block,
            }
        }
    }

    results_dir = r"d:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    json_path = os.path.join(results_dir, "pdr_contracted_20pct.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, separators=(',', ':'))
    print(f"\n{SEP}")
    print(f"JSON saved to: {json_path}")

    # ----------------------------------------------------------------
    # PRINT FULL SUMMARY TABLE
    # ----------------------------------------------------------------
    print(f"\n{SEP}")
    print("EXTENSION PERCENTILE SUMMARY  |  All Breaks | All Days | Combined Direction")
    print(f"{'Asset':<6} {'Type':<16} {'P10':>8} {'P25':>8} {'P50':>8} {'P75':>8} {'P90':>8} {'Max':>10}")
    print("-" * 70)
    for asset, block in [("NQ", nq_ext_block), ("ES", es_ext_block)]:
        for bt in ["all_breaks", "single_break", "double_break"]:
            tv = block[bt]["All"]["Combined"]["table_vals"]
            if tv:
                print(f"{asset:<6} {bt:<16} {tv['p10']:>7.3f}R  {tv['p25']:>7.3f}R  "
                      f"{tv['p50']:>7.3f}R  {tv['p75']:>7.3f}R  {tv['p90']:>7.3f}R  {tv['max']:>8.3f}R")

    print(f"\n{SEP}")
    print("ORIGINAL EXTENSION (from pdr_analysis.html) for reference:")
    print("NQ all_breaks All Combined: P10=0.08R  P25=0.18R  P50=0.40R  P75=0.77R  P90=1.28R")
    print("ES all_breaks All Combined: P10=0.08R  P25=0.18R  P50=0.39R  P75=0.76R  P90=1.27R")
    print("(Extensions above are in original PDR units)")
    print("(Contracted extensions below are in contracted PDR = 60% of original)")

    print(f"\n  Total time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
