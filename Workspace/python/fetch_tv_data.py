from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import os

def fetch_data():
    print("Initializing tvDatafeed (logging in as guest)...")
    tv = TvDatafeed()
    
    symbol = 'NIFTY'
    exchange = 'NSE'
    print(f"Fetching 1-minute data for {symbol} on {exchange}...")
    
    # Fetch 5000 bars (candles) of 1-minute data, which is roughly a week of trading data
    data = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_1_minute, n_bars=5000)
    
    if data is not None and not data.empty:
        output_path = r"d:\Antigravity\Workspace\python\nifty_1min_sample.csv"
        data.to_csv(output_path)
        print(f"\nSUCCESS! Saved {len(data)} rows of 1-minute data to: {output_path}")
        print("\nHere is a preview of the data:")
        print(data.head())
        print("...")
        print(data.tail())
    else:
        print("Failed to fetch data.")

if __name__ == "__main__":
    fetch_data()
