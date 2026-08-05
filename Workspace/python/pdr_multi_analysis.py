"""
PDR Multi-Contraction Analysis
================================
Runs the complete pdr_analysis.html research for multiple scenarios:

Contraction levels:  0% (original), 10%, 20%
For each level:
  - Break probabilities (atleast_one, single, double, inside)
  - Extension CDF + percentile tables
  - By weekday (Mon-Fri + All)
  - By break type (all_breaks, single_break, double_break)
  - By direction (Up, Down, Combined)

Open filter:
  For each contraction level, also reports:
    - Days where open is WITHIN original PDR range
    - Days where open is WITHIN the contracted range
    - Days where open is OUTSIDE original PDR range (gap open)
  Then re-runs the analysis filtered to each open scenario.

Outputs:
  - Console summary table
  - d:\\Antigravity\\Results\\pdr_multi_analysis.json  (for new HTML page)
"""

import pandas as pd
import numpy as np
from numba import njit
import json
import time
import os

NQ_PATH = r"d:\Antigravity\Historical data\NQ Futures Datasets\RTH Data\parquet\NQ_1m_RTH_data.parquet"
ES_PATH = r"d:\Antigravity\Historical data\ES Futures Datasets\RTH Data\parquet\ES_1m_RTH_data.parquet"

OFFSETS = [0.00, 0.10, 0.20]   # 0%, 10%, 20% contraction each side

PCTS_CDF   = list(range(95, -5, -5))   # 95,90,...,0  (survival function)
PCTS_TABLE = [10, 25, 50, 75, 90]

# ===========================================================================
# NUMBA CORE
# ===========================================================================

