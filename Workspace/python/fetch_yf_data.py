import yfinance as yf
import pandas as pd

def fetch_data():
    symbol = "RELIANCE.NS"
    print(f"Fetching 1-minute historical data for {symbol} using yfinance...")
    
    # yfinance allows up to 7 days of 1-minute data for free
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="7d", interval="1m")
    
    if data is not None and not data.empty:
        output_path = r"d:\Antigravity\Workspace\python\reliance_1min_sample.csv"
        # Reset index to make Datetime a column
        data.reset_index(inplace=True)
        data.to_csv(output_path, index=False)
        print(f"\nSUCCESS! Saved {len(data)} rows of 1-minute data to: {output_path}")
        print("\nPreview of the downloaded data:")
        print(data.head())
    else:
        print("Failed to fetch data.")

if __name__ == "__main__":
    fetch_data()
