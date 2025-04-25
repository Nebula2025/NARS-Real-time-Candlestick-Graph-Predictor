from src.common.enums import EventType
from data_handlers.live_data_handler import LiveDataHandler
from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from alpaca.trading.enums import AssetClass

class LiveDataFetcher:
    """
    A data fetching class for streaming live financial data.
    It sets up the WebSocket client for receiving live market data and provides
    convenience methods to subscribe/unsubscribe to specific event streams.
    """

    async def __init__(self, api_key: str, secret_key: str, symbol: str) -> None:
        """
        Instantiates a WebSocket client for accessing live financial data.

        Args:
            stream_type (StreamType): Type of Alpaca data stream (Crypto, Stock, or Option).
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            symbol (str): Ticker symbol to subscribe to.

        Raises:
            ValueError: If API keys are missing or if the symbol is not valid.
            TypeError: If the LiveDataHandler's create_handler method is not callable.
            ConnectionError: If the WebSocket client fails to initialize.
        """
        # Check if API key and secret key are provided
        if not api_key or not secret_key:
            raise ValueError("API key and secret key are required.")

        # Check if handler is callable
        if not callable(LiveDataHandler.create_handler):
            raise TypeError("The handler must be a callable function.")

        # Checks if the provided symbol is valid
        trading_client = TradingClient(api_key, secret_key, paper=True)
        try:
            asset = trading_client.get_asset(symbol_or_asset_id=symbol)
            if asset.asset_class != AssetClass.US_EQUITY:
                raise ValueError(f"Invalid asset class for symbol: {symbol}")
        except Exception as e:
            raise ValueError(f"A valid symbol is required. Error: {e}")
            
        self._symbol = symbol
        self._running = False
        self._handler = LiveDataHandler(symbol)
        
        self._wss_client = StockDataStream(api_key, secret_key)

        self._subscriptions = self._initialize_subscriptions()
        
    def _initialize_subscriptions(self):
        """
        Initializes subscription methods.
        
        Returns:
            dict: A mapping of EventType to a list containing:
                [subscribe_method, unsubscribe_method, subscription_state]
                subscription_state is 0 for unsubscribed and 1 for subscribed.
        """
        subscriptions = {
            EventType.BARS: [self._wss_client.subscribe_bars, self._wss_client.unsubscribe_bars, 0],
            EventType.DAILY_BARS: [self._wss_client.subscribe_daily_bars, self._wss_client.unsubscribe_daily_bars, 0],
        }

        return subscriptions

    def _subscribe_event(self, event_type: EventType) -> None:
        """
        Subscribes to a specific event type if not already subscribed.

        Args:
            event_type (EventType): The event type to subscribe to.
        """
        event = self._subscriptions.get(event_type)
        if event and event[2] == 0:  # Not subscribed
            event[0](self._handler.create_handler(event_type, self._stream_type), self._symbol)
            event[2] = 1  # Mark as subscribed
        else:
            print(f"Already subscribed to {event_type}")

    def _unsubscribe_event(self, event_type: EventType) -> None:
        """
        Unsubscribes from a specific event type if currently subscribed.

        Args:
            event_type (EventType): The event type to unsubscribe from.
        """
        event = self._subscriptions.get(event_type)
        if event and event[2] == 1 and self._running: # Subscribed and running
            event[1](self._symbol)
            event[2] = 0  # Mark as unsubscribed
        else:
            print(f"Not subscribed to {event_type}")

    def subscribe_all(self) -> None:
        """Subscribes to all available events."""
        for event_type in self._subscriptions:
            self._subscribe_event(event_type)

    def unsubscribe_all(self) -> None:
        """Unsubscribes from all active events."""
        for event_type in self._subscriptions:
            self._unsubscribe_event(event_type)

    def start(self) -> None:
        """Starts the WebSocket client for streaming data."""
        if not self._running:
            self._running = True
            self._wss_client.run()
    
    async def close(self) -> None:
        """Closes the WebSocket connection."""
        if self._running:
            await self._wss_client.close()
            self._running = False

    def stop(self) -> None:
        """Stops the WebSocket connection."""
        if self._running:
            self._wss_client.stop()
            self._running = False

    async def stop_ws(self) -> None:
        """Signals WebSocket connection should close by adding a closing message to the stop_stream_queue."""
        if self._running:
            await self._wss_client.stop_ws()
            self._running = False

    # Convenience methods for subscribing to specific events
    def subscribe_bars(self) -> None: 
        """Subscribes to the 'bars' event."""
        self._subscribe_event(EventType.BARS)

    def subscribe_daily_bars(self) -> None: 
        """Subscribes to the 'daily bars' event."""
        self._subscribe_event(EventType.DAILY_BARS)

    # Convenience methods for unsubscribing from specific events
    def unsubscribe_bars(self) -> None: 
        """Unsubscribes from the 'bars' event."""
        self._unsubscribe_event(EventType.BARS)

    def unsubscribe_daily_bars(self) -> None: 
        """Unsubscribes from the 'daily bars' event."""
        self._unsubscribe_event(EventType.DAILY_BARS)