@njit
def compute_session_metrics(
    session_starts, session_ends, session_weekdays,
    nq_h, nq_l, nq_o,
    es_h, es_l, es_o,
    offset_frac,
    # output arrays  (pre-allocated, size = num_sessions)
    out_nq_ext,    out_nq_type,  out_nq_dir,  out_nq_wd,
    out_es_ext,    out_es_type,  out_es_dir,  out_es_wd,
    # open-filter flags (written per session)
    out_open_in_orig,       # bool: nq open AND es open within original PDH/L
    out_open_in_cont,       # bool: open within contracted range
    out_valid,              # bool: session counted (not skipped)
    # prob counters  [6 rows: wd0-4, row5=all] x [7 cols]
    #  cols: 0=valid, 1=nq_db, 2=nq_sb, 3=nq_nb, 4=es_db, 5=es_sb, 6=es_nb
    prob_all,               # all sessions
    prob_open_in_orig,      # filtered: open in original range
    prob_open_in_cont,      # filtered: open in contracted range
    prob_open_out,          # filtered: open OUTSIDE original range
):
    N = len(session_starts)
    nq_cnt = 0
    es_cnt = 0

    for curr in range(1, N):
        prev = curr - 1
        ps = session_starts[prev]; pe = session_ends[prev]
        cs = session_starts[curr]; ce = session_ends[curr]

        out_valid[curr] = False
        out_open_in_orig[curr] = False
        out_open_in_cont[curr] = False

        if ps > pe or cs > ce:
            continue
        wd = session_weekdays[curr]
        if wd < 0 or wd > 4:
            continue

        # --- Previous day actual H/L ---
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

        # --- Contracted reference levels ---
        nq_ref_h = p_nq_h - offset_frac * nq_pdr
        nq_ref_l = p_nq_l + offset_frac * nq_pdr
        nq_ref_r = nq_ref_h - nq_ref_l

        es_ref_h = p_es_h - offset_frac * es_pdr
        es_ref_l = p_es_l + offset_frac * es_pdr
        es_ref_r = es_ref_h - es_ref_l

        if nq_ref_r <= 0.0 or es_ref_r <= 0.0:
            continue

        # --- Current day first bar open ---
        nq_open = nq_o[cs]
        es_open = es_o[cs]

        open_in_orig = (nq_open > p_nq_l and nq_open < p_nq_h and
                        es_open > p_es_l and es_open < p_es_h)
        open_in_cont = (nq_open > nq_ref_l and nq_open < nq_ref_h and
                        es_open > es_ref_l and es_open < es_ref_h)

        out_valid[curr]         = True
        out_open_in_orig[curr]  = open_in_orig
        out_open_in_cont[curr]  = open_in_cont

        # --- Scan current day for breaks ---
        nq_broken_h = False; nq_broken_l = False
        es_broken_h = False; es_broken_l = False
        nq_first_dir = 0; es_first_dir = 0
        nq_max_up = -1e10; nq_min_dn = 1e10
        es_max_up = -1e10; es_min_dn = 1e10
        nq_is_double = False; es_is_double = False

        for i in range(cs, ce + 1):
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

        # --- Categorize ---
        def update_prob(p_arr, wd_idx):
            p_arr[wd_idx, 0] += 1
            p_arr[5,      0] += 1
            if nq_broken_h and nq_broken_l:
                p_arr[wd_idx, 1] += 1; p_arr[5, 1] += 1
            elif nq_broken_h or nq_broken_l:
                p_arr[wd_idx, 2] += 1; p_arr[5, 2] += 1
            else:
                p_arr[wd_idx, 3] += 1; p_arr[5, 3] += 1
            if es_broken_h and es_broken_l:
                p_arr[wd_idx, 4] += 1; p_arr[5, 4] += 1
            elif es_broken_h or es_broken_l:
                p_arr[wd_idx, 5] += 1; p_arr[5, 5] += 1
            else:
                p_arr[wd_idx, 6] += 1; p_arr[5, 6] += 1

        update_prob(prob_all, wd)
        if open_in_orig:
            update_prob(prob_open_in_orig, wd)
        if open_in_cont:
            update_prob(prob_open_in_cont, wd)
        if not open_in_orig:
            update_prob(prob_open_out, wd)

        # --- Extension ---
        def store_ext(ext_arr, type_arr, dir_arr, wd_arr, cnt,
                      first_dir, is_double, max_up, min_dn, ref_h, ref_l, ref_r):
            if first_dir == 0 or ref_r <= 0:
                return cnt
            if first_dir == 1:
                ext_r = (max_up - ref_h) / ref_r
            else:
                ext_r = (ref_l - min_dn) / ref_r
            btype = 2 if is_double else 1
            ext_arr[cnt] = ext_r
            type_arr[cnt] = btype
            dir_arr[cnt] = first_dir
            wd_arr[cnt] = wd
            return cnt + 1

        nq_cnt = store_ext(out_nq_ext, out_nq_type, out_nq_dir, out_nq_wd,
                           nq_cnt, nq_first_dir, nq_is_double,
                           nq_max_up, nq_min_dn, nq_ref_h, nq_ref_l, nq_ref_r)
        es_cnt = store_ext(out_es_ext, out_es_type, out_es_dir, out_es_wd,
                           es_cnt, es_first_dir, es_is_double,
                           es_max_up, es_min_dn, es_ref_h, es_ref_l, es_ref_r)

    return nq_cnt, es_cnt


# ===========================================================================
# ANALYSIS HELPERS
# ===========================================================================

def cdf_vals(arr):
    if len(arr) == 0:
        return [0.0] * len(PCTS_CDF)
    return [round(float(np.percentile(arr, 100 - p)), 2) for p in PCTS_CDF]


def table_vals(arr):
    if len(arr) == 0:
        return {}
    return {
        "p10": round(float(np.percentile(arr, 10)), 2),
        "p25": round(float(np.percentile(arr, 25)), 2),
        "p50": round(float(np.percentile(arr, 50)), 2),
        "p75": round(float(np.percentile(arr, 75)), 2),
        "p90": round(float(np.percentile(arr, 90)), 2),
        "max": round(float(arr.max()), 2),
    }


