"""
Generate per-hour percentile JSON data for the HTML dashboard.
Reads nq_break_results.csv and outputs the data as a JS file.
"""
import pandas as pd
import numpy as np
import json, os

DATA_DIR = r"d:\Antigravity\SCID\NQ"
SESSION_START = 18
PCTS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]

df = pd.read_csv(os.path.join(DATA_DIR, "nq_break_results.csv"))
df['initial_ext_r'] = np.where(df['type'] == 2, df['max_ext_before_double_r'], df['max_ext_r'])
print(f"Loaded {len(df)} rows")

# Window labels like the reference: "18:00-18:59", etc.
def block_to_window(bi):
    h = (bi + SESSION_START) % 24
    return f"{h:02d}:00-{h:02d}:59"

# --- Probability data ---
prob_data = []
for bi in sorted(df["block_idx"].unique()):
    sub = df[df["block_idx"] == bi]
    total = len(sub)
    n_db = int((sub["type"] == 2).sum())
    prob_data.append({
        "Window": block_to_window(bi),
        "NQ_DB_Prob": round(100 * n_db / total, 2) if total > 0 else 0,
        "Total": total,
        "DB": n_db,
        "SB": int((sub["type"] == 1).sum()),
        "NB": int((sub["type"] == 0).sum()),
    })

# --- Extension data by hour ---
def compute_ext(subset, col):
    vals = subset[col].values
    if len(vals) == 0:
        return None
    row = {"N": len(vals)}
    for p in PCTS:
        row[f"{p}%"] = round(float(np.percentile(vals, p)), 2)
    return row

ext_data = {"double_break": {"combined": [], "high_first": [], "low_first": []},
            "single_break": {"combined": [], "high_first": [], "low_first": []},
            "all_breaks": {"combined": [], "high_first": [], "low_first": []}}

for bi in sorted(df["block_idx"].unique()):
    w = block_to_window(bi)
    sub = df[df["block_idx"] == bi]
    
    for break_type, type_val, col in [
        ("double_break", 2, "max_ext_before_double_r"),
        ("single_break", 1, "initial_ext_r"),
        ("all_breaks", None, "initial_ext_r"),
    ]:
        if type_val is not None:
            bsub = sub[sub["type"] == type_val]
        else:
            bsub = sub[sub["type"] > 0]
        
        for direction, dir_val in [("combined", None), ("high_first", 1), ("low_first", -1)]:
            if dir_val is not None:
                dsub = bsub[bsub["first_break_dir"] == dir_val]
            else:
                dsub = bsub
            
            r = compute_ext(dsub, col)
            if r is None:
                r = {"N": 0}
                for p in PCTS:
                    r[f"{p}%"] = 0
            r["Window"] = w
            # Move Window to front
            r = {"Window": r["Window"], **{k: v for k, v in r.items() if k != "Window"}}
            ext_data[break_type][direction].append(r)

# --- H/L First probability data ---
prob_first_data = []
for bi in sorted(df["block_idx"].unique()):
    w = block_to_window(bi)
    sub = df[df["block_idx"] == bi]
    breaks = sub[sub["type"] > 0]
    hf = breaks[breaks["first_break_dir"] == 1]
    lf = breaks[breaks["first_break_dir"] == -1]
    total_breaks = len(breaks)
    
    # Of those that broke high first, how many also broke low (double break)?
    hf_db = hf[hf["type"] == 2]
    lf_db = lf[lf["type"] == 2]
    
    row = {
        "Window": w,
        "NQ_H_First_Pct": round(100 * len(hf) / total_breaks, 2) if total_breaks > 0 else 0,
        "NQ_L_First_Pct": round(100 * len(lf) / total_breaks, 2) if total_breaks > 0 else 0,
        "NQ_H_First_Opp_Break": round(100 * len(hf_db) / len(hf), 2) if len(hf) > 0 else 0,
        "NQ_L_First_Opp_Break": round(100 * len(lf_db) / len(lf), 2) if len(lf) > 0 else 0,
    }
    prob_first_data.append(row)

data = {
    "prob": prob_data,
    "prob_first": prob_first_data,
    "ext": {"nq": ext_data},
}

# Write as JS
js_content = f"window._D = {json.dumps(data, separators=(',', ':'))};"
out_path = os.path.join(DATA_DIR, "nq_break_data.js")
with open(out_path, "w") as f:
    f.write(js_content)
print(f"Data written to {out_path} ({len(js_content):,} bytes)")
