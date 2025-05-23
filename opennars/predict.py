import socket
from threading import Thread, Lock
import plotly.graph_objects as go
from src.data_fetchers.historical_data_fetcher import HistoricalDataFetcher
from config.config import Config
from alpaca.data.timeframe import TimeFrame

import datetime

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
predict_address = ("localhost", 12345)
nars_address = ("localhost", 54321)
nars_predicted = 0
augment = 0

nars_lock = Lock()
datapoints = []


def percent_correct(true, observed):
    if true == 0:
        return 1.0 if observed == 0 else 0.0
    error = abs(observed - true) / abs(true)
    return max(0.0, 1 - error)


def send_status(trade_count, volume, expected, message=None):

    if message is None:

        # if nars is low go up
        # elif nars is high go down
        # else nars is within 5 points then good

        buffer = 1
        with nars_lock:
            cur_predicted = nars_predicted

        f = None
        if expected > cur_predicted + buffer:

            msg_1 = "<{up} --> [on]>. %1;0.9%"

            max_distance = 10
            d = abs(expected - cur_predicted)
            if max_distance <= 0:
                # degenerate case: if no span, treat identical as 1, else 0
                return 1.0 if d == 0 else 0.0

            f = str(max(0.0, min(1, 1 - d / max_distance)))

            f = str(percent_correct(cur_predicted, expected))

            msg_2 = "<{SELF} --> [good]>. %" + f + ";0.9%"

            sock.sendto((msg_1 + "|" + msg_2).encode(), nars_address)

        elif expected < cur_predicted - buffer:
            msg_1 = "<{down} --> [on]>. %1;0.9%"

            max_distance = 10
            d = abs(expected - cur_predicted)
            if max_distance <= 0:
                # degenerate case: if no span, treat identical as 1, else 0
                return 1.0 if d == 0 else 0.0
            # 1 - (d / D), clamped to [0,1]
            f = str(max(0.0, min(1, 1 - d / max_distance)))

            f = str(percent_correct(cur_predicted, expected))

            msg_2 = "<{SELF} --> [good]>. %" + f + ";0.9%"

            sock.sendto((msg_1 + "|" + msg_2).encode(), nars_address)

        else:
            msg_1 = None
            msg_2 = None
            msg = "<{SELF} --> [good]>. %1;0.9%"
            sock.sendto(msg.encode(), nars_address)


def process_data():

    start = datetime.datetime.strptime("2020-01-01", "%Y-%m-%d")
    end = datetime.datetime.strptime("2025-01-01", "%Y-%m-%d")

    timeframe_map = {
        "minute": TimeFrame.Minute,
        "hour": TimeFrame.Hour,
        "day": TimeFrame.Day,
    }

    timeframe = timeframe_map["day"]
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
    global augment
    with nars_lock:
        nars_predicted = close[0]

    trade_count = [p.trade_count for p in data[symbol]]
    volume = [p.volume for p in data[symbol]]

    nars_predicted_array = []

    for i in range(1):
        nars_predicted_array = []
        for i, c in enumerate(close):
            # nars predict

            augment = 100

            send_status(trade_count[i], volume[i], expected=c)
            nars_predicted_array.append(nars_predicted)

    fig = go.Figure()

    x = list(range(len(close)))
    fig.add_trace(go.Scatter(x=x, y=close, mode="lines+markers", name="Trade Close"))
    fig.add_trace(
        go.Scatter(
            x=x, y=nars_predicted_array, mode="lines+markers", name="Nars Prediction"
        )
    )

    fig.update_layout(
        title="Trade Close and Nars Prediction Over Time",
        xaxis_title=f"Index({timeframe}'s)",
        yaxis=dict(title="Trade Close / Nars Prediction"),
        legend=dict(x=0.01, y=0.99),
    )

    fig.show()


def receive_commands():
    global nars_predicted
    global augment
    sock.bind(predict_address)

    while True:
        data, _ = sock.recvfrom(1024)
        command = data.decode()
        print(f"command received: {command}")

        with nars_lock:
            if command == "^up":
                nars_predicted = nars_predicted + augment

            elif command == "^down":
                nars_predicted = nars_predicted - augment

            elif command == "^hold":
                pass


if __name__ == "__main__":
    t = Thread(target=receive_commands)
    t.daemon = True
    t.start()

    process_data()
