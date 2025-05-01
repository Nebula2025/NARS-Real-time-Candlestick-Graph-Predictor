from os import wait
import random
import socket
import sys
from threading import Thread, Lock
import math

"""
The socket is used to establish communication between NARS and the game, and as expected, NARS will also use the exact 
same method to print content to the UI.
"""
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
game_address = ("localhost", 12345)
control_address = ("localhost", 54321)
nars_predicted = 0


nars_lock = Lock()
datapoints = []


def percent_correct(true, observed):
    if true == 0:
        return 1.0 if observed == 0 else 0.0
    error = abs(observed - true) / abs(true)
    return max(0.0, 1 - error)


def send_status(trade_count, volume, expected, message=None):
    """
    In this game, information is sent to NARS every frame, describing: 1) the position of the ball relative to the
    paddle, and 2) whether the current situation is satisfactory.

    Each message is just a string.
    Messages are separated by "|".
    """

    if message is None:

        # if nars is low go up
        # elif nars is high go down
        # else nars is within 5 points then good

        """
        percent error, flipped to report how close nars was to prediction as f value
        f = str(1 - (nars_predicted - expected) / expected)"""

        buffer = 1

        # nars_predicted = expected
        with nars_lock:
            cur_predicted = nars_predicted

        print("CURRENT SEND:", cur_predicted, "CLOSE:", expected)

        f = None
        if expected > cur_predicted + buffer:
            # sock.sendto(msg.encode(), control_address)
            # str(1 - (paddle_pos[0] - ball_pos[0]) / (screen_width - paddle_width))

            msg_1 = "<{up} --> [on]>. %1;0.9%"

            max_distance = 10
            d = abs(expected - cur_predicted)
            if max_distance <= 0:
                # degenerate case: if no span, treat identical as 1, else 0
                return 1.0 if d == 0 else 0.0
            # 1 - (d / D), clamped to [0,1]
            f = str(max(0.0, min(1, 1 - d / max_distance)))

            f = str(percent_correct(cur_predicted, expected))

            msg_2 = "<{SELF} --> [good]>. %" + f + ";0.9%"

            sock.sendto((msg_1 + "|" + msg_2).encode(), control_address)
        elif expected < cur_predicted - buffer:
            # sock.sendto(msg.encode(), control_address)
            """
            + str(
                1
                - (ball_pos[0] - (paddle_pos[0] + paddle_width))
                / (screen_width - paddle_width)
            """
            msg_1 = "<{down} --> [on]>. %1;0.9%"

            """
            x = 1 - (cur_predicted - expected) / expected
            x = (x + 1) / 2.0
            f = str(min(max(x, 0.0), 1.0))
            """

            max_distance = 10
            d = abs(expected - cur_predicted)
            if max_distance <= 0:
                # degenerate case: if no span, treat identical as 1, else 0
                return 1.0 if d == 0 else 0.0
            # 1 - (d / D), clamped to [0,1]
            f = str(max(0.0, min(1, 1 - d / max_distance)))

            f = str(percent_correct(cur_predicted, expected))

            msg_2 = "<{SELF} --> [good]>. %" + f + ";0.9%"
            sock.sendto((msg_1 + "|" + msg_2).encode(), control_address)

        else:
            msg_1 = None
            msg_2 = None
            msg = "<{SELF} --> [good]>. %1;0.9%"
            sock.sendto(msg.encode(), control_address)

        # print("F:", f, msg_1, msg_2)


from src.data_fetchers.historical_data_fetcher import HistoricalDataFetcher
from config.config import Config
from alpaca.data.timeframe import TimeFrame

import datetime

# def __init__(self, api_key: str, secret_key: str, symbol: str) -> None:


def process_data():

    start = datetime.datetime.strptime("2021-01-01", "%Y-%m-%d")
    end = datetime.datetime.strptime("2021-01-30", "%Y-%m-%d")

    timeframe_map = {
        "minute": TimeFrame.Minute,
        "hour": TimeFrame.Hour,
        "day": TimeFrame.Day,
    }

    timeframe = timeframe_map["minute"]
    symbol = "SPY"

    fetcher = HistoricalDataFetcher(
        api_key=Config.ALPACA_API_KEY,
        secret_key=Config.ALPACA_SECRET_KEY,
        symbol=symbol,
    )
    data = fetcher.retrieve_historical_bar_data(
        timeframe=timeframe, start=start, end=end
    )

    close = [p.close for p in data[symbol]]

    global nars_predicted
    with nars_lock:
        nars_predicted = close[0]

    trade_count = [p.trade_count for p in data[symbol]]
    volume = [p.volume for p in data[symbol]]

    while True:
        for i, c in enumerate(close):
            # nars predict
            send_status(trade_count[i], volume[i], expected=c)


def receive_commands():
    global nars_predicted
    sock.bind(game_address)

    while True:
        data, _ = sock.recvfrom(1024)
        command = data.decode()
        print(f"command received: {command}")

        with nars_lock:
            if command == "^up":
                nars_predicted = nars_predicted + 1
            elif command == "^down":
                nars_predicted = nars_predicted - 1
            elif command == "^hold":
                pass

            cur = nars_lock
        # print("CURRENT:", cur)


if __name__ == "__main__":
    t = Thread(target=receive_commands)
    t.daemon = True
    t.start()

    process_data()
