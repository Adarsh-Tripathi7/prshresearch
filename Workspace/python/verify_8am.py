import pandas as pd
import numpy as np

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

print("Loading NQ data...")
nq_1m = pd.read_parquet(r"d:\Antigravity\Historical data\NQ Futures Datasets\Full Data\parquet\NQ_1m_full_data.parquet")
nq_1m['Datetime'] = pd.to_datetime(nq_1m['Date'].astype(str) + ' ' + nq_1m['Time'].astype(str))
nq_1m['SessionDate'] = pd.to_datetime(nq_1m['Datetime'].apply(get_session_date))
nq_1m['Mins'] = nq_1m['Datetime'].apply(calc_mins_from_start)

# Filter for just a few days to manually verify
sessions = nq_1m['SessionDate'].unique()
sample_sessions = sessions[-10:] # last 10 days

print("\n--- Manual Verification of 08:00-08:59 Window ---")
start_m = 900 # 08:00
end_m = 959   # 08:59
rth_close_m = 1380 # 16:00

for sess in sample_sessions:
    df_sess = nq_1m[nq_1m['SessionDate'] == sess]
    
    ib_df = df_sess[(df_sess['Mins'] >= start_m) & (df_sess['Mins'] <= end_m)]
    if ib_df.empty: continue
        
    ib_h = ib_df['High'].max()
    ib_l = ib_df['Low'].min()
    
    post_df = df_sess[(df_sess['Mins'] > end_m) & (df_sess['Mins'] <= rth_close_m)]
    
    broke_h = (post_df['High'] > ib_h).any()
    broke_l = (post_df['Low'] < ib_l).any()
    
    db = broke_h and broke_l
    
    print(f"Session: {sess.date()} | IB High: {ib_h:.2f} | IB Low: {ib_l:.2f}")
    
    if broke_h:
        h_time = post_df[post_df['High'] > ib_h]['Datetime'].iloc[0]
        print(f"  -> Broke High at {h_time.time()}")
    if broke_l:
        l_time = post_df[post_df['Low'] < ib_l]['Datetime'].iloc[0]
        print(f"  -> Broke Low at {l_time.time()}")
        
    print(f"  -> Double Break: {db}\n")
