import argparse
import datetime
from config.config import Config
from src.data_fetchers.historical_data_fetcher import HistoricalDataFetcher
from alpaca.data.timeframe import TimeFrame

def parse_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Fetch historical bar data from Alpaca API.")
    
    # Command-line arguments
    parser.add_argument('--symbol', type=str, required=True, help="Ticker symbol (e.g., 'SPY')")
    parser.add_argument('--start', type=str, required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument('--end', type=str, help="End date in YYYY-MM-DD format (Optional, default is today)")
    parser.add_argument('--timeframe', type=str, required=True, choices=['minute', 'hour', 'day'],
                        help="Timeframe for the data (minute, hour, or day)")
    
    return parser.parse_args()

def main():
    # Parse command-line arguments
    args = parse_args()

    # Convert start date string to a datetime object
    start_date = datetime.datetime.strptime(args.start, '%Y-%m-%d')
    
    # If end date is provided, convert it, otherwise set it to today's date
    if args.end:
        end_date = datetime.datetime.strptime(args.end, '%Y-%m-%d')
    else:
        end_date = datetime.datetime.now()  # Default to the current date and time

    # Map string input for timeframe to actual TimeFrame enum
    timeframe_map = {
        'minute': TimeFrame.Minute,
        'hour': TimeFrame.Hour,
        'day': TimeFrame.Day
    }
    timeframe = timeframe_map[args.timeframe]

    # Instantiate the data fetcher and retrieve historical bar data
    d = HistoricalDataFetcher(Config.ALPACA_API_KEY, Config.ALPACA_SECRET_KEY, args.symbol)
    d.retrieve_historical_bar_data(timeframe, start_date, end_date)

if __name__ == "__main__":
    main()