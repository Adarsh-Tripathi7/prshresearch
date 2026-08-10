"""
Convert msgpack data files to multiple parquet files per timeframe.
Handles mixed types by coercing numeric columns.
"""
import os
import glob
import msgpack
import pandas as pd
import numpy as np

data_dir = r'd:\Antigravity\prshcapital\data'
pq_dir = os.path.join(data_dir, 'pq')
os.makedirs(pq_dir, exist_ok=True)

msgpack_files = glob.glob(os.path.join(data_dir, '*.msgpack'))

total_json_size = 0
total_pq_size = 0

def safe_to_parquet(df, path):
    """Convert df to parquet, coercing numeric columns properly."""
    for col in df.columns:
        if col == 'Window':
            df[col] = df[col].astype(str)
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df.to_parquet(path, engine='pyarrow', compression='snappy')

for mp_file in msgpack_files:
    basename = os.path.splitext(os.path.basename(mp_file))[0]
    out_dir = os.path.join(pq_dir, basename)
    os.makedirs(out_dir, exist_ok=True)
    
    with open(mp_file, 'rb') as f:
        data = msgpack.unpack(f, raw=False)
    
    total_json_size += os.path.getsize(mp_file)
    print(f'\n=== {basename} ({os.path.getsize(mp_file)/1024:.1f}KB msgpack) ===')
    
    # Handle pdr/pwr files which have a different structure
    if not isinstance(data, dict) or 'prob' not in data:
        if isinstance(data, list):
            df = pd.DataFrame(data)
            for col in df.columns:
                if col == 'Window' or col == 'Day' or col == 'Date':
                    df[col] = df[col].astype(str)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            pq_path = os.path.join(out_dir, 'data.parquet')
            df.to_parquet(pq_path, engine='pyarrow', compression='snappy')
            sz = os.path.getsize(pq_path)
            total_pq_size += sz
            print(f'  data: {len(df)} rows -> {sz/1024:.1f}KB')
        continue
    
    # Convert flat tables
    for key in ['prob', 'prob_first', 'corr', 'close_pos']:
        if key in data and isinstance(data[key], list) and len(data[key]) > 0:
            df = pd.DataFrame(data[key])
            pq_path = os.path.join(out_dir, f'{key}.parquet')
            safe_to_parquet(df, pq_path)
            sz = os.path.getsize(pq_path)
            total_pq_size += sz
            print(f'  {key}: {len(df)} rows -> {sz/1024:.1f}KB')
    
    # Convert nested ext tables
    if 'ext' in data and isinstance(data['ext'], dict):
        for asset in data['ext']:
            for btype in data['ext'][asset]:
                for direction in data['ext'][asset][btype]:
                    rows = data['ext'][asset][btype][direction]
                    if isinstance(rows, list) and len(rows) > 0:
                        df = pd.DataFrame(rows)
                        fname = f'ext_{asset}_{btype}_{direction}.parquet'
                        pq_path = os.path.join(out_dir, fname)
                        safe_to_parquet(df, pq_path)
                        sz = os.path.getsize(pq_path)
                        total_pq_size += sz
                        print(f'  ext/{asset}/{btype}/{direction}: {len(df)} rows -> {sz/1024:.1f}KB')

print(f'\n--- TOTAL ---')
print(f'MsgPack total: {total_json_size/1024/1024:.2f}MB')
print(f'Parquet total: {total_pq_size/1024/1024:.2f}MB')
print(f'Compression ratio: {total_json_size/total_pq_size:.1f}x smaller')
