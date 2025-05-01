from enum import Enum

class EventType(Enum):
    """
    Enum representing various types of market events that can be subscribed to.

    Attributes:
        BARS (str): Represents aggregated trade data over a fixed time interval.
        DAILY_BARS (str): Represents daily bar data, summarizing the trading day.
    """
    BARS = "bars"
    DAILY_BARS = "daily_bars"