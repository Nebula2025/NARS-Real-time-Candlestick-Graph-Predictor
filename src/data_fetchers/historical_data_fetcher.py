import os
import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockBarsRequest

class HistoricalDataFetcher:
    """
    A data fetching class for streaming live financial data.
    It sets up the WebSocket client for receiving live market data and provides
    convenience methods to subscribe/unsubscribe to specific event streams.
    """

    def __init__(self, api_key: str, secret_key: str, symbol: str) -> None:
        """
        Instantiates a WebSocket client for accessing live financial data.

        Args:
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            symbol (str): Ticker symbol to subscribe to.

        Raises:
            ValueError: If API keys are missing or if the symbol is not valid.
        """
        # Check if API key and secret key are provided
        if not api_key or not secret_key:
            raise ValueError("API key and secret key are required.")
        
        # Checks if the provided symbol is valid
        trading_client = TradingClient(api_key, secret_key, paper=True)
        try:
            asset = trading_client.get_asset(symbol_or_asset_id=symbol)
            if asset.asset_class != AssetClass.US_EQUITY:
                raise ValueError(f"Invalid asset class for symbol: {symbol}")
        except Exception as e:
            raise ValueError(f"A valid symbol is required. Error: {e}")
        
        self._symbol = symbol
        self._client = StockHistoricalDataClient(api_key, secret_key)

    def retrieve_historical_bar_data(self, timeframe: TimeFrame, start: datetime.datetime, end: datetime.datetime) -> None:
        """
        Retrieves historical bar data for the given timeframe and date range,
        then saves the data to a CSV file if it doesn't already exist.

        Args:
            timeframe (TimeFrame): The time frame for the bar data (e.g., 1 minute, 1 hour).
            start (datetime): The start datetime for the data query.
            end (datetime): The end datetime for the data query.

        Returns:
            None
        """
        # Format the filename based on the symbol, timeframe, start, and end
        filename = f"data/{self._symbol}-{timeframe.value}-{start.strftime('%Y-%m-%d-%H-%M-%S')}-{end.strftime('%Y-%m-%d-%H-%M-%S')}.csv"
        
        # Check if the file already exists
        if not os.path.exists(filename):
            # Request data from Alpaca
            request_params = StockBarsRequest(
                symbol_or_symbols=self._symbol,
                timeframe=timeframe,
                start=start,
                end=end
            )
            bars = self._client.get_stock_bars(request_params)
            
            # Save the DataFrame to a CSV file
            bars.df.to_csv(filename)
            print(f"Data saved to {filename}")
        else:
            print(f"Data already exists in file:{filename}.")