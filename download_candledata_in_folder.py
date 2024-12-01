import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import argparse

class NSEDataDownloader:
    def __init__(self):
        # Hardcoded number of years
        self.years = 3
        
    def setup_folder(self, symbol):
        """
        Create folder based on symbol name if it doesn't exist
        
        Parameters:
        symbol (str): Stock symbol
        
        Returns:
        str: Absolute path to the folder
        """
        folder_name = symbol.upper()
        folder_path = os.path.abspath(folder_name)
        
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
                print(f"Created new folder: {folder_path}")
            except Exception as e:
                raise Exception(f"Error creating folder: {str(e)}")
        else:
            print(f"Using existing folder: {folder_path}")
            
        return folder_path

    def validate_symbol(self, symbol):
        """
        Validate if the symbol exists on NSE
        
        Parameters:
        symbol (str): Stock symbol
        
        Returns:
        tuple: (nse_symbol, base_symbol)
        """
        base_symbol = symbol.upper()
        nse_symbol = f"{base_symbol}.NS"
        
        try:
            ticker = yf.Ticker(nse_symbol)
            test_data = ticker.history(period="1d")
            if test_data.empty:
                raise Exception(f"Could not find data for {base_symbol} on NSE")
            return nse_symbol, base_symbol
        except Exception as e:
            raise Exception(f"Error validating symbol {base_symbol}: {str(e)}")

    def download_candlestick_data(self, nse_symbol, base_symbol):
        """
        Download weekly candlestick data for a given NSE symbol
        
        Parameters:
        nse_symbol (str): NSE stock symbol with .NS suffix
        base_symbol (str): Original stock symbol for file naming
        
        Returns:
        pandas.DataFrame: DataFrame containing the candlestick data
        """
        print(f"Downloading data for {base_symbol} from NSE...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.years*365)
        
        try:
            # Create folder for this symbol
            folder_path = self.setup_folder(base_symbol)
            
            ticker = yf.Ticker(nse_symbol)
            df = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1wk'
            )
            
            if df.empty:
                raise Exception("No data was downloaded")
                
            # Clean and format the data
            df = df.reset_index()
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
            
            # Round the prices to 2 decimal places
            price_columns = ['Open', 'High', 'Low', 'Close']
            df[price_columns] = df[price_columns].round(2)
            
            # Convert volume to integer
            df['Volume'] = df['Volume'].astype(int)
            
            # Add symbol column
            df.insert(0, 'Symbol', base_symbol)
            
            # Create filename and full path
            filename = f"NSE_{base_symbol}_weekly_{self.years}years_{datetime.now().strftime('%Y%m%d')}.csv"
            file_path = os.path.join(folder_path, filename)
            
            # Save to CSV
            df.to_csv(file_path, index=False)
            print(f"Data successfully saved to {file_path}")
            
            return df
            
        except Exception as e:
            raise Exception(f"Error downloading data: {str(e)}")

    def display_data_summary(self, df, symbol):
        """
        Display summary of the downloaded data
        """
        if df is not None and not df.empty:
            print(f"\nSummary for {symbol}:")
            print("\nFirst few rows of the downloaded data:")
            print(df.head())
            
            print("\nBasic statistics:")
            stats = df[['Open', 'High', 'Low', 'Close', 'Volume']].describe()
            pd.set_option('display.float_format', lambda x: '%.2f' % x)
            print(stats)
            
            print(f"\nDate range: {df['Date'].min()} to {df['Date'].max()}")
            print(f"Total number of weeks: {len(df)}")

def main():
    parser = argparse.ArgumentParser(description='NSE Stock Data Downloader - Weekly Candlestick Data')
    parser.add_argument('symbols', nargs='+', help='One or more stock symbols (e.g., TATAMOTORS RELIANCE TCS)')
    args = parser.parse_args()

    try:
        downloader = NSEDataDownloader()
        
        for symbol in args.symbols:
            try:
                print("\n" + "="*50)
                nse_symbol, base_symbol = downloader.validate_symbol(symbol)
                df = downloader.download_candlestick_data(nse_symbol, base_symbol)
                downloader.display_data_summary(df, base_symbol)
                print("="*50 + "\n")
            except Exception as e:
                print(f"Error processing {symbol}: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()