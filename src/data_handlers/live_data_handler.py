import datetime


class LiveDataHandler:
    """Handles incoming streaming data asynchronously."""
    def __init__(self, symbol: str):
        self.symbol = symbol

    async def handle_data(self, data, event_type, called):
        """Processes incoming data asynchronously."""
        # print(f"Time Difference (now - called): {datetime.datetime.now(datetime.timezone.utc) - called}")
        # print(f"{event_type}: Time Difference (now - gotten): {datetime.datetime.now(datetime.timezone.utc) - data.timestamp}")
        print(f"[{event_type}] {self.symbol}: {data}")

    def create_handler(self, event_type):
        """Returns an async function bound with symbol and event type."""
        async def handler(data):
            called = datetime.datetime.now(datetime.timezone.utc)
            await self.handle_data(data, event_type, called)
        return handler