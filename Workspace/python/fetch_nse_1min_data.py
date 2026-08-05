import pandas as pd
from datasets import load_dataset
import os
import sys

def download_and_save_data(target_symbol, output_dir=r"d:\Antigravity\Workspace\python"):
    print(f"Streaming dataset over the network... scanning for symbol: {target_symbol}")
    print("This will scan through the 10GB dataset on-the-fly to save disk space.")
    print("It may take 10-30 minutes depending on your internet speed.")
    
    # streaming=True prevents downloading the full 125GB to disk
    # We use streaming to iterate through records over the internet
    ds_minute = load_dataset("xxparthparekhxx/indian-stock-market-minute-data", split="minute", streaming=True)
    
    rows = []
    count = 0
    try:
        for row in ds_minute:
            count += 1
            if count % 500000 == 0:
                print(f"Scanned {count} rows... Found {len(rows)} matching rows so far.")
                
            if row["symbol"] == target_symbol:
                rows.append(row)
                
    except Exception as e:
        print(f"\nStream ended or interrupted: {e}")
            
    if not rows:
        print(f"\nNo data found for symbol: {target_symbol}")
        return

    print(f"\nFinished scanning. Creating DataFrame and saving to CSV...")
    df = pd.DataFrame(rows)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    safe_symbol = target_symbol.replace(' ', '_')
    output_path = os.path.join(output_dir, f"{safe_symbol}_1min_hf_data.csv")
    df.to_csv(output_path, index=False)
    print(f"Successfully saved {len(df)} rows to {output_path}")

if __name__ == "__main__":
    # NIFTY 50 is usually represented as "NIFTY 50" in NSE datasets
    download_and_save_data("NIFTY 50")