def build_ext_block(ext, types, dirs, wds):
    """Build full extension block: break_type -> day -> direction -> {probs,vals,table_vals}"""
    WD_MAP = {
        "All": None, "Monday": 0, "Tuesday": 1,
        "Wednesday": 2, "Thursday": 3, "Friday": 4,
    }
    result = {}
    for bt_name, bt_filter in [
        ("all_breaks",    None),
        ("single_break",  np.array([1])),
        ("double_break",  np.array([2])),
    ]:
        result[bt_name] = {}
        for day_name, day_val in WD_MAP.items():
            result[bt_name][day_name] = {}
            for dir_name, dir_val in [("Up", 1), ("Down", -1), ("Combined", 0)]:
                mask = np.ones(len(ext), dtype=bool)
                if bt_filter is not None:
                    mask &= np.isin(types, bt_filter)
                if day_val is not None:
                    mask &= (wds == day_val)
                if dir_val != 0:
                    mask &= (dirs == dir_val)
                arr = ext[mask]
                result[bt_name][day_name][dir_name] = {
                    "probs":      PCTS_CDF,
                    "vals":       cdf_vals(arr),
                    "table_vals": table_vals(arr) if len(arr) > 0 else {},
                }
    return result


def build_prob(prob_arr):
    """Convert numba prob array [6x7] -> structured dict by weekday"""
    WD_KEYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "All"]
    result = {}
    for i, wd in enumerate(WD_KEYS):
        v = int(prob_arr[i, 0])
        if v == 0:
            result[wd] = {}
            continue
        nq_db = int(prob_arr[i, 1]); nq_sb = int(prob_arr[i, 2]); nq_nb = int(prob_arr[i, 3])
        es_db = int(prob_arr[i, 4]); es_sb = int(prob_arr[i, 5]); es_nb = int(prob_arr[i, 6])
        result[wd] = {
            "n": v,
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
    return result


def apply_open_filter(ext, types, dirs, wds, valid, open_flag):
    """Filter extension arrays to sessions where open_flag is True."""
    sess_with_flag = np.where(open_flag)[0]
    sess_set = set(sess_with_flag.tolist())

    # We need to know which sessions each extension belongs to.
    # Since we stored wd per event but not session index, we rebuild
    # by re-filtering using the valid/open arrays for probability,
    # but for extension we need to use the separate per-open filtered runs.
    # (This function is unused; we use separate numba runs instead.)
    pass


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
    return sess_starts, sess_ends, weekdays, N


def normalise(df, sym):
    df.columns = [c.strip() for c in df.columns]
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
    elif 'Date' in df.columns and 'Time' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df = df.sort_values('Datetime').reset_index(drop=True)
    mask = ((df['Datetime'].dt.hour > 9) |
            ((df['Datetime'].dt.hour == 9) & (df['Datetime'].dt.minute >= 30))) & \
           (df['Datetime'].dt.hour < 16)
    df = df[mask].copy()
    df['SessionDate'] = df['Datetime'].dt.date
    keep = ['Datetime', 'SessionDate', 'Open', 'High', 'Low']
    return df[keep].rename(columns={
        'Open': f'{sym}_O', 'High': f'{sym}_H', 'Low': f'{sym}_L'
    })


# ===========================================================================
# OPEN FILTER EXTENSION RECOMPUTE
# We run the numba loop once per (offset, open_filter) combination.
# Rather than filtering results post-hoc, we pass a session-level boolean
# mask into a simpler wrapper.
# ===========================================================================

@njit
def compute_filtered(
    session_starts, session_ends, session_weekdays,
    nq_h, nq_l, nq_o, es_h, es_l, es_o,
    offset_frac, open_mode,          # 0=all, 1=open_in_orig, 2=open_in_cont, 3=open_out_orig
    out_nq_ext, out_nq_type, out_nq_dir, out_nq_wd,
    out_es_ext, out_es_type, out_es_dir, out_es_wd,
    prob,
):
    N = len(session_starts)
    nq_cnt = 0; es_cnt = 0

    for curr in range(1, N):
        prev = curr - 1
        ps = session_starts[prev]; pe = session_ends[prev]
        cs = session_starts[curr]; ce = session_ends[curr]
        if ps > pe or cs > ce: continue
        wd = session_weekdays[curr]
        if wd < 0 or wd > 4: continue

        p_nq_h = -1e10; p_nq_l = 1e10
        p_es_h = -1e10; p_es_l = 1e10
        for i in range(ps, pe + 1):
            if nq_h[i] > p_nq_h: p_nq_h = nq_h[i]
            if nq_l[i] < p_nq_l: p_nq_l = nq_l[i]
            if es_h[i] > p_es_h: p_es_h = es_h[i]
            if es_l[i] < p_es_l: p_es_l = es_l[i]

        nq_pdr = p_nq_h - p_nq_l
        es_pdr = p_es_h - p_es_l
        if nq_pdr <= 0.0 or es_pdr <= 0.0: continue

        nq_ref_h = p_nq_h - offset_frac * nq_pdr
        nq_ref_l = p_nq_l + offset_frac * nq_pdr
        nq_ref_r = nq_ref_h - nq_ref_l
        es_ref_h = p_es_h - offset_frac * es_pdr
        es_ref_l = p_es_l + offset_frac * es_pdr
        es_ref_r = es_ref_h - es_ref_l
        if nq_ref_r <= 0.0 or es_ref_r <= 0.0: continue

        nq_open = nq_o[cs]; es_open = es_o[cs]
        open_in_orig = (nq_open > p_nq_l and nq_open < p_nq_h and
                        es_open > p_es_l and es_open < p_es_h)
        open_in_cont = (nq_open > nq_ref_l and nq_open < nq_ref_h and
                        es_open > es_ref_l and es_open < es_ref_h)

        # Apply open mode filter
        if open_mode == 1 and not open_in_orig: continue
        if open_mode == 2 and not open_in_cont: continue
        if open_mode == 3 and open_in_orig:     continue   # outside orig = not in orig

        # Scan breaks
        nq_broken_h = False; nq_broken_l = False
        es_broken_h = False; es_broken_l = False
        nq_first_dir = 0; es_first_dir = 0
        nq_max_up = -1e10; nq_min_dn = 1e10
        es_max_up = -1e10; es_min_dn = 1e10
        nq_is_double = False; es_is_double = False

        for i in range(cs, ce + 1):
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

        # Prob
        prob[wd, 0] += 1; prob[5, 0] += 1
        if nq_broken_h and nq_broken_l: prob[wd,1]+=1; prob[5,1]+=1
        elif nq_broken_h or nq_broken_l: prob[wd,2]+=1; prob[5,2]+=1
        else: prob[wd,3]+=1; prob[5,3]+=1
        if es_broken_h and es_broken_l: prob[wd,4]+=1; prob[5,4]+=1
        elif es_broken_h or es_broken_l: prob[wd,5]+=1; prob[5,5]+=1
        else: prob[wd,6]+=1; prob[5,6]+=1

        # Extensions
        if nq_first_dir != 0 and nq_ref_r > 0:
            ext_r = (nq_max_up - nq_ref_h)/nq_ref_r if nq_first_dir==1 else (nq_ref_l - nq_min_dn)/nq_ref_r
            out_nq_ext[nq_cnt]=ext_r; out_nq_type[nq_cnt]=2 if nq_is_double else 1
            out_nq_dir[nq_cnt]=nq_first_dir; out_nq_wd[nq_cnt]=wd; nq_cnt+=1
        if es_first_dir != 0 and es_ref_r > 0:
            ext_r = (es_max_up - es_ref_h)/es_ref_r if es_first_dir==1 else (es_ref_l - es_min_dn)/es_ref_r
            out_es_ext[es_cnt]=ext_r; out_es_type[es_cnt]=2 if es_is_double else 1
            out_es_dir[es_cnt]=es_first_dir; out_es_wd[es_cnt]=wd; es_cnt+=1

    return nq_cnt, es_cnt


# ===========================================================================
# OPEN GAP STATS (single pass for all offsets)
# ===========================================================================

@njit
def compute_open_stats(
    session_starts, session_ends, session_weekdays,
    nq_h, nq_l, nq_o, es_h, es_l, es_o,
    offsets,           # float32 array of offsets
    # output: [num_offsets, 5 (wd), 4 (col)] col: 0=total,1=in_orig,2=in_cont,3=out_orig
    stats_wd,
    stats_all,         # [num_offsets, 4]
):
    N = len(session_starts)
    n_off = len(offsets)

    for curr in range(1, N):
        prev = curr - 1
        ps = session_starts[prev]; pe = session_ends[prev]
        cs = session_starts[curr]; ce = session_ends[curr]
        if ps > pe or cs > ce: continue
        wd = session_weekdays[curr]
        if wd < 0 or wd > 4: continue

        p_nq_h = -1e10; p_nq_l = 1e10
        p_es_h = -1e10; p_es_l = 1e10
        for i in range(ps, pe + 1):
            if nq_h[i] > p_nq_h: p_nq_h = nq_h[i]
            if nq_l[i] < p_nq_l: p_nq_l = nq_l[i]
            if es_h[i] > p_es_h: p_es_h = es_h[i]
            if es_l[i] < p_es_l: p_es_l = es_l[i]

        nq_pdr = p_nq_h - p_nq_l
        es_pdr = p_es_h - p_es_l
        if nq_pdr <= 0.0 or es_pdr <= 0.0: continue

        nq_open = nq_o[cs]; es_open = es_o[cs]
        open_in_orig = (nq_open > p_nq_l and nq_open < p_nq_h and
                        es_open > p_es_l and es_open < p_es_h)

        for k in range(n_off):
            off = offsets[k]
            nq_ref_h = p_nq_h - off * nq_pdr
            nq_ref_l = p_nq_l + off * nq_pdr
            es_ref_h = p_es_h - off * es_pdr
            es_ref_l = p_es_l + off * es_pdr

            open_in_cont = (nq_open > nq_ref_l and nq_open < nq_ref_h and
                            es_open > es_ref_l and es_open < es_ref_h)

            stats_wd[k, wd, 0] += 1
            stats_all[k, 0] += 1
            if open_in_orig:
                stats_wd[k, wd, 1] += 1; stats_all[k, 1] += 1
            if open_in_cont:
                stats_wd[k, wd, 2] += 1; stats_all[k, 2] += 1
            if not open_in_orig:
                stats_wd[k, wd, 3] += 1; stats_all[k, 3] += 1


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    t0 = time.time()
    SEP = "=" * 72

    print(SEP)
    print("  PDR MULTI-CONTRACTION ANALYSIS")
    print(f"  Offsets tested: {[f'{int(o*100)}%' for o in OFFSETS]}")
    print(f"  Open filters:  All | Open in Original | Open in Contracted | Gap Open")
    print(SEP)

    # -----------------------------------------------------------------------
    # Load & merge
    # -----------------------------------------------------------------------
    print("\nLoading NQ 1m RTH...")
    nq = pd.read_parquet(NQ_PATH)
    print(f"  {len(nq):,} rows | cols: {list(nq.columns)}")
    print("Loading ES 1m RTH...")
    es = pd.read_parquet(ES_PATH)
    print(f"  {len(es):,} rows")

    nq = normalise(nq, 'NQ')
    es = normalise(es, 'ES')
    df = pd.merge(nq, es, on=['Datetime', 'SessionDate'], how='inner')
    df = df.sort_values('Datetime').reset_index(drop=True)
    sess_starts, sess_ends, weekdays, N = build_sessions(df)
    n_sess = df['SessionDate'].nunique()
    print(f"\nMerged: {len(df):,} rows | {n_sess} sessions")

    nq_h = df['NQ_H'].values.astype(np.float32)
    nq_l = df['NQ_L'].values.astype(np.float32)
    nq_o = df['NQ_O'].values.astype(np.float32)
    es_h = df['ES_H'].values.astype(np.float32)
    es_l = df['ES_L'].values.astype(np.float32)
    es_o = df['ES_O'].values.astype(np.float32)

    # -----------------------------------------------------------------------
    # Open gap stats (all offsets in one pass)
    # -----------------------------------------------------------------------
    print("\nComputing open gap stats...")
    off_arr = np.array(OFFSETS, dtype=np.float32)
    n_off = len(OFFSETS)
    stats_wd  = np.zeros((n_off, 5, 4), dtype=np.int32)
    stats_all = np.zeros((n_off, 4),    dtype=np.int32)
    compute_open_stats(sess_starts, sess_ends, weekdays,
                       nq_h, nq_l, nq_o, es_h, es_l, es_o,
                       off_arr, stats_wd, stats_all)

    WD_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    OFF_LABELS = [f"{int(o*100)}% contracted" for o in OFFSETS]

    print(f"\n{'-'*72}")
    print("OPEN POSITION STATS (Both NQ & ES open within range)")
    print(f"{'':30} {'Total':>8} {'In Orig':>10} {'In Cont':>10} {'Gap Open':>10} {'Gap%':>7}")
    print(f"{'-'*72}")
    for k, off_label in enumerate(OFF_LABELS):
        total = stats_all[k, 0]
        in_orig = stats_all[k, 1]
        in_cont = stats_all[k, 2]
        gap = stats_all[k, 3]
        print(f"  {off_label:<28} {total:>8,} {in_orig:>10,} {in_cont:>10,} {gap:>10,} {gap/total*100:>6.1f}%")

    print(f"\n  By Weekday (0% original range — gap open days):")
    print(f"  {'Day':<12}", end="")
    for wd in WD_NAMES:
        print(f"  {wd[:3]:>8}", end="")
    print()
    for k, off_label in enumerate(OFF_LABELS):
        label = f"  {off_label:<12}"
        print(label, end="")
        for d in range(5):
            total = stats_wd[k, d, 0]
            gap   = stats_wd[k, d, 3]
            pct   = gap / total * 100 if total > 0 else 0
            print(f"  {pct:>6.1f}%", end="")
        print()

    # -----------------------------------------------------------------------
    # Main analysis loop: offset x open_mode
    # -----------------------------------------------------------------------
    OPEN_MODES = [
        (0, "all",           "All Sessions"),
        (1, "open_in_orig",  "Open Within Original PDR"),
        (2, "open_in_cont",  "Open Within Contracted Range"),
        (3, "open_out_orig", "Gap Open (Outside PDR)"),
    ]

    all_results = {}   # key: f"{offset_pct}_{open_mode_key}"

    MAX = N * 2
    for offset in OFFSETS:
        off_pct = int(offset * 100)
        off_label = f"off{off_pct}"
        print(f"\n{SEP}")
        print(f"  OFFSET = {off_pct}%  |  New PDR = {int((1-2*offset)*100)}% of original")
        print(SEP)

        for mode_int, mode_key, mode_label in OPEN_MODES:
            nq_ext  = np.zeros(MAX, np.float32); nq_type = np.zeros(MAX, np.int32)
            nq_dir  = np.zeros(MAX, np.int32);   nq_wd   = np.zeros(MAX, np.int32)
            es_ext  = np.zeros(MAX, np.float32); es_type = np.zeros(MAX, np.int32)
            es_dir  = np.zeros(MAX, np.int32);   es_wd   = np.zeros(MAX, np.int32)
            prob    = np.zeros((6, 7), dtype=np.int32)

            t1 = time.time()
            nq_cnt, es_cnt = compute_filtered(
                sess_starts, sess_ends, weekdays,
                nq_h, nq_l, nq_o, es_h, es_l, es_o,
                np.float32(offset), mode_int,
                nq_ext, nq_type, nq_dir, nq_wd,
                es_ext, es_type, es_dir, es_wd,
                prob,
            )

            nq_ext = nq_ext[:nq_cnt]; nq_type = nq_type[:nq_cnt]
            nq_dir = nq_dir[:nq_cnt]; nq_wd   = nq_wd[:nq_cnt]
            es_ext = es_ext[:es_cnt]; es_type = es_type[:es_cnt]
            es_dir = es_dir[:es_cnt]; es_wd   = es_wd[:es_cnt]

            prob_struct = build_prob(prob)
            nq_ext_block = build_ext_block(nq_ext, nq_type, nq_dir, nq_wd)
            es_ext_block = build_ext_block(es_ext, es_type, es_dir, es_wd)

            key = f"{off_label}_{mode_key}"
            all_results[key] = {
                "label":   f"{off_pct}% contracted — {mode_label}",
                "offset":  offset,
                "open_mode": mode_key,
                "prob":    prob_struct,
                "ext":     {"nq": nq_ext_block, "es": es_ext_block},
            }

            # --- Print summary ---
            n_total = int(prob[5, 0])
            p = prob_struct.get("All", {})
            if p:
                nq_p = p.get("nq", {}); es_p = p.get("es", {})
                nq_ext_p50 = nq_ext_block["all_breaks"]["All"]["Combined"]["table_vals"].get("p50", 0)
                es_ext_p50 = es_ext_block["all_breaks"]["All"]["Combined"]["table_vals"].get("p50", 0)
                print(f"\n  [{mode_label}]  N={n_total:,}")
                print(f"  NQ: Break={nq_p.get('atleast_one',0):.1f}%  "
                      f"Single={nq_p.get('single',0):.1f}%  "
                      f"Double={nq_p.get('double',0):.1f}%  "
                      f"Inside={nq_p.get('inside',0):.1f}%  "
                      f"P50 ext={nq_ext_p50:.3f}R")
                print(f"  ES: Break={es_p.get('atleast_one',0):.1f}%  "
                      f"Single={es_p.get('single',0):.1f}%  "
                      f"Double={es_p.get('double',0):.1f}%  "
                      f"Inside={es_p.get('inside',0):.1f}%  "
                      f"P50 ext={es_ext_p50:.3f}R")

    # -----------------------------------------------------------------------
    # Build open stats JSON block
    # -----------------------------------------------------------------------
    open_stats = {}
    for k, off in enumerate(OFFSETS):
        off_pct = int(off * 100)
        total = int(stats_all[k, 0])
        open_stats[f"off{off_pct}"] = {
            "offset": off,
            "total":    total,
            "in_orig":  int(stats_all[k, 1]),
            "in_cont":  int(stats_all[k, 2]),
            "gap_open": int(stats_all[k, 3]),
            "in_orig_pct":  round(stats_all[k, 1] / total * 100, 2) if total else 0,
            "in_cont_pct":  round(stats_all[k, 2] / total * 100, 2) if total else 0,
            "gap_open_pct": round(stats_all[k, 3] / total * 100, 2) if total else 0,
            "by_weekday": {
                WD_NAMES[d]: {
                    "total":    int(stats_wd[k, d, 0]),
                    "in_orig":  int(stats_wd[k, d, 1]),
                    "in_cont":  int(stats_wd[k, d, 2]),
                    "gap_open": int(stats_wd[k, d, 3]),
                    "gap_pct":  round(stats_wd[k, d, 3] / stats_wd[k, d, 0] * 100, 2)
                                if stats_wd[k, d, 0] else 0,
                } for d in range(5)
            }
        }

    # -----------------------------------------------------------------------
    # Save JSON
    # -----------------------------------------------------------------------
    output = {
        "meta": {
            "offsets": OFFSETS,
            "open_modes": [m[1] for m in OPEN_MODES],
            "note": "Extensions in contracted PDR units. Multiply by (1-2*offset) to get original PDR units.",
        },
        "open_stats": open_stats,
        "scenarios": all_results,
    }

    results_dir = r"d:\Antigravity\Results"
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "pdr_multi_analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(',', ':'))

    print(f"\n{SEP}")
    print(f"  JSON saved to: {out_path}")
    print(f"  Total time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
