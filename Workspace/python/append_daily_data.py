"""
append_daily_data.py
Fetches the latest 1-minute NQ/ES data from yfinance 
and appends it to the existing historical Parquet files.

Usage:
    python append_daily_data.py
    
This script is safe to run multiple times — it deduplicates by timestamp.
"""
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

DATA_DIR = r'd:\Antigravity\Workspace\data'
os.makedirs(DATA_DIR, exist_ok=True)

TICKERS = {
    'NQ=F': 'NQ_1min.parquet',
    'ES=F': 'ES_1min.parquet'
}

def fetch_and_append(ticker_symbol, filename):
    filepath = os.path.join(DATA_DIR, filename)
    
    # Fetch last 7 days of 1-minute data (maximum allowed)
    print(f"\n--- {ticker_symbol} ---")
    print(f"Fetching 1-min data (last 7 days)...")
    
    ticker = yf.Ticker(ticker_symbol)
    new_data = ticker.history(period='7d', interval='1m')
    
    if new_data.empty:
        print(f"  No data returned for {ticker_symbol}. Market may be closed.")
        return
    
    print(f"  Fetched {len(new_data)} rows ({new_data.index.min()} to {new_data.index.max()})")
    
    # Clean columns
    new_data = new_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    new_data.index.name = 'Datetime'
    
    if os.path.exists(filepath):
        # Load existing data
        existing = pd.read_parquet(filepath)
        print(f"  Existing file: {len(existing)} rows")
        
        # Ensure both have the same index type
        if not isinstance(existing.index, pd.DatetimeIndex):
            existing.index = pd.to_datetime(existing.index)
        
        # Merge and deduplicate
        combined = pd.concat([existing, new_data])
        combined = combined[~combined.index.duplicated(keep='last')]
        combined = combined.sort_index()
        
        new_rows = len(combined) - len(existing)
        print(f"  Added {new_rows} new rows (total: {len(combined)})")
    else:
        combined = new_data
        print(f"  Created new file with {len(combined)} rows")
    
    # Save
    combined.to_parquet(filepath, engine='pyarrow', compression='snappy')
    size_kb = os.path.getsize(filepath) / 1024
    print(f"  Saved to {filename} ({size_kb:.1f}KB)")

def main():
    print("=" * 50)
    print(f"  NQ/ES Daily Data Append")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    for ticker, filename in TICKERS.items():
        try:
            fetch_and_append(ticker, filename)
        except Exception as e:
            print(f"  ERROR fetching {ticker}: {e}")
    
    print("\n[OK] Done!")

if __name__ == '__main__':
    main()